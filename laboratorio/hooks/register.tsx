import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, RenderElement, Timer } from 'claude-code'

import type { LabSeleccion } from '../types'
import { celdas, filasDe, fotograma, fotogramas, indice, medidas, planPanel, TEXTO_COLUMNAS, TEXTO_FILAS } from './dibujo'
import { indiceEn } from './animacion'
import type { Perfil } from './animacion'
import { celdas2 } from './celdas2'
import type { Tam } from './sprites'
import { ANIMACIONES, celdasConv, indiceConv } from './convdibujo'

type $ = EngineInterface

// Laboratorio de Emi. No hace nada hasta que escribes /emilab. Mide, con el motor real, cuánto espacio da la banda sobre el
// prompt y un panel acoplado, y dibuja a Emi en cada tamaño. Las medidas se guardan en ~/.claude/mascota-lab/medidas.json.

const LATIDO = 250
const PANEL = 'emilab'
const CAMBIO_ESTADO = 4000
const ESTADOS = ['nueva', 'escribiendo', 'terminado'] as const
const TAMANOS_NUM: Record<string, Tam> = { '13': 'S', '26': 'N', '40': 'M', '52': 'L', '64': 'XL' }

const seleccion = atom({ plugin: 'mascota-lab', key: 'seleccion' } as const, { tam: 'off', inicio: 0 } as LabSeleccion)
const tic = atom({ plugin: 'mascota-lab', key: 'tic' } as const, 0)

let latido: Timer | undefined
let carpeta = ''
let ultimoTexto = ''

type MedidaBanda = { maxRows: number; bodyColumns: number; columnas: number; filas: number; superficie: string; isFullscreen: boolean | null }
type MedidaPanel = { placement: string; bodyColumns: number; bodyRows: number; isFocused: boolean; veces: number }
let banda: MedidaBanda = { maxRows: 0, bodyColumns: 0, columnas: 0, filas: 0, superficie: '', isFullscreen: null }
let panel: MedidaPanel | null = null
let panelAbierto = false

function guardar($: $) {
  if (!carpeta) {
    return
  }
  const texto = JSON.stringify({ banda, panel, panelAbierto, fecha: new Date().toISOString() })
  const sinFecha = JSON.stringify({ banda, panel, panelAbierto })
  if (sinFecha === ultimoTexto) {
    return
  }
  ultimoTexto = sinFecha
  void $.fs.write(`${carpeta}/medidas.json`, texto).catch(() => undefined)
}

function arrancarLatido($: $) {
  latido?.cancel()
  latido = $.clock.every(LATIDO, () => {
    void update($, tic, n => n + 1).catch(() => undefined)
  })
}

function tieneContenido(arbol: unknown): arbol is RenderElement {
  if (!arbol || typeof arbol !== 'object') {
    return false
  }
  const hijos = (arbol as { children?: unknown }).children
  return (arbol as { type?: unknown }).type === 'Text' || (Array.isArray(hijos) && hijos.length > 0)
}

function informe() {
  const b = banda
  const lineas = [
    `Banda sobre el prompt (medida por el motor): superficie ${b.superficie || '(sin medir)'}, ${b.bodyColumns} columnas x ${b.maxRows} filas como máximo; ventana ${b.columnas} x ${b.filas}; pantalla completa: ${b.isFullscreen === null ? 'sin medir' : b.isFullscreen ? 'sí' : 'no'}.`,
  ]
  if (panel) {
    lineas.push(`Panel de prueba: ${panel.placement}, cuerpo ${panel.bodyColumns} columnas x ${panel.bodyRows} filas (${panel.veces} dibujos).`)
  } else {
    lineas.push('Panel de prueba: sin medir todavía (/emilab pane).')
  }
  for (const [n, t] of Object.entries(TAMANOS_NUM)) {
    const m = medidas(t)
    lineas.push(`  ${n}: ${m.ancho} x ${m.alto} px = ${m.ancho} columnas x ${m.filas} filas -> banda: ${b.maxRows ? (b.maxRows >= m.filas ? 'cabe' : 'NO cabe') : '?'}${panel ? ` | panel: ${panel.bodyRows >= m.filas ? 'cabe' : 'NO cabe'}` : ''}`)
  }
  lineas.push('Uso: /emilab 13|26|40|52|64 (banda), /emilab pane (panel acoplado), /emilab pane off, /emilab off. Medidas en ~/.claude/mascota-lab/medidas.json')
  return lineas.join('\n')
}

async function abrirPanel($: $) {
  const resultado = await $.ui.open({ id: PANEL, title: 'Emi (laboratorio)', columns: 64 }).catch((error: unknown) => ({ isPlaced: false as const, reason: String(error) }))
  panelAbierto = resultado.isPlaced
  arrancarLatido($)
  guardar($)
  return resultado
}

const PROTO = 'emiproto'
// Un tic por fotograma del estado más rápido (4 fps = 250 ms, 8 fps = 125 ms): sin ticks que no cambian nada.
const TICK_BLIT = 250
const TICK_BLIT_FLUIDO = 125
const TICK_ATOMO = 250
const ticProto = atom({ plugin: 'mascota-lab', key: 'ticProto' } as const, 0)

type Modo = 'atomo' | 'blit'
type Fase = { nombre: string; modo: Modo; perfil: Perfil; segundos: number }

const FASES: readonly Fase[] = [
  { nombre: 'A control: redibujar cada 250 ms (como el mod actual)', modo: 'atomo', perfil: 'actual', segundos: 12 },
  { nombre: 'D redibujar cada 125 ms con fotogramas por tiempo (8 fps, sin blit)', modo: 'atomo', perfil: 'fluido', segundos: 12 },
  { nombre: 'B blit, 4 fotogramas por segundo en los estados vivos', modo: 'blit', perfil: 'actual', segundos: 12 },
  { nombre: 'C blit, 8 fotogramas por segundo en los estados vivos', modo: 'blit', perfil: 'fluido', segundos: 12 },
]

const contadores = () => ({ rendersTrasBlit: 0, ticks: 0, renders: 0, renderMs: 0, renderBytes: 0, blits: 0, blitMs: 0, blitBytes: 0, saltados: 0, denegados: 0 })

let c = contadores()
let modo: Modo = 'blit'
let perfil: Perfil = 'actual'
const estado = 'escribiendo'
let inicio = 0
let actual: { tam: Tam; cells: string } | null = null
let enviadas = ''
let ultimoBlit = 0
let timer: Timer | undefined
let resultados: unknown[] = []
let corriendo = false

function celdasEn(tam: Tam, ms: number, n: number) {
  const total = fotogramas(estado, tam).length
  const i = modo === 'atomo' && perfil === 'actual' ? indice(estado, n, total) : indiceEn(estado, ms, perfil, total)
  return celdas2(tam, filasDe(estado, tam, i))
}

async function paso($: $) {
  c.ticks += 1
  if (!actual) {
    return
  }
  const t0 = await $.clock.now()
  const x = celdasEn(actual.tam, t0 - inicio, 0)
  if (x.cells === enviadas) {
    c.saltados += 1
    return
  }
  const r = await $.ui.blit({ requestId: PROTO, key: 'proto', cells: x.cells })
  c.blitMs += (await $.clock.now()) - t0
  if (r.deny) {
    c.denegados += 1
    $.ui.invalidate('ui.render')
    return
  }
  enviadas = x.cells
  actual = { tam: actual.tam, cells: x.cells }
  ultimoBlit = Date.now()
  c.blits += 1
  c.blitBytes += x.cells.length
}

async function arrancar($: $, nuevo: { modo: Modo; perfil: Perfil }) {
  timer?.cancel()
  modo = nuevo.modo
  perfil = nuevo.perfil
  c = contadores()
  enviadas = ''
  inicio = await $.clock.now()
  timer =
    modo === 'atomo'
      ? $.clock.every(perfil === 'fluido' ? TICK_BLIT_FLUIDO : TICK_ATOMO, () => {
          c.ticks += 1
          void update($, ticProto, n => n + 1).catch(() => undefined)
        })
      : $.clock.every(perfil === 'fluido' ? TICK_BLIT_FLUIDO : TICK_BLIT, () => {
          void paso($)
        })
  $.ui.invalidate('ui.render')
}

function informeProto() {
  const f = (n: number, d = 0) => n.toFixed(d)
  return (
    `Prototipo de animación · modo ${modo} · perfil ${perfil} · ${c.ticks} ticks\n` +
    `  pasadas de dibujo: ${c.renders}, ${c.rendersTrasBlit} justo después de un blit (${f(c.renderMs)} ms dentro del dibujo, ${f(c.renderBytes / 1024, 1)} KB de celdas)\n` +
    `  envíos blit: ${c.blits} (${f(c.blitMs)} ms, ${f(c.blitBytes / 1024, 1)} KB) · saltados por no haber cambio: ${c.saltados} · denegados: ${c.denegados}\n` +
    'Uso: /emiproto atomo | atomo8 | blit | fluido | bench | off'
  )
}

async function bench($: $) {
  if (corriendo) {
    return
  }
  corriendo = true
  resultados = []
  const abierto = await $.ui.open({ id: PROTO, title: 'Emi (prototipo)', columns: 64 }).catch((error: unknown) => ({ isPlaced: false as const, reason: String(error) }))
  if (!abierto.isPlaced) {
    resultados = [{ error: abierto.reason }]
  } else {
    for (const fase of FASES) {
      await arrancar($, fase)
      await $.clock.sleep(fase.segundos * 1000)
      resultados.push({ fase: fase.nombre, segundos: fase.segundos, ...c })
    }
    timer?.cancel()
    timer = undefined
    await $.ui.close({ id: PROTO }).catch(() => undefined)
  }
  corriendo = false
  if (carpeta) {
    await $.fs.write(`${carpeta}/bench.json`, JSON.stringify({ fecha: new Date().toISOString(), resultados }, null, 2)).catch(() => undefined)
  }
}

// Prueba de estados con más fotogramas: /emiconv [nueva|pensando|hula|escribiendo|terminado|responde|leyendo|necesita|duerme|guardando] nat60 | nn60 | nn48 | nn40 | nn30 | actual [fps] | off.
const CONVPANEL = 'emiconv'
const ticConv = atom({ plugin: 'mascota-lab', key: 'ticConv' } as const, 0)
let convEstado = 'nueva'
let convVariante = 'nat60'
let convFps = 8
let convInicio = 0
let convTimer: Timer | undefined

function convCeldas(ms: number) {
  if (convVariante === 'actual') {
    const total = fotogramas(convEstado, 'M').length
    return { ...celdas2('M', filasDe(convEstado, 'M', indiceConv(ms, convFps, total))), fotograma: indiceConv(ms, convFps, total) + 1, de: total }
  }
  const de = ANIMACIONES[convEstado]?.variantes[convVariante]?.fotogramas.length ?? 0
  const i = indiceConv(ms, convFps, de)
  const x = celdasConv(convVariante, i, convEstado)
  return x ? { ...x, fotograma: i + 1, de } : null
}


export const register: Register = on => {
  on('command.run', { command: 'emiproto' }, async ($, e) => {
    const orden = e.args.trim().toLowerCase()
    if (orden === 'off') {
      timer?.cancel()
      timer = undefined
      await $.ui.close({ id: PROTO }).catch(() => undefined)
      return { text: 'Prototipo apagado.' }
    }
    if (orden === 'bench') {
      void bench($)
      return { text: 'Comparación en marcha: unos 40 segundos con un panel acoplado; deja los datos en ~/.claude/mascota-lab/bench.json.' }
    }
    if (orden === 'atomo' || orden === 'atomo8' || orden === 'blit' || orden === 'fluido') {
      await $.ui.open({ id: PROTO, title: 'Emi (prototipo)', columns: 64 }).catch(() => undefined)
      await arrancar($, { modo: orden === 'atomo' || orden === 'atomo8' ? 'atomo' : 'blit', perfil: orden === 'fluido' || orden === 'atomo8' ? 'fluido' : 'actual' })
      return { text: `Panel de prototipo abierto en modo ${orden}.` }
    }
    return { text: informeProto() }
  })

  on('ui.render', { component: 'Pane', requestId: PROTO }, async ($, e) => {
    const t0 = Date.now()
    const n = await read($, ticProto)
    if (e.surface !== 'terminal') {
      const { Text } = $.ui.resolve(e)
      return <Text dimColor>El prototipo solo dibuja en el terminal.</Text>
    }
    const { Box, Raster, Text } = $.ui.resolve(e)
    const plan = planPanel(e.props.scroll.bodyRows, e.props.bodyColumns)
    if (!plan) {
      return <Text color="red">Panel demasiado pequeño para el prototipo.</Text>
    }
    const ms = (await $.clock.now()) - inicio
    const x = celdasEn(plan.tam, ms, n)
    actual = { tam: plan.tam, cells: x.cells }
    enviadas = x.cells
    c.renders += 1
    if (Date.now() - ultimoBlit < 40) {
      c.rendersTrasBlit += 1
    }
    c.renderBytes += x.cells.length
    const arbol = (
      <Box flexDirection="column">
        <Raster key="proto" columns={x.columnas} rows={x.filas} cells={x.cells} />
        <Text bold wrap="truncate-end">
          prototipo · {modo} · {perfil}
        </Text>
        <Text dimColor wrap="truncate-end">
          glifos {x.glifos} de {x.columnas * x.filas} celdas
        </Text>
      </Box>
    )
    c.renderMs += Date.now() - t0
    return arbol
  })


  on('command.run', { command: 'emiconv' }, async ($, e) => {
    const partes = e.args.trim().toLowerCase().split(/\s+/).filter(Boolean)
    const estado = partes[0] && partes[0] in ANIMACIONES ? partes.shift()! : 'nueva'
    const orden = partes[0] ?? ''
    const fpsTexto = partes[1] ?? ''
    if (orden === 'off') {
      convTimer?.cancel()
      convTimer = undefined
      await $.ui.close({ id: CONVPANEL }).catch(() => undefined)
      return { text: 'Prueba de estados apagada.' }
    }
    const anim = ANIMACIONES[estado]!
    if (orden !== 'actual' && !anim.variantes[orden]) {
      return { text: `Uso: /emiconv [${Object.keys(ANIMACIONES).join('|')}] ${[...Object.keys(anim.variantes), 'actual'].join(' | ')} [fps] | off  (por defecto nat60 a ${anim.fps} fps en «${estado}»; actual = el estado de hoy, 40x60, 2 fps)` }
    }
    const fps = Number(fpsTexto)
    convEstado = estado
    convVariante = orden
    convFps = fps > 0 && fps <= 30 ? fps : orden === 'actual' ? 2 : anim.fps
    convInicio = await $.clock.now()
    await $.ui.open({ id: CONVPANEL, title: `Emi · ${estado}`, columns: 64 }).catch(() => undefined)
    convTimer?.cancel()
    // Dos tics por fotograma (mínimo 50 ms): el fotograma sale del reloj, así que el tic solo fija cuánto tarda en verse el cambio.
    convTimer = $.clock.every(Math.max(50, Math.round(500 / convFps)), () => {
      void update($, ticConv, n => n + 1).catch(() => undefined)
    })
    return { text: `Panel abierto: ${estado} · ${orden} a ${convFps} fps. Cambia con /emiconv [estado] <variante> [fps]; /emiconv off lo cierra.` }
  })

  on('ui.render', { component: 'Pane', requestId: CONVPANEL }, async ($, e) => {
    await read($, ticConv)
    if (e.surface !== 'terminal') {
      const { Text } = $.ui.resolve(e)
      return <Text dimColor>La prueba solo dibuja en el terminal.</Text>
    }
    const { Box, Raster, Text } = $.ui.resolve(e)
    const x = convCeldas((await $.clock.now()) - convInicio)
    if (!x) {
      return <Text color="red">Variante desconocida.</Text>
    }
    const caben = e.props.bodyColumns >= x.columnas && e.props.scroll.bodyRows >= x.filas + 3
    if (!caben) {
      return <Text color="red">Panel demasiado pequeño: hacen falta {x.columnas} columnas y {x.filas + 3} filas (hay {e.props.bodyColumns} y {e.props.scroll.bodyRows}).</Text>
    }
    return (
      <Box flexDirection="column">
        <Raster key="conv" columns={x.columnas} rows={x.filas} cells={x.cells} />
        <Text bold wrap="truncate-end">
          {convEstado} · {convVariante} · {convFps} fps · fotograma {x.fotograma}/{x.de}
        </Text>
        <Text dimColor wrap="truncate-end">
          {x.columnas} x {x.filas * 2} px · glifos {x.glifos} de {x.columnas * x.filas} celdas
        </Text>
      </Box>
    )
  })

  on('session.start', async ($, e, next) => {
    const hecho = await next(e)
    const casa = (await $.env.get('HOME').catch(() => undefined)) ?? (await $.env.get('USERPROFILE').catch(() => undefined))
    carpeta = casa ? `${casa}/.claude/mascota-lab` : ''
    await $.command.register({
      name: 'emilab',
      description: 'Laboratorio de Emi: /emilab 13|26|40|52|64 | pane | pane off | off',
      argumentHint: '[13 | 26 | 40 | 52 | 64 | pane | pane off | off]',
      immediate: true,
    })
    // Medición automática de una sola vez: si existe auto.txt con «abrir», abre el panel de prueba, deja las medidas y lo cierra.
    if (carpeta) {
      const marca = await $.fs.read(`${carpeta}/auto.txt`).catch(() => '')
      if (typeof marca === 'string' && marca.trim() === 'abrir') {
        await $.fs.write(`${carpeta}/auto.txt`, 'hecho').catch(() => undefined)
        const r = await abrirPanel($)
        $.clock.after(25000, () => {
          void $.ui.close({ id: PANEL }).catch(() => undefined)
          panelAbierto = false
          guardar($)
        })
        void r
      }
    }
    await $.command.register({
      name: 'emiproto',
      description: 'Prototipo de animación de Emi: /emiproto atomo | atomo8 | blit | fluido | bench | off',
      argumentHint: '[atomo | atomo8 | blit | fluido | bench | off]',
      immediate: true,
    })
    await $.command.register({
      name: 'emiconv',
      description: 'Prueba de estados con más fotogramas: /emiconv [nueva|pensando|hula] nat60 | nn60 | nn48 | nn40 | nn30 | actual [fps] | off',
      argumentHint: '[nueva | pensando] [nat60 | nn60 | nn48 | nn40 | nn30 | actual] [fps] | off',
      immediate: true,
    })
    // Medición automática de una sola vez: si auto.txt contiene «bench», compara las tres formas de animar y deja bench.json.
    if (carpeta) {
      const marcaBench = await $.fs.read(`${carpeta}/auto.txt`).catch(() => '')
      if (typeof marcaBench === 'string' && marcaBench.trim() === 'bench') {
        await $.fs.write(`${carpeta}/auto.txt`, 'hecho').catch(() => undefined)
        void bench($)
      }
    }
    return hecho
  })

  on('command.run', { command: 'emilab' }, async ($, e) => {
    const orden = e.args.trim().toLowerCase()
    if (orden === 'off' || orden === 'no') {
      latido?.cancel()
      latido = undefined
      await update($, seleccion, () => ({ tam: 'off', inicio: 0 }))
      await $.ui.close({ id: PANEL }).catch(() => undefined)
      panelAbierto = false
      guardar($)
      return { text: 'Laboratorio apagado.' }
    }
    if (orden === 'pane off' || orden === 'panel off') {
      await $.ui.close({ id: PANEL }).catch(() => undefined)
      panelAbierto = false
      guardar($)
      return { text: 'Panel de prueba cerrado.' }
    }
    if (orden === 'pane' || orden === 'panel') {
      const r = await abrirPanel($)
      return { text: r.isPlaced ? 'Panel de prueba abierto: las medidas se guardan solas. Para cerrarlo: /emilab pane off.' : `El panel no se pudo colocar: ${r.reason}` }
    }
    const tam = TAMANOS_NUM[orden]
    if (tam) {
      await update($, seleccion, () => ({ tam: orden as LabSeleccion['tam'], inicio: Date.now() }))
      arrancarLatido($)
      return { text: `Banda de prueba a ${orden} (${medidas(tam).ancho} x ${medidas(tam).alto} px). Cambia de estado cada 4 s.\n${informe()}` }
    }
    return { text: informe() }
  })

  on('ui.close', async ($, e, next) => {
    if (e.id === PANEL) {
      panelAbierto = false
      guardar($)
    }
    return next(e)
  }).catch(($, e, next) => next(e))

  // ---------- La banda de prueba (y la medición de la banda, siempre) ----------

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    banda = {
      maxRows: e.props.maxRows,
      bodyColumns: e.props.bodyColumns,
      columnas: e.viewport?.columns ?? 0,
      filas: e.viewport?.rows ?? 0,
      superficie: e.surface,
      isFullscreen: e.viewport?.isFullscreen ?? null,
    }
    guardar($)
    const sel = await read($, seleccion)
    const tamNum = sel.tam === 'off' ? null : TAMANOS_NUM[sel.tam]
    if (!tamNum || e.props.hasSurvey || e.surface !== 'terminal') {
      return next(e)
    }
    const n = await read($, tic)
    const { Box, Text, Raster } = $.ui.resolve(e)
    const estado = ESTADOS[Math.floor((Date.now() - sel.inicio) / CAMBIO_ESTADO) % ESTADOS.length] ?? 'nueva'
    const c = celdas(tamNum, fotograma(estado, tamNum, n))
    const cabe = e.props.maxRows >= c.filas
    const resto = await next(e).catch(() => undefined)
    const cuerpo = (
      <Box flexDirection="row" gap={1}>
        <Raster key="lab" columns={c.columnas} rows={c.filas} cells={c.cells} />
        <Box flexDirection="column">
          <Text bold wrap="truncate-end">
            Laboratorio · {sel.tam} · estado {estado}
          </Text>
          <Text wrap="truncate-end">
            Ocupa {c.columnas} columnas x {c.filas} filas
          </Text>
          <Text wrap="truncate-end">
            Banda: {e.props.bodyColumns} columnas x {e.props.maxRows} filas máx.
          </Text>
          <Text color={cabe ? 'green' : 'red'} bold wrap="truncate-end">
            {cabe ? 'Cabe entero' : 'NO cabe entero: se desplaza o se recorta'}
          </Text>
        </Box>
      </Box>
    )
    return tieneContenido(resto) ? (
      <Box flexDirection="column">
        {cuerpo}
        {resto}
      </Box>
    ) : (
      cuerpo
    )
  })

  // ---------- El panel de prueba ----------

  on('ui.render', { component: 'Pane', requestId: PANEL }, async ($, e) => {
    const n = await read($, tic)
    if (e.surface !== 'terminal') {
      const { Text } = $.ui.resolve(e)
      return <Text dimColor>El panel de prueba solo dibuja en el terminal.</Text>
    }
    const { Box, Text, Raster } = $.ui.resolve(e)
    const filas = e.props.scroll.bodyRows
    const columnas = e.props.bodyColumns
    panel = { placement: e.props.placement, bodyColumns: columnas, bodyRows: filas, isFocused: e.props.isFocused, veces: (panel?.veces ?? 0) + 1 }
    guardar($)
    const plan = planPanel(filas, columnas)
    if (!plan) {
      return (
        <Text color="red" wrap="wrap">
          El panel ({columnas} x {filas}) es demasiado pequeño para el sprite menor.
        </Text>
      )
    }
    const estado = ESTADOS[Math.floor(n / 16) % ESTADOS.length] ?? 'nueva'
    const c = celdas(plan.tam, fotograma(estado, plan.tam, n))
    const datos = (
      <Box flexDirection="column">
        <Text bold wrap="truncate-end">
          {e.props.placement} · cuerpo {columnas} x {filas}
        </Text>
        <Text wrap="truncate-end">
          sprite {plan.tam}: {c.columnas} x {c.filas} filas
        </Text>
        <Text wrap="truncate-end">texto: {plan.texto}</Text>
        <Text dimColor wrap="truncate-end">
          estado {estado}
        </Text>
      </Box>
    )
    return plan.texto === 'abajo' ? (
      <Box flexDirection="column">
        <Raster key="panel" columns={c.columnas} rows={c.filas} cells={c.cells} />
        {datos}
      </Box>
    ) : (
      <Box flexDirection="row" gap={1}>
        <Raster key="panel" columns={c.columnas} rows={c.filas} cells={c.cells} />
        {datos}
      </Box>
    )
  })
}

void TEXTO_COLUMNAS
void TEXTO_FILAS
