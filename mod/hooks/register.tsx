import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, RenderElement, Timer } from 'claude-code'

import type { MascotaAjustes, MascotaAnimo, MascotaEstado, MascotaTamano } from '../types'
import { esFalloReal, esRechazo } from './deteccion'
import { ESPECIAL } from './animaciones'
import { celdas, dibujoSvg, elegirTam, especialEnBanda, especialQueCabe, fotograma, fotogramaEn, medidas, planPanel, TEXTO_COLUMNAS, TEXTO_FILAS } from './dibujo'
import type { Tam } from './sprites'
import { CARAS, COLORES, DURACION, ESTADOS, NOMBRE, SIESTA, cortar, detalleDe, estadoDeHerramienta, frase } from './estados'

type $ = EngineInterface

const LATIDO = 250
const LILA = '#b79ae0'
// Una conversación da señales de vida cada 10 s; sin señal en 35 s se da por cerrada.
const PRESENCIA = 10000
const SIN_SENAL = 35000
// Un turno que dura más de esto cuenta como «un encargo largo»: baile, aviso de Windows.
const LARGO = 120000
const AVISO_DESDE = 30000
const ENTRE_AVISOS = 60000

const INICIAL: MascotaAnimo = { estado: 'hula', desde: 0, hasta: 0, detalle: '' }
const AJUSTES: MascotaAjustes = { tamano: 'normal', sonido: true, avisos: true, modo: 'banda', escritorio: true }
const PANEL = 'emi'

const animo = atom({ plugin: 'mascota', key: 'animo' } as const, INICIAL)
const tic = atom({ plugin: 'mascota', key: 'tic' } as const, 0)
const ajustes = atom({ plugin: 'mascota', key: 'ajustes' } as const, AJUSTES)
const otras = atom({ plugin: 'mascota', key: 'otras' } as const, 0)
const panel = atom({ plugin: 'mascota', key: 'panel' } as const, false)

// Lo que vive aquí se reinicia en cada recarga; lo que se dibuja está en $.state.
let trabajando = false
let inicioTurno = 0
let herramientas = 0
let actual: MascotaEstado = 'hula'
let desdeActual = 0
// El programa de escritorio (escritorio\emi_escritorio.pyw) vive en el proyecto; si no existe en esta ruta, el mod sigue sin él.
let rutaEscritorio = ''
let enDemo = false
let ultimoAviso = 0
let carpeta = ''
let idSesion = ''
let esWindows = false
let latido: Timer | undefined
let demo: Timer | undefined
let vueltas = 0
// Herramientas que el permiso denegó (por id de llamada) y si el turno se interrumpió: ni una cosa ni la otra es un fallo.
const denegados = new Set<string>()
let abortado = false
// Lo último que midió el motor al dibujar la banda: sirve para estimar el hueco de un panel antes de abrirlo.
let vista = { columnas: 0, filas: 0, isFullscreen: null as boolean | null }

async function fijar($: $, estado: MascotaEstado, detalle = '', desdeDemo = false) {
  if (enDemo && !desdeDemo) {
    return
  }
  const ahora = Date.now()
  const dura = DURACION[estado]
  actual = estado
  desdeActual = ahora
  await update($, animo, () => ({ estado, desde: ahora, hasta: dura ? ahora + dura : 0, detalle })).catch(() => undefined)
  await ajustarRapido($)
  // El programa de escritorio lee el estado del archivo de la sesión: se publica en cada cambio.
  await publicar($)
}

// Un estado con animación propia (pensando: 5 fps) pide más tics que el latido de 250 ms, pero solo mientras dura ese estado:
// el resto del tiempo no corre nada extra (se ve en la banda y en el panel, en terminal y escritorio).
let rapido: Timer | undefined
let rapidoDe = ''
async function ajustarRapido($: $) {
  const e = ESPECIAL[actual]
  // A 4 fps o menos basta el latido de 250 ms: no hace falta un reloj extra.
  if (!e || e.fps <= 4) {
    rapido?.cancel()
    rapido = undefined
    rapidoDe = ''
    return
  }
  if (rapido && rapidoDe === actual) {
    return
  }
  rapido?.cancel()
  rapidoDe = actual
  // Dos tics por fotograma (mínimo 50 ms): el fotograma sale del reloj, el tic solo fija cuánto tarda en verse el cambio.
  rapido = $.clock.every(Math.max(50, Math.round(500 / e.fps)), () => {
    void update($, tic, n => n + 1).catch(() => undefined)
  })
}

// ---------- Avisos fuera de la pantalla (Windows) ----------

function guionAviso(tipo: 'listo' | 'necesita', sonido: boolean, aviso: boolean) {
  const partes: string[] = []
  if (sonido) {
    partes.push(
      tipo === 'listo'
        ? '[console]::Beep(784,110);[console]::Beep(988,110);[console]::Beep(1175,220)'
        : '[console]::Beep(988,140);Start-Sleep -Milliseconds 60;[console]::Beep(988,140)',
    )
  }
  if (aviso) {
    const texto = tipo === 'listo' ? 'Claude ha terminado' : 'Claude te necesita'
    partes.push(
      "Add-Type -AssemblyName System.Windows.Forms;Add-Type -AssemblyName System.Drawing;" +
        "$n=New-Object System.Windows.Forms.NotifyIcon;$n.Icon=[System.Drawing.SystemIcons]::Information;" +
        `$n.BalloonTipTitle='${NOMBRE}';$n.BalloonTipText='${texto}';$n.Visible=$true;$n.ShowBalloonTip(6000);` +
        'Start-Sleep -Seconds 7;$n.Dispose()',
    )
  }
  return partes.join(';')
}

// `globo`: si además del sonido va el aviso de Windows (el sonido suena siempre que está activado; el globo, solo en encargos largos).
async function avisar($: $, tipo: 'listo' | 'necesita', globo = true) {
  const a = await read($, ajustes)
  if (!esWindows || (!a.sonido && !(a.avisos && globo))) {
    return
  }
  const guion = guionAviso(tipo, a.sonido, a.avisos && globo)
  void $.process
    .run(['powershell', '-NoProfile', '-NonInteractive', '-Command', guion], { timeoutMs: 20000 })
    .catch(() => undefined)
}

// ---------- Otras conversaciones ----------

async function publicar($: $, cerrada = false) {
  if (!carpeta || !idSesion) {
    return
  }
  const datos = { id: idSesion, trabajando, vivo: Date.now(), cerrada, estado: actual, desde: desdeActual }
  await $.fs.write(`${carpeta}/sesiones/${idSesion}.json`, JSON.stringify(datos)).catch(() => undefined)
}

// Abre Emi en el escritorio (Windows): un programa aparte que se cierra solo cuando ya no queda ninguna conversación. Una sola instancia:
// si ya hay una, la nueva se va sola. El archivo escritorio.txt es el interruptor que lee el programa («off» lo cierra).
async function lanzarEscritorio($: $) {
  if (!esWindows || !carpeta || !rutaEscritorio) {
    return
  }
  const a = await read($, ajustes)
  await $.fs.write(`${carpeta}/escritorio.txt`, a.escritorio ? 'on' : 'off').catch(() => undefined)
  if (!a.escritorio) {
    return
  }
  const guion = `$p='${rutaEscritorio}';if(Test-Path $p){Start-Process pythonw -ArgumentList ('"'+$p+'"') -WindowStyle Hidden}`
  void $.process.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', guion], { timeoutMs: 20000 }).catch(() => undefined)
}

async function contarOtras($: $) {
  if (!carpeta) {
    return
  }
  const entradas = await $.fs.list(`${carpeta}/sesiones`).catch(() => [])
  const ahora = Date.now()
  let n = 0
  for (const entrada of entradas) {
    if (entrada.kind !== 'file' || !entrada.name.endsWith('.json') || entrada.name === `${idSesion}.json`) {
      continue
    }
    const texto = await $.fs.read(`${carpeta}/sesiones/${entrada.name}`).catch(() => '')
    try {
      const r = JSON.parse(typeof texto === 'string' ? texto : '') as { trabajando?: boolean; vivo?: number; cerrada?: boolean }
      if (r.trabajando && !r.cerrada && typeof r.vivo === 'number' && ahora - r.vivo < SIN_SENAL) {
        n += 1
      }
    } catch {
      // Un archivo a medio escribir: se lee en la siguiente pasada.
    }
  }
  await update($, otras, () => n).catch(() => undefined)
}

// ---------- El latido: fotogramas, estados que pasan y siesta ----------

async function latir($: $) {
  const ahora = Date.now()
  await update($, tic, n => n + 1).catch(() => undefined)
  vueltas += 1
  if (!enDemo) {
    const a = await read($, animo)
    if (a.hasta > 0 && ahora >= a.hasta) {
      await fijar($, a.estado === 'falla' && trabajando ? 'pensando' : 'hula')
    } else if (a.estado === 'hula' && !trabajando && a.desde > 0 && ahora - a.desde > SIESTA) {
      await fijar($, 'duerme')
    }
  }
  if (vueltas % (PRESENCIA / LATIDO) === 0) {
    await publicar($)
  }
  if (vueltas % 20 === 0) {
    await contarOtras($)
  }
}

function probar($: $) {
  demo?.cancel()
  enDemo = true
  let i = 0
  void fijar($, ESTADOS[0] ?? 'hula', 'demostración', true)
  demo = $.clock.every(3000, () => {
    i += 1
    const siguiente = ESTADOS[i]
    if (!siguiente) {
      demo?.cancel()
      demo = undefined
      enDemo = false
      void fijar($, 'hula')
      return
    }
    void fijar($, siguiente, 'demostración', true)
  })
}

// ---------- El panel acoplado ----------

// El mayor tamaño que pide cada ajuste; el real depende del espacio que dé el motor.
const topeDe = (t: MascotaTamano): Tam => (t === 'grande' ? 'XL' : t === 'mini' ? 'S' : 'L')

async function guardarAjustes($: $, cambio: Partial<MascotaAjustes>) {
  const nuevo = await update($, ajustes, x => ({ ...x, ...cambio }))
  await $.store.set('ajustes', nuevo).catch(() => undefined)
}

// Abre el panel y dice por qué no se pudo ('' si quedó colocado). Si no se coloca, no se deja a medias: se cierra y Emi sigue en la banda.
async function abrirPanel($: $): Promise<string> {
  const a = await read($, ajustes)
  const filasEst = Math.max(10, (vista.filas || 41) - 2)
  const columnasEst = Math.max(40, Math.floor((vista.columnas || 156) * 0.45))
  const plan = planPanel(filasEst, columnasEst, topeDe(a.tamano))
  const m = plan ? medidas(plan.tam) : null
  // Con tamaño normal o grande, si el terminal da sitio, el panel se abre lo bastante ancho y alto para la animación de 60x60 de «pensando».
  const esp = Object.values(ESPECIAL).map(e => medidas(e.tam)).reduce((x, y) => ({ ancho: Math.max(x.ancho, y.ancho), filas: Math.max(x.filas, y.filas) }), { ancho: 0, filas: 0 })
  const cabeEsp = (a.tamano === 'normal' || a.tamano === 'grande') && columnasEst >= esp.ancho + 2 && filasEst >= esp.filas + TEXTO_FILAS
  const columns = Math.max(m ? m.ancho + (plan?.texto === 'lado' ? TEXTO_COLUMNAS : 0) + 2 : 40, cabeEsp ? esp.ancho + 2 : 0)
  const rows = Math.max(m ? m.filas + 4 : 10, cabeEsp ? esp.filas + TEXTO_FILAS : 0)
  const r = await $.ui.open({ id: PANEL, title: NOMBRE, columns, rows }).catch((error: unknown) => ({ isPlaced: false as const, reason: String(error) }))
  if (!r.isPlaced) {
    await $.ui.close({ id: PANEL }).catch(() => undefined)
    await update($, panel, () => false).catch(() => undefined)
    return r.reason
  }
  await update($, panel, () => true).catch(() => undefined)
  await ajustarRapido($)
  return ''
}

async function aBanda($: $) {
  await guardarAjustes($, { modo: 'banda' })
  await update($, panel, () => false).catch(() => undefined)
  await $.ui.close({ id: PANEL }).catch(() => undefined)
  await ajustarRapido($)
}

// ---------- Cómo se ve ----------

function tieneContenido(arbol: unknown): arbol is RenderElement {
  if (!arbol || typeof arbol !== 'object') {
    return false
  }
  const hijos = (arbol as { children?: unknown }).children
  return (arbol as { type?: unknown }).type === 'Text' || (Array.isArray(hijos) && hijos.length > 0)
}

function textoEstado(a: MascotaAnimo, ahora: number, puntos: number) {
  const base = frase(a.estado, a.desde, ahora)
  return a.estado === 'pensando' || a.estado === 'responde' ? base.replace('…', '.'.repeat(1 + (puntos % 3))) : base
}

const TAMANOS: readonly MascotaTamano[] = ['grande', 'normal', 'mini', 'compacta', 'oculta']

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const hecho = await next(e)
    const casa = (await $.env.get('HOME').catch(() => undefined)) ?? (await $.env.get('USERPROFILE').catch(() => undefined))
    carpeta = casa ? `${casa}/.claude/mascota` : ''
    rutaEscritorio = casa ? `${casa}/Proyectos/mods-claude/emilia-mascota/escritorio/emi_escritorio.pyw` : ''
    idSesion = await $.session.id().catch(() => '')
    esWindows = (await $.env.get('OS').catch(() => undefined)) === 'Windows_NT'

    const guardado = (await $.store.get('ajustes').catch(() => undefined)) as Partial<MascotaAjustes> | undefined
    if (guardado && typeof guardado === 'object') {
      await update($, ajustes, a => ({
        tamano: TAMANOS.includes(guardado.tamano as MascotaTamano) ? (guardado.tamano as MascotaTamano) : a.tamano,
        sonido: typeof guardado.sonido === 'boolean' ? guardado.sonido : a.sonido,
        avisos: typeof guardado.avisos === 'boolean' ? guardado.avisos : a.avisos,
        modo: guardado.modo === 'panel' || guardado.modo === 'banda' ? guardado.modo : a.modo,
        escritorio: typeof guardado.escritorio === 'boolean' ? guardado.escritorio : a.escritorio,
      }))
    }

    await $.command.register({
      name: 'emi',
      description: 'Emi, la mascota: /emi grande | normal | mini | compacta | oculta | panel | banda | sonido | silencio | avisos | sin-avisos | escritorio | sin-escritorio | probar',
      argumentHint: '[grande | normal | mini | compacta | oculta | panel | banda | sonido | silencio | avisos | sin-avisos | escritorio | sin-escritorio | probar]',
      immediate: true,
    })

    // Una conversación que se reanuda o un mod que se recarga a mitad de turno no ven empezar nada: Emi arranca de guardia.
    if ((await read($, animo)).desde === 0) {
      await fijar($, 'nueva')
    }
    latido?.cancel()
    latido = $.clock.every(LATIDO, () => {
      void latir($)
    })
    await publicar($)
    await lanzarEscritorio($)
    await contarOtras($)
    // Una recarga cierra el panel sin avisar: se parte de «sin panel» y, si ese es el modo guardado, se reabre.
    await update($, panel, () => false).catch(() => undefined)
    if ((await read($, ajustes)).modo === 'panel') {
      const motivo = await abrirPanel($)
      if (motivo) {
        $.ui.toast(`Emi: el panel necesita más sitio (${motivo}). Sigue en la banda; /emi panel lo prueba de nuevo.`, { timeoutMs: 8000 })
      }
    }
    return hecho
  })

  on('session.end', async ($, e, next) => {
    await publicar($, true)
    if (e.reason === 'clear') {
      trabajando = false
      await fijar($, 'nueva')
    }
    return next(e)
  })

  on('turn.start', async ($, e, next) => {
    trabajando = true
    abortado = false
    inicioTurno = Date.now()
    herramientas = 0
    await fijar($, 'pensando')
    await publicar($)
    return next(e)
  })

  // Lo que llega del modelo: pensamiento o texto. Solo se mira: nada de esto cambia la respuesta.
  on('turn.step', async function* ($, e, next) {
    if (e.agentId !== undefined) {
      return yield* next(e)
    }
    const flujo = next(e)
    let paso = await flujo.next()
    while (!paso.done) {
      const trozo = paso.value
      if (trozo.kind === 'text' && actual !== 'responde' && actual !== 'necesita') {
        actual = 'responde'
        void fijar($, 'responde')
      } else if (trozo.kind === 'thinking' && actual !== 'pensando' && actual !== 'necesita') {
        actual = 'pensando'
        void fijar($, 'pensando')
      }
      yield trozo
      paso = await flujo.next()
    }
    return paso.value
  })

  on('tool.call', async ($, e, next) => {
    if (e.agentId === undefined) {
      herramientas += 1
      await fijar($, estadoDeHerramienta(e.tool), detalleDe(e.tool, e as unknown as Record<string, unknown>))
    }
    const r = await next(e)
    const denegado = e.tool_use_id !== undefined && denegados.delete(e.tool_use_id)
    // El motor deja el texto que lee el modelo en `text`; si falta (la respuesta de otro hook), se mira `result` cuando es texto.
    const resultado = { isError: r.isError, deny: r.deny, text: r.text ?? (typeof r.result === 'string' ? r.result : undefined) }
    const contexto = { denegadoPorCheck: denegado, turnoAbortado: abortado }
    if (e.agentId === undefined) {
      if (esFalloReal(resultado, contexto)) {
        await fijar($, 'falla', e.tool)
      } else if (esRechazo(resultado, contexto)) {
        // Un permiso rechazado, una herramienta denegada o una interrupción no son un fallo: Claude sigue pensando.
        await fijar($, 'pensando')
      }
    }
    return r
  }).catch(($, e, next) => next(e))

  // Las denegaciones del permiso se anotan aquí para no confundirlas luego con un fallo de la herramienta.
  on('tool.check', async ($, e, next) => {
    const r = await next(e)
    if (r.decision === 'deny' && e.tool_use_id !== undefined && e.agentId === undefined) {
      if (denegados.size > 200) {
        denegados.clear()
      }
      denegados.add(e.tool_use_id)
    }
    return r
  }).catch(($, e, next) => next(e))

  // Claude Code avisa de que necesita permiso o una respuesta tuya (no de que lleva rato esperando).
  on('classic.Notification', async ($, e, next) => {
    if (!/idle/i.test(e.notification_type)) {
      await fijar($, 'necesita', cortar(e.message ?? '', 60))
      const ahora = Date.now()
      if (ahora - ultimoAviso > ENTRE_AVISOS) {
        ultimoAviso = ahora
        void avisar($, 'necesita')
      }
    }
    return next(e)
  }).catch(($, e, next) => next(e))

  on('turn.complete', async ($, e, next) => {
    if (e.agentId === undefined) {
      trabajando = false
      abortado = e.reason === 'aborted'
      const duro = Date.now() - inicioTurno
      if (e.reason === 'answer') {
        const largo = duro >= LARGO || herramientas >= 25
        await fijar($, largo ? 'baile' : 'terminado', `${Math.max(1, Math.round(duro / 1000))} s · ${herramientas} herramientas`)
        // Cada vez que Claude termina suena el pitido de «listo»; el globo de Windows solo si el encargo fue largo.
        const globo = duro >= AVISO_DESDE
        if (globo) {
          ultimoAviso = Date.now()
        }
        void avisar($, 'listo', globo)
      } else if (e.reason === 'aborted') {
        await fijar($, 'hula')
      } else {
        await fijar($, 'para', e.reason === 'refusal' ? 'Claude se ha negado' : 'error de la API')
      }
      await publicar($)
    }
    return next(e)
  })

  on('command.run', { command: 'emi' }, async ($, e) => {
    const orden = e.args.trim().toLowerCase()
    const a = await read($, ajustes)
    const guardar = (cambio: Partial<MascotaAjustes>) => guardarAjustes($, cambio)
    if ((TAMANOS as readonly string[]).includes(orden)) {
      await guardar({ tamano: orden as MascotaTamano })
      return { text: orden === 'oculta' ? `${NOMBRE} se esconde. /emi normal la trae de vuelta.` : `${NOMBRE} en tamaño «${orden}».` }
    }
    if (orden === 'sonido' || orden === 'silencio') {
      await guardar({ sonido: orden === 'sonido' })
      return { text: orden === 'sonido' ? 'Sonido al terminar y al necesitarte: activado.' : 'Sin sonido.' }
    }
    if (orden === 'avisos' || orden === 'sin-avisos') {
      await guardar({ avisos: orden === 'avisos' })
      return { text: orden === 'avisos' ? 'Aviso de Windows cuando termina un encargo largo o te necesita: activado.' : 'Sin avisos de Windows.' }
    }
    if (orden === 'escritorio' || orden === 'sin-escritorio') {
      await guardar({ escritorio: orden === 'escritorio' })
      await lanzarEscritorio($)
      return {
        text:
          orden === 'escritorio'
            ? 'Emi también flota sobre el escritorio, aunque minimices Claude, mientras haya una conversación abierta. Arrástrala para moverla; clic derecho para el tamaño o para cerrarla.'
            : 'Emi ya no flota sobre el escritorio.',
      }
    }
    if (orden === 'panel') {
      const motivo = await abrirPanel($)
      if (motivo) {
        return { text: `No pude abrir el panel acoplado: ${motivo}\nEmi sigue en la banda.` }
      }
      await guardar({ modo: 'panel' })
      return { text: 'Emi está en el panel acoplado, con el mayor tamaño que cabe. /emi banda la devuelve a la banda. Se queda así en las próximas sesiones.' }
    }
    if (orden === 'banda') {
      await aBanda($)
      return { text: 'Emi vuelve a la banda sobre el cuadro de texto.' }
    }
    if (orden === 'probar') {
      probar($)
      return { text: 'Te enseño los 12 estados de Emi, tres segundos cada uno.' }
    }
    return {
      text:
        `${NOMBRE} · tamaño ${a.tamano} · ${a.modo === 'panel' ? 'panel acoplado' : 'banda'} · sonido ${a.sonido ? 'sí' : 'no'} · avisos ${a.avisos ? 'sí' : 'no'} · escritorio ${a.escritorio ? 'sí' : 'no'}${esWindows ? '' : ' (sonido y avisos solo en Windows)'}\n` +
        'Uso: /emi grande | normal | mini | compacta | oculta · /emi panel | banda · /emi sonido | silencio · /emi avisos | sin-avisos · /emi escritorio | sin-escritorio · /emi probar',
    }
  })

  // ---------- El panel acoplado: si lo cierra la persona, Emi vuelve a la banda y se queda ahí ----------

  on('ui.close', async ($, e, next) => {
    if (e.id === PANEL) {
      await update($, panel, () => false).catch(() => undefined)
      await ajustarRapido($)
      if (e.origin.kind === 'person') {
        await guardarAjustes($, { modo: 'banda' }).catch(() => undefined)
      }
    }
    return next(e)
  }).catch(($, e, next) => next(e))

  // ---------- La barra de Emi, encima del cuadro de texto ----------

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    vista = { columnas: e.viewport?.columns ?? 0, filas: e.viewport?.rows ?? 0, isFullscreen: e.viewport?.isFullscreen ?? null }
    const aj = await read($, ajustes)
    // Con el panel abierto Emi vive allí: la banda no la repite.
    if (e.props.hasSurvey || aj.tamano === 'oculta' || (await read($, panel))) {
      return next(e)
    }
    const a = await read($, animo)
    const n = await read($, tic)
    const mas = await read($, otras)
    const ahora = Date.now()
    const color = COLORES[a.estado]
    const dicho = textoEstado(a, ahora, n)
    const extra = [a.detalle, mas > 0 ? `+${mas} ${mas === 1 ? 'conversación' : 'conversaciones'} en marcha` : ''].filter(Boolean)

    const resto = await next(e).catch(() => undefined)
    const ajeno = tieneContenido(resto) ? resto : null

    // En el terminal, el mayor sprite que cabe en las filas que concede el motor; si no cabe ninguno, la línea compacta.
    const tope = topeDe(aj.tamano)
    const tam = e.surface === 'terminal' ? elegirTam(e.props.maxRows - 1, e.props.bodyColumns - TEXTO_COLUMNAS, tope) : null
    // «pensando» tiene su animación también en la banda del terminal, a 60x60 si la banda es alta y si no en una versión de 28x28 (cabe en las 14 filas).
    const chico = e.surface === 'terminal' && (aj.tamano === 'normal' || aj.tamano === 'grande') ? especialEnBanda(a.estado, e.props.maxRows - 1, e.props.bodyColumns) : null

    if (aj.tamano === 'compacta' || (e.surface === 'terminal' && !tam && !chico)) {
      const { Box, Button, Text } = $.ui.resolve(e)
      const puntos = a.estado === 'pensando' || a.estado === 'responde' ? '.'.repeat(1 + (n % 3)) : ''
      const linea = (
        <Box flexDirection="row" gap={1}>
          <Text color={color} bold wrap="truncate-end">
            {CARAS[a.estado]} {NOMBRE}
          </Text>
          <Text color={color} wrap="truncate-end">
            · {dicho.replace('…', puntos)}
          </Text>
          <Text dimColor wrap="truncate-end">
            {extra.length ? `· ${extra.join(' · ')}` : ''}
          </Text>
          <Button key="emi-grande" label="agrandar" onPress={() => update($, ajustes, x => ({ ...x, tamano: 'normal' as const }))} />
        </Box>
      )
      return ajeno ? (
        <Box flexDirection="column">
          {linea}
          {ajeno}
        </Box>
      ) : (
        linea
      )
    }

    if (e.surface === 'terminal' && (tam || chico)) {
      const { Box, Button, Raster, Text } = $.ui.resolve(e)
      const c = chico ? celdas(chico, fotogramaEn(a.estado, chico, ahora - a.desde)) : celdas(tam!, fotograma(a.estado, tam!, n))
      const reducido = (chico ? chico !== ESPECIAL[a.estado]?.tam : tam !== tope) && aj.tamano !== 'mini'
      const lineas = reducido ? [...extra, 'más grande: /emi panel'] : extra
      const banda = (
        <Box flexDirection="row" gap={1}>
          <Raster key="emi" columns={c.columnas} rows={c.filas} cells={c.cells} />
          <Box flexDirection="column">
            <Text color={LILA} bold wrap="truncate-end">
              {NOMBRE}
            </Text>
            <Text color={color} bold wrap="truncate-end">
              {dicho}
            </Text>
            {lineas.map(linea => (
              <Text key={linea} dimColor wrap="truncate-end">
                {linea}
              </Text>
            ))}
            <Button key="emi-compacta" label="compacta" onPress={() => update($, ajustes, x => ({ ...x, tamano: 'compacta' as const }))} />
          </Box>
        </Box>
      )
      return ajeno ? (
        <Box flexDirection="column">
          {banda}
          {ajeno}
        </Box>
      ) : (
        banda
      )
    }

    // El terminal ya está atendido arriba (con sprite o en línea compacta); esto solo deja a TypeScript saber que lo que sigue no es terminal.
    if (e.surface === 'terminal') {
      return next(e)
    }

    // La app de escritorio, el editor y el móvil dibujan un SVG (sin Raster): escala entera, sin límite de filas de terminal.
    const { Box, Button, Svg, Text } = $.ui.resolve(e)
    const tamSvg: Tam = aj.tamano === 'grande' ? 'XL' : aj.tamano === 'mini' ? 'N' : 'L'
    // «pensando»: su animación de 5 fotogramas a 5 fps (60x60), también en la banda: un SVG se escala y no tiene el límite de filas del terminal.
    const especial = aj.tamano === 'normal' || aj.tamano === 'grande' ? (ESPECIAL[a.estado]?.tam ?? null) : null
    const d = especial ? dibujoSvg(especial, fotogramaEn(a.estado, especial, ahora - a.desde)) : dibujoSvg(tamSvg, fotograma(a.estado, tamSvg, n))
    const escala = 2
    const banda = (
      <Box flexDirection="row" gap={1}>
        <Svg source={d.source} alt={`${NOMBRE}: ${a.estado}`} width={d.ancho * escala} height={d.alto * escala} />
        <Box flexDirection="column">
          <Text color={LILA} bold wrap="truncate-end">
            {NOMBRE}
          </Text>
          <Text color={color} bold wrap="truncate-end">
            {dicho}
          </Text>
          {extra.map(linea => (
            <Text key={linea} dimColor wrap="truncate-end">
              {linea}
            </Text>
          ))}
          <Button key="emi-compacta" label="compacta" onPress={() => update($, ajustes, x => ({ ...x, tamano: 'compacta' as const }))} />
        </Box>
      </Box>
    )
    return ajeno ? (
      <Box flexDirection="column">
        {banda}
        {ajeno}
      </Box>
    ) : (
      banda
    )
  })

  // ---------- El panel de Emi: el mayor sprite que cabe en el hueco real del panel ----------

  on('ui.render', { component: 'Pane', requestId: PANEL }, async ($, e) => {
    const aj = await read($, ajustes)
    const a = await read($, animo)
    const n = await read($, tic)
    const mas = await read($, otras)
    const ahora = Date.now()
    const color = COLORES[a.estado]
    const dicho = textoEstado(a, ahora, n)
    const extra = [a.detalle, mas > 0 ? `+${mas} ${mas === 1 ? 'conversación' : 'conversaciones'} en marcha` : ''].filter(Boolean).join(' · ')
    const filas = e.props.scroll.bodyRows
    const columnas = e.props.bodyColumns
    const volver = () => aBanda($)

    if (e.surface === 'terminal') {
      const { Box, Button, Raster, Text } = $.ui.resolve(e)
      const plan = planPanel(filas, columnas, topeDe(aj.tamano))
      if (!plan) {
        return (
          <Box flexDirection="column">
            <Text color={LILA} bold wrap="wrap">
              {NOMBRE}: el panel es muy pequeño ({columnas} x {filas}).
            </Text>
            <Button key="emi-volver" label="volver a la banda" onPress={volver} />
          </Box>
        )
      }
      // «pensando» tiene su animación de 5 fotogramas a 5 fps (60x60): solo en el panel, con tamaño normal o grande y si cabe con el texto debajo.
      const especial = aj.tamano === 'normal' || aj.tamano === 'grande' ? especialQueCabe(a.estado, filas, columnas) : null
      const m = medidas(especial ?? plan.tam)
      const c = especial ? celdas(especial, fotogramaEn(a.estado, especial, ahora - a.desde)) : celdas(plan.tam, fotograma(a.estado, plan.tam, n))
      const texto = (
        <Box flexDirection="column">
          <Text color={LILA} bold wrap="truncate-end">
            {NOMBRE} · {m.ancho} x {m.alto}
          </Text>
          <Text color={color} bold wrap="truncate-end">
            {dicho}
          </Text>
          <Text dimColor wrap="truncate-end">
            {extra || ' '}
          </Text>
          <Button key="emi-volver" label="volver a la banda" onPress={volver} />
        </Box>
      )
      return especial || plan.texto === 'abajo' ? (
        <Box flexDirection="column">
          <Raster key="emi-panel" columns={c.columnas} rows={c.filas} cells={c.cells} />
          {texto}
        </Box>
      ) : (
        <Box flexDirection="row" gap={1}>
          <Raster key="emi-panel" columns={c.columnas} rows={c.filas} cells={c.cells} />
          {texto}
        </Box>
      )
    }

    const { Box, Button, Svg, Text } = $.ui.resolve(e)
    const tamSvg: Tam = aj.tamano === 'grande' ? 'XL' : aj.tamano === 'mini' ? 'N' : 'L'
    // «pensando»: su animación de 5 fotogramas a 5 fps (60x60); un SVG se escala, así que siempre cabe.
    const especial = aj.tamano === 'normal' || aj.tamano === 'grande' ? (ESPECIAL[a.estado]?.tam ?? null) : null
    const d = especial ? dibujoSvg(especial, fotogramaEn(a.estado, especial, ahora - a.desde)) : dibujoSvg(tamSvg, fotograma(a.estado, tamSvg, n))
    return (
      <Box flexDirection="column">
        <Svg source={d.source} alt={`${NOMBRE}: ${a.estado}`} width={d.ancho * 2} height={d.alto * 2} />
        <Text color={LILA} bold wrap="truncate-end">
          {NOMBRE}
        </Text>
        <Text color={color} bold wrap="truncate-end">
          {dicho}
        </Text>
        <Text dimColor wrap="truncate-end">
          {extra || ' '}
        </Text>
        <Button key="emi-volver" label="volver a la banda" onPress={volver} />
      </Box>
    )
  })
}
