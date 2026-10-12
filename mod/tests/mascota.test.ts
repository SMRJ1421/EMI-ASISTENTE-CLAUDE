import { describe, expect, mock, test } from 'claude-code/testing'

import { esFalloReal, esRechazo, RECHAZO } from '../hooks/deteccion'
import { ESPECIAL } from '../hooks/animaciones'
import { celdas, PASO_MS, colorDe, descomprimir, dibujoSvg, elegirTam, especialEnBanda, especialQueCabe, filasDe, fotograma, fotogramaEn, fotogramas, indice, leerCeldas, medidas, ORDEN, planPanel, TARJETA } from '../hooks/dibujo'
import { ESTADOS, FRASES, detalleDe, estadoDeHerramienta } from '../hooks/estados'
import { ALFABETO, TAMANOS } from '../hooks/sprites'

const BANDA = {
  hasSurvey: false,
  isWorking: false,
  maxRows: 40,
  bodyColumns: 140,
  scroll: { offset: 0, bodyRows: 40 },
  view: {},
}
const PANEL = { title: 'Emi', isFocused: false, bodyColumns: 62, placement: 'dock' as const, scroll: { offset: 0, bodyRows: 38 }, view: {} }

const cualquiera = (frases: readonly string[]) => new RegExp(frases.map(f => f.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'))

const opacos = (filas: readonly string[]) => filas.join('').split('').filter(c => c !== '.').length

const sueloDe = (filas: readonly string[]) => {
  const minimo = Math.max(3, Math.round((filas[0]?.length ?? 12) / 4))
  let ultimo = 0
  filas.forEach((fila, y) => {
    if (fila.split('').filter(c => c !== '.').length >= minimo) {
      ultimo = y
    }
  })
  return ultimo
}

describe('los datos de los sprites', () => {
  test('12 estados x 4 fotogramas x 5 tamaños, todos rectangulares y con colores válidos', () => {
    for (const t of ORDEN) {
      const d = TAMANOS[t]
      expect(d.alto % 2).toBe(0)
      for (const estado of ESTADOS) {
        const frames = fotogramas(estado, t)
        expect(frames.length).toBe(4)
        for (const f of frames) {
          const filas = f.split('/').map(descomprimir)
          expect(filas.length).toBe(d.alto)
          expect(filas.every(fila => fila.length === d.ancho)).toBe(true)
          expect(filas.join('').split('').every(c => c === '.' || ALFABETO.includes(c))).toBe(true)
        }
      }
    }
  })

  test('la descompresión de tramos es exacta', () => {
    expect(descomprimir('ab§5c.d')).toBe('abccccc.d')
    expect(descomprimir('§z.')).toBe('.'.repeat(35))
    expect(descomprimir('abc')).toBe('abc')
  })

  test('los cuatro fotogramas de un estado son distintos en todos los tamaños (hay animación)', () => {
    for (const t of ORDEN) {
      for (const estado of ESTADOS) {
        expect(new Set(fotogramas(estado, t)).size).toBeGreaterThan(1)
      }
    }
  })

  test('el fotograma avanza un paso por tic en todos los estados (4 fps)', () => {
    expect(indice('escribiendo', 0, 4)).toBe(0)
    expect(indice('escribiendo', 1, 4)).toBe(1)
    expect(indice('duerme', 1, 4)).toBe(1)
    expect(indice('duerme', 2, 4)).toBe(2)
    expect(fotograma('baile', 'L', 0).join('/')).not.toBe(fotograma('baile', 'L', 1).join('/'))
  })
})

describe('fidelidad: Emi sale completa y sin deformar', () => {
  test('los 240 fotogramas tienen cuerpo completo (ni vacíos ni cortados)', () => {
    for (const t of ORDEN) {
      const d = TAMANOS[t]
      for (const estado of ESTADOS) {
        for (let i = 0; i < 4; i += 1) {
          expect(opacos(fotograma(estado, t, i))).toBeGreaterThan(d.ancho * d.alto * 0.15)
        }
      }
    }
  })

  test('los 4 fotogramas de un estado mantienen el suelo (sin saltos que no sean del dibujo)', () => {
    for (const t of ORDEN) {
      const margen = Math.ceil((2 * TAMANOS[t].alto) / 40)
      for (const estado of ESTADOS) {
        const suelos = [0, 1, 2, 3].map(i => sueloDe(fotograma(estado, t, i)))
        expect(Math.max(...suelos) - Math.min(...suelos)).toBeLessThanOrEqual(margen)
      }
    }
  })

  test('las proporciones se conservan: ancho / alto ≈ 0,65 en todos los tamaños', () => {
    for (const t of ORDEN) {
      const m = medidas(t)
      expect(Math.abs(m.ancho / m.alto - 0.65)).toBeLessThan(0.025)
    }
  })

  test('el tamaño mini es la mitad exacta del nativo', () => {
    expect(medidas('S').ancho * 2).toBe(medidas('N').ancho)
    expect(medidas('S').alto * 2).toBe(medidas('N').alto)
  })
})

describe('elegir el tamaño según el espacio', () => {
  test('la banda de 15 filas solo admite el mini; más espacio, más tamaño', () => {
    expect(elegirTam(15, 151)).toBe('S')
    expect(elegirTam(20, 151)).toBe('N')
    expect(elegirTam(30, 151)).toBe('M')
    expect(elegirTam(40, 151)).toBe('L')
    expect(elegirTam(48, 151)).toBe('XL')
    expect(elegirTam(48, 151, 'L')).toBe('L')
    expect(elegirTam(48, 40)).toBe('M')
    expect(elegirTam(9, 151)).toBeNull()
  })

  test('plan del panel: el mayor sprite, con el texto debajo o al lado', () => {
    expect(planPanel(38, 62)?.tam).toBe('M')
    expect(planPanel(38, 80)).toEqual({ tam: 'M', texto: 'abajo' })
    expect(planPanel(40, 80)).toEqual({ tam: 'L', texto: 'lado' })
    expect(planPanel(44, 62)).toEqual({ tam: 'L', texto: 'abajo' })
    expect(planPanel(52, 80)).toEqual({ tam: 'XL', texto: 'abajo' })
    expect(planPanel(5, 62)).toBeNull()
  })
})

describe('celdas, SVG y rendimiento', () => {
  test('celdas y SVG de cada tamaño: dimensiones y límites del motor', () => {
    for (const t of ORDEN) {
      const m = medidas(t)
      const filas = fotograma('escribiendo', t, 0)
      const c = celdas(t, filas)
      expect([c.columnas, c.filas]).toEqual([m.ancho, m.filas])
      expect(c.columnas).toBeLessThanOrEqual(512)
      expect(c.filas).toBeLessThanOrEqual(256)
      expect(dibujoSvg(t, filas).source.length).toBeLessThan(131072)
    }
  })

  test('convertir los 240 fotogramas es rápido y, ya convertidos, cada redibujo cuesta casi nada', () => {
    const t0 = Date.now()
    for (const t of ORDEN) {
      for (const estado of ESTADOS) {
        for (let i = 0; i < 4; i += 1) {
          celdas(t, fotograma(estado, t, i))
        }
      }
    }
    const primera = Date.now() - t0
    const t1 = Date.now()
    for (let vuelta = 0; vuelta < 40; vuelta += 1) {
      for (const t of ORDEN) {
        celdas(t, fotograma('escribiendo', t, vuelta))
      }
    }
    const repetida = Date.now() - t1
    expect(primera).toBeLessThan(5000)
    expect(repetida).toBeLessThan(500)
  })
})

describe('qué hace Emi con cada herramienta', () => {
  test('lee, escribe, pregunta', () => {
    expect(estadoDeHerramienta('Read')).toBe('leyendo')
    expect(estadoDeHerramienta('Grep')).toBe('leyendo')
    expect(estadoDeHerramienta('Edit')).toBe('escribiendo')
    expect(estadoDeHerramienta('PowerShell')).toBe('escribiendo')
    expect(estadoDeHerramienta('AskUserQuestion')).toBe('necesita')
    expect(estadoDeHerramienta('mcp__odoo__search_records')).toBe('leyendo')
    expect(estadoDeHerramienta('mcp__odoo__update_record')).toBe('escribiendo')
  })

  test('la pista corta lleva el nombre del archivo, no la ruta', () => {
    expect(detalleDe('Read', { file_path: 'C:\\Users\\Admin0011\\Downloads\\informe.docx' })).toBe('Read informe.docx')
    expect(detalleDe('Edit', { file_path: 'C:/x/y/z.ts' })).toBe('Edit z.ts')
  })
})

describe('la barra', () => {
  test('se dibuja en el terminal (todos los tamaños) y en el escritorio', async $ => {
    await $.command.run({ command: 'emi', args: 'app' })
    for (const tamano of ['grande', 'normal', 'mini', 'compacta']) {
      await $.command.run({ command: 'emi', args: tamano } as never)
      for (const surface of ['terminal', 'desktop'] as const) {
        const ui = await $.ui.mount({ plugin: 'mascota', surface, component: 'AbovePrompt', props: BANDA })
        expect(await ui.find({ type: 'Text', text: 'Emi' })).toBeDefined()
        await ui.unmount()
      }
    }
    await $.command.run({ command: 'emi', args: 'normal' } as never)
  })

  test('con solo 15 filas (tu terminal de 41) elige el mini y avisa de que el panel la ve más grande', async $ => {
    const ui = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'AbovePrompt', props: { ...BANDA, maxRows: 15, bodyColumns: 151 } })
    expect(await ui.find({ type: 'Text', text: 'Emi' })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: '/emi panel' })).toBeDefined()
    await ui.unmount()
  })

  test('con menos de 10 filas pasa sola a la línea compacta', async $ => {
    const ui = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'AbovePrompt', props: { ...BANDA, maxRows: 6 } })
    expect(await ui.find({ type: 'Button', text: 'agrandar' })).toBeDefined()
    await ui.unmount()
  })

  test('los estados siguen a las herramientas', async ($, on) => {
    on('tool.call', () => ({ result: 'ok' }))
    await $.tool.call({ tool: 'Read', file_path: 'C:/x/informe.docx' })
    const leyendo = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'AbovePrompt', props: BANDA })
    expect(await leyendo.find({ type: 'Text', text: 'Read informe.docx' })).toBeDefined()
    expect(await leyendo.find({ type: 'Text', text: cualquiera(FRASES.leyendo) })).toBeDefined()
    await leyendo.unmount()
    await $.tool.call({ tool: 'Edit', file_path: 'C:/x/informe.docx', old_string: 'a', new_string: 'b' })
    await $.command.run({ command: 'emi', args: 'app' })
    const escribiendo = await $.ui.mount({ plugin: 'mascota', surface: 'desktop', component: 'AbovePrompt', props: BANDA })
    expect(await escribiendo.find({ type: 'Text', text: 'Edit informe.docx' })).toBeDefined()
    await escribiendo.unmount()
  })

  test('una herramienta que falla asusta a Emi', async ($, on) => {
    on('tool.call', () => ({ result: 'boom', isError: true }) as never)
    await $.tool.call({ tool: 'Bash', command: 'exit 1' })
    const ui = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'AbovePrompt', props: BANDA })
    expect(await ui.find({ type: 'Text', text: cualquiera(FRASES.falla) })).toBeDefined()
    await ui.unmount()
  })

  test('piensa y termina con confeti', async ($, on) => {
    on('turn.start', (_$, e) => ({ turnId: e.turnId }))
    on('turn.complete', () => ({ text: '' }))
    await $.turn.start({ text: 'hola', turnId: 't1' })
    const pensando = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'AbovePrompt', props: BANDA })
    expect(await pensando.find({ type: 'Text', text: /cavilando|rumiando|vueltas|maquinando|cabos|idea/ })).toBeDefined()
    await pensando.unmount()
    await $.turn.complete({ reason: 'answer', turnId: 't1' } as never)
    const listo = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'AbovePrompt', props: BANDA })
    expect(await listo.find({ type: 'Text', text: cualquiera(FRASES.terminado) })).toBeDefined()
    await listo.unmount()
  })
})

describe('el panel acoplado', () => {
  test('se dibuja en terminal y en escritorio con el espacio que le da el motor', async $ => {
    for (const [filas, columnas] of [[38, 62], [38, 80], [52, 80], [14, 62]] as const) {
      const ui = await $.ui.mount({
        plugin: 'mascota',
        surface: 'terminal',
        component: 'Pane',
        requestId: 'emi',
        props: { ...PANEL, bodyColumns: columnas, scroll: { offset: 0, bodyRows: filas } },
      })
      expect(await ui.find({ type: 'Text', text: 'Emi' })).toBeDefined()
      await ui.unmount()
    }
    const escritorio = await $.ui.mount({ plugin: 'mascota', surface: 'desktop', component: 'Pane', requestId: 'emi', props: PANEL })
    expect(await escritorio.find({ type: 'Text', text: 'Emi' })).toBeDefined()
    await escritorio.unmount()
  })

  test('un panel demasiado pequeño lo dice y ofrece volver a la banda', async $ => {
    const ui = await $.ui.mount({
      plugin: 'mascota',
      surface: 'terminal',
      component: 'Pane',
      requestId: 'emi',
      props: { ...PANEL, bodyColumns: 62, scroll: { offset: 0, bodyRows: 5 } },
    })
    expect(await ui.find({ type: 'Text', text: 'muy pequeño' })).toBeDefined()
    expect(await ui.find({ type: 'Button', text: 'volver a la banda' })).toBeDefined()
    await ui.unmount()
  })

  test('/emi panel abre el panel y esconde la banda; /emi banda la devuelve', async ($, on) => {
    on('ui.open', () => ({ value: { isPlaced: true } }) as never)
    on('ui.close', () => ({ value: undefined }) as never)
    on('ui.render', () => ({ type: 'engine', ref: 1 }) as never)
    const abierto = await $.command.run({ command: 'emi', args: 'panel' } as never)
    expect(JSON.stringify(abierto)).toContain('panel acoplado')
    const oculta = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'AbovePrompt', props: BANDA })
    expect(await oculta.find({ type: 'Text', text: 'Emi' })).toBeUndefined()
    await oculta.unmount()
    await $.command.run({ command: 'emi', args: 'banda' } as never)
    const vuelve = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'AbovePrompt', props: BANDA })
    expect(await vuelve.find({ type: 'Text', text: 'Emi' })).toBeDefined()
    await vuelve.unmount()
  })

  test('si el motor no puede colocar el panel, Emi sigue en la banda y se explica por qué', async ($, on) => {
    on('ui.open', () => ({ value: { isPlaced: false, reason: 'terminal estrecho' } }) as never)
    on('ui.close', () => ({ value: undefined }) as never)
    const r = await $.command.run({ command: 'emi', args: 'panel' } as never)
    expect(JSON.stringify(r)).toContain('No pude abrir el panel')
    expect(JSON.stringify(r)).toContain('terminal estrecho')
    const ui = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'AbovePrompt', props: BANDA })
    expect(await ui.find({ type: 'Text', text: 'Emi' })).toBeDefined()
    await ui.unmount()
  })
})

describe('los comandos', () => {
  test('/emi sin argumentos explica el modo y los comandos', async $ => {
    const r = await $.command.run({ command: 'emi', args: '' } as never)
    expect(JSON.stringify(r)).toContain('/emi panel | banda')
    expect(JSON.stringify(r)).toContain('banda')
  })

  test('/emi oculta la esconde', async ($, on) => {
    on('ui.render', () => ({ type: 'engine', ref: 1 }) as never)
    await $.command.run({ command: 'emi', args: 'oculta' } as never)
    const ui = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'AbovePrompt', props: BANDA })
    expect(await ui.find({ type: 'Text', text: 'Emi' })).toBeUndefined()
    await ui.unmount()
    await $.command.run({ command: 'emi', args: 'normal' } as never)
  })
})

describe('detección de fallos reales', () => {
  const normal = { denegadoPorCheck: false, turnoAbortado: false }

  test('solo un error de verdad es un fallo; denegaciones, rechazos e interrupciones no', () => {
    expect(esFalloReal({ isError: true, text: 'command not found' }, normal)).toBe(true)
    expect(esFalloReal({ isError: false, text: 'ok' }, normal)).toBe(false)
    expect(esFalloReal({ deny: 'bloqueado por un hook' }, normal)).toBe(false)
    expect(esFalloReal({ isError: true, text: 'boom' }, { denegadoPorCheck: true, turnoAbortado: false })).toBe(false)
    expect(esFalloReal({ isError: true, text: 'boom' }, { denegadoPorCheck: false, turnoAbortado: true })).toBe(false)
    expect(esFalloReal({ isError: true, text: "The user doesn't want to proceed with this tool use." }, normal)).toBe(false)
    expect(esFalloReal({ isError: true, text: '[Request interrupted by user for tool use]' }, normal)).toBe(false)
    expect(RECHAZO.test('Permission to use Bash has been denied.')).toBe(true)
    expect(RECHAZO.test('ENOENT: no such file')).toBe(false)
  })

  test('un rechazo no es un fallo ni un éxito', () => {
    expect(esRechazo({ deny: 'x' }, normal)).toBe(true)
    expect(esRechazo({ isError: true, text: 'The user rejected this' }, normal)).toBe(true)
    expect(esRechazo({ isError: true, text: 'command not found' }, normal)).toBe(false)
    expect(esRechazo({ isError: false, text: 'ok' }, normal)).toBe(false)
  })

  test('una denegación de otro plugin ya no asusta a Emi: sigue pensando', async ($, on) => {
    on('tool.call', () => ({ deny: 'bloqueada por otro plugin' }))
    await $.tool.call({ tool: 'Bash', command: 'ls' })
    const ui = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'AbovePrompt', props: BANDA })
    expect(await ui.find({ type: 'Text', text: cualquiera(FRASES.falla) })).toBeUndefined()
    expect(await ui.find({ type: 'Text', text: cualquiera(FRASES.pensando.map(f => f.replace('…', ''))) })).toBeDefined()
    await ui.unmount()
  })

  test('un permiso que rechazas tú ya no asusta a Emi', async ($, on) => {
    on('tool.call', () => ({ result: "The user doesn't want to proceed with this tool use.", isError: true }) as never)
    await $.tool.call({ tool: 'Bash', command: 'rm x' })
    const ui = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'AbovePrompt', props: BANDA })
    expect(await ui.find({ type: 'Text', text: cualquiera(FRASES.falla) })).toBeUndefined()
    await ui.unmount()
  })

  test('un error real sigue asustando a Emi', async ($, on) => {
    on('tool.call', () => ({ result: 'ENOENT: no such file or directory', isError: true }) as never)
    await $.tool.call({ tool: 'Read', file_path: 'C:/no/existe.txt' })
    const ui = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'AbovePrompt', props: BANDA })
    expect(await ui.find({ type: 'Text', text: cualquiera(FRASES.falla) })).toBeDefined()
    await ui.unmount()
  })

  test('aprobar un plan (ExitPlanMode) es «te necesita», igual que una pregunta', async ($, on) => {
    expect(estadoDeHerramienta('ExitPlanMode')).toBe('necesita')
    expect(estadoDeHerramienta('AskUserQuestion')).toBe('necesita')
    expect(detalleDe('ExitPlanMode', {})).toBe('te pide aprobar el plan')
    on('tool.call', () => ({ result: 'ok' }))
    await $.tool.call({ tool: 'ExitPlanMode', plan: 'plan' } as never)
    const ui = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'AbovePrompt', props: BANDA })
    expect(await ui.find({ type: 'Text', text: cualquiera(FRASES.necesita) })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: 'te pide aprobar el plan' })).toBeDefined()
    await ui.unmount()
  })
})

describe('celdas Raster: espacio con fondo cuando las dos mitades son iguales', () => {
  test('la imagen es exactamente la misma que con un glifo en cada celda, en los 240 fotogramas', () => {
    let glifos = 0
    let total = 0
    for (const t of ORDEN) {
      for (const estado of ESTADOS) {
        for (let i = 0; i < 4; i += 1) {
          const filas = fotograma(estado, t, i)
          const c = celdas(t, filas)
          const visto = leerCeldas(c)
          const esperadoArriba: number[] = []
          const esperadoAbajo: number[] = []
          for (let r = 0; r < filas.length; r += 2) {
            for (let x = 0; x < (filas[0]?.length ?? 0); x += 1) {
              const a = filas[r]?.[x] ?? '.'
              const b = filas[r + 1]?.[x] ?? '.'
              esperadoArriba.push(a === '.' ? TARJETA : colorDe(t, a))
              esperadoAbajo.push(b === '.' ? TARJETA : colorDe(t, b))
            }
          }
          expect(visto.arriba).toEqual(esperadoArriba)
          expect(visto.abajo).toEqual(esperadoAbajo)
          glifos += c.glifos
          total += c.columnas * c.filas
        }
      }
    }
    expect(glifos / total).toBeLessThan(0.5)
  })

  test('el tamaño del panel actual (40x60) usa menos de la mitad de glifos', () => {
    let glifos = 0
    let total = 0
    for (const estado of ESTADOS) {
      for (let i = 0; i < 4; i += 1) {
        const c = celdas('M', fotograma(estado, 'M', i))
        glifos += c.glifos
        total += c.columnas * c.filas
      }
    }
    expect(glifos / total).toBeLessThan(0.45)
  })
})

describe('hula (de guardia) con 8 fotogramas con 5 fps, sin tarjeta', () => {
  test('la hoja tiene 8 fotogramas distintos y deja ver el fondo (arte naranja de guardia)', () => {
    expect(ESPECIAL['hula']).toEqual({ tam: 'H5', chico: 'H5S', tarjeta: false })
    expect(medidas('H5')).toEqual({ ancho: 60, alto: 60, filas: 30 })
    expect(medidas('H5S')).toEqual({ ancho: 28, alto: 28, filas: 14 })
    const vistos = new Set<string>()
    for (let i = 0; i < 8; i += 1) {
      const filas = filasDe('hula', 'H5', i)
      expect(filas.length).toBe(60)
      expect(filas.every(f => f.length === 60)).toBe(true)
      vistos.add(filas.join('/'))
    }
    expect(vistos.size).toBe(8)
    // Sin tarjeta: la primera celda (vacía) usa el color por defecto del terminal y el SVG no lleva recuadro.
    const c = celdas('H5', filasDe('hula', 'H5', 0))
    const bytes = (Uint8Array as unknown as { fromBase64: (s: string) => Uint8Array }).fromBase64(c.cells)
    const w = new Uint32Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / 4)
    expect(w[2]).toBe(0x01000000)
    expect(dibujoSvg('H5', filasDe('hula', 'H5', 0)).source).not.toContain('<rect')
  })

  test('el fotograma cambia cada 200 ms y el ciclo de 8 dura 1,6 s', () => {
    const f = (ms: number) => fotogramaEn('hula', 'H5', ms).join('/')
    expect(f(199)).toBe(f(0))
    expect(f(200)).toBe(filasDe('hula', 'H5', 1).join('/'))
    expect(f(1600)).toBe(f(0))
  })
})

describe('sonido al terminar', () => {
  test('cada vez que Claude termina suena el pitido de «listo», aunque el encargo sea corto; el globo de Windows solo en los largos', async ($, on) => {
    const reloj = mock.clock(on)
    const guiones: string[] = []
    on('process.run', (_$, e) => {
      guiones.push(JSON.stringify(e))
      return { value: { exitCode: 0, stdout: '', stderr: '' } } as never
    })
    on('turn.start', (_$, e) => ({ turnId: e.turnId }))
    on('turn.complete', () => ({ text: '' }))
    on('env.get', (_$, e) => ({ value: (e as { name?: string }).name === 'OS' ? 'Windows_NT' : undefined }) as never)
    on('command.register', () => ({ value: undefined }) as never)
    on('session.start', (_$, e) => ({ cwd: e.cwd }) as never)
    await $.session.start({ cwd: 'C:/x', source: 'startup' } as never)
    await $.command.run({ command: 'emi', args: 'sonido' } as never)
    await $.command.run({ command: 'emi', args: 'avisos' } as never)
    await $.turn.start({ text: 'hola', turnId: 't20' })
    await $.turn.complete({ reason: 'answer', turnId: 't20' } as never)
    await reloj.advance(100)
    const listos = guiones.filter(g => g.includes('Beep(784,110)'))
    expect(listos.length).toBe(1)
    expect(listos[0]).not.toContain('ShowBalloonTip')
    await $.command.run({ command: 'emi', args: 'silencio' } as never)
    await $.turn.start({ text: 'otra', turnId: 't21' })
    await $.turn.complete({ reason: 'answer', turnId: 't21' } as never)
    await reloj.advance(100)
    expect(guiones.filter(g => g.includes('Beep(784,110)')).length).toBe(1)
  })
})

describe('escribiendo / comandos con 8 fotogramas con 5 fps', () => {
  test('la hoja tiene 8 fotogramas distintos de 60x60 sin tarjeta, y avanza uno cada 200 ms', () => {
    expect(ESPECIAL['escribiendo']).toEqual({ tam: 'E5', chico: 'E5S', tarjeta: false })
    expect(medidas('E5')).toEqual({ ancho: 60, alto: 60, filas: 30 })
    expect(medidas('E5S')).toEqual({ ancho: 28, alto: 28, filas: 14 })
    const vistos = new Set<string>()
    for (let i = 0; i < 8; i += 1) {
      const filas = filasDe('escribiendo', 'E5', i)
      expect(filas.length).toBe(60)
      expect(filas.every(f => f.length === 60)).toBe(true)
      vistos.add(filas.join('/'))
    }
    expect(vistos.size).toBe(8)
    const f = (ms: number) => fotogramaEn('escribiendo', 'E5', ms).join('/')
    expect(f(199)).toBe(f(0))
    expect(f(200)).toBe(filasDe('escribiendo', 'E5', 1).join('/'))
    expect(f(1600)).toBe(f(0))
    expect(especialQueCabe('escribiendo', 34, 60)).toBe('E5')
    expect(especialEnBanda('escribiendo', 14, 151)).toBe('E5S')
  })
})

describe('terminado con 8 fotogramas con 5 fps (60x60)', () => {
  test('la hoja tiene 8 fotogramas distintos, en el panel, la banda alta y la banda de 14 filas', () => {
    expect(ESPECIAL['terminado']).toEqual({ tam: 'T5', chico: 'T5S', tarjeta: false })
    expect(medidas('T5')).toEqual({ ancho: 60, alto: 60, filas: 30 })
    expect(medidas('T5S')).toEqual({ ancho: 28, alto: 28, filas: 14 })
    const vistos = new Set<string>()
    for (let i = 0; i < 8; i += 1) {
      const filas = filasDe('terminado', 'T5', i)
      expect(filas.length).toBe(60)
      expect(filas.every(f => f.length === 60)).toBe(true)
      vistos.add(filas.join('/'))
    }
    expect(vistos.size).toBe(8)
    expect(fotogramaEn('terminado', 'T5', 1600).join('/')).toBe(fotogramaEn('terminado', 'T5', 0).join('/'))
    expect(especialQueCabe('terminado', 34, 60)).toBe('T5')
    expect(especialEnBanda('terminado', 14, 151)).toBe('T5S')
  })
})

describe('responde (te responde) con 8 fotogramas con 5 fps (60x60)', () => {
  test('la hoja tiene 8 fotogramas distintos y se usa en el panel y en las bandas', () => {
    expect(ESPECIAL['responde']).toEqual({ tam: 'R5', chico: 'R5S', tarjeta: false })
    expect(medidas('R5')).toEqual({ ancho: 60, alto: 60, filas: 30 })
    expect(medidas('R5S')).toEqual({ ancho: 28, alto: 28, filas: 14 })
    const vistos = new Set<string>()
    for (let i = 0; i < 8; i += 1) {
      const filas = filasDe('responde', 'R5', i)
      expect(filas.length).toBe(60)
      expect(filas.every(f => f.length === 60)).toBe(true)
      vistos.add(filas.join('/'))
    }
    expect(vistos.size).toBe(8)
    expect(fotogramaEn('responde', 'R5', 1600).join('/')).toBe(fotogramaEn('responde', 'R5', 0).join('/'))
    expect(especialQueCabe('responde', 34, 60)).toBe('R5')
    expect(especialEnBanda('responde', 14, 151)).toBe('R5S')
  })
})

describe('leyendo con 8 fotogramas con 5 fps (60x60)', () => {
  test('la hoja tiene 8 fotogramas distintos y se usa en el panel y en las bandas', () => {
    expect(ESPECIAL['leyendo']).toEqual({ tam: 'L5', chico: 'L5S', tarjeta: false })
    expect(medidas('L5')).toEqual({ ancho: 60, alto: 60, filas: 30 })
    expect(medidas('L5S')).toEqual({ ancho: 28, alto: 28, filas: 14 })
    const vistos = new Set<string>()
    for (let i = 0; i < 8; i += 1) {
      const filas = filasDe('leyendo', 'L5', i)
      expect(filas.length).toBe(60)
      expect(filas.every(f => f.length === 60)).toBe(true)
      vistos.add(filas.join('/'))
    }
    expect(vistos.size).toBe(8)
    expect(fotogramaEn('leyendo', 'L5', 200).join('/')).toBe(filasDe('leyendo', 'L5', 1).join('/'))
    expect(fotogramaEn('leyendo', 'L5', 1600).join('/')).toBe(fotogramaEn('leyendo', 'L5', 0).join('/'))
    expect(especialQueCabe('leyendo', 34, 60)).toBe('L5')
    expect(especialEnBanda('leyendo', 14, 151)).toBe('L5S')
  })
})

describe('necesita con 8 fotogramas con 5 fps (60x60)', () => {
  test('la hoja tiene 8 fotogramas distintos y se usa en el panel y en las bandas', () => {
    expect(ESPECIAL['necesita']).toEqual({ tam: 'N5', chico: 'N5S', tarjeta: false })
    expect(medidas('N5')).toEqual({ ancho: 60, alto: 60, filas: 30 })
    expect(medidas('N5S')).toEqual({ ancho: 28, alto: 28, filas: 14 })
    const vistos = new Set<string>()
    for (let i = 0; i < 8; i += 1) {
      const filas = filasDe('necesita', 'N5', i)
      expect(filas.length).toBe(60)
      expect(filas.every(f => f.length === 60)).toBe(true)
      vistos.add(filas.join('/'))
    }
    expect(vistos.size).toBe(8)
    expect(fotogramaEn('necesita', 'N5', 200).join('/')).toBe(filasDe('necesita', 'N5', 1).join('/'))
    expect(fotogramaEn('necesita', 'N5', 1600).join('/')).toBe(fotogramaEn('necesita', 'N5', 0).join('/'))
    expect(especialQueCabe('necesita', 34, 60)).toBe('N5')
    expect(especialEnBanda('necesita', 14, 151)).toBe('N5S')
  })
})

describe('duerme con 8 fotogramas con 5 fps (60x60)', () => {
  test('la hoja tiene 8 fotogramas distintos y se usa en el panel y en las bandas', () => {
    expect(ESPECIAL['duerme']).toEqual({ tam: 'D5', chico: 'D5S', tarjeta: false })
    expect(medidas('D5')).toEqual({ ancho: 60, alto: 60, filas: 30 })
    expect(medidas('D5S')).toEqual({ ancho: 28, alto: 28, filas: 14 })
    const vistos = new Set<string>()
    for (let i = 0; i < 8; i += 1) {
      const filas = filasDe('duerme', 'D5', i)
      expect(filas.length).toBe(60)
      expect(filas.every(f => f.length === 60)).toBe(true)
      vistos.add(filas.join('/'))
    }
    expect(vistos.size).toBe(8)
    expect(fotogramaEn('duerme', 'D5', 200).join('/')).toBe(filasDe('duerme', 'D5', 1).join('/'))
    expect(fotogramaEn('duerme', 'D5', 1600).join('/')).toBe(fotogramaEn('duerme', 'D5', 0).join('/'))
    expect(especialQueCabe('duerme', 34, 60)).toBe('D5')
    expect(especialEnBanda('duerme', 14, 151)).toBe('D5S')
  })
})

describe('guardando con 8 fotogramas con 5 fps (60x60)', () => {
  test('la hoja tiene 8 fotogramas distintos y se usa en el panel y en las bandas', () => {
    expect(ESPECIAL['guardando']).toEqual({ tam: 'G5', chico: 'G5S', tarjeta: false })
    expect(medidas('G5')).toEqual({ ancho: 60, alto: 60, filas: 30 })
    expect(medidas('G5S')).toEqual({ ancho: 28, alto: 28, filas: 14 })
    const vistos = new Set<string>()
    for (let i = 0; i < 8; i += 1) {
      const filas = filasDe('guardando', 'G5', i)
      expect(filas.length).toBe(60)
      expect(filas.every(f => f.length === 60)).toBe(true)
      vistos.add(filas.join('/'))
    }
    expect(vistos.size).toBe(8)
    expect(fotogramaEn('guardando', 'G5', 200).join('/')).toBe(filasDe('guardando', 'G5', 1).join('/'))
    expect(fotogramaEn('guardando', 'G5', 1600).join('/')).toBe(fotogramaEn('guardando', 'G5', 0).join('/'))
    expect(especialQueCabe('guardando', 34, 60)).toBe('G5')
    expect(especialEnBanda('guardando', 14, 151)).toBe('G5S')
  })
})

describe('banda en la app de escritorio', () => {
  test('apagada por defecto; /emi app la muestra y /emi sin-app la quita', async ($, on) => {
    on('ui.render', () => ({ type: 'engine', ref: 1 }) as never) // lo que queda debajo cuando Emi no dibuja
    const sin = await $.ui.mount({ plugin: 'mascota', surface: 'desktop', component: 'AbovePrompt', props: BANDA })
    expect(await sin.find({ type: 'Svg' })).toBeUndefined()
    await sin.unmount()
    await $.command.run({ command: 'emi', args: 'app' })
    const con = await $.ui.mount({ plugin: 'mascota', surface: 'desktop', component: 'AbovePrompt', props: BANDA })
    expect(await con.find({ type: 'Svg' })).toBeDefined()
    await con.unmount()
    await $.command.run({ command: 'emi', args: 'sin-app' })
    const otra = await $.ui.mount({ plugin: 'mascota', surface: 'desktop', component: 'AbovePrompt', props: BANDA })
    expect(await otra.find({ type: 'Svg' })).toBeUndefined()
    await otra.unmount()
  })
})

describe('guardando en Obsidian', () => {
  test('escribir en el vault, el CLI obsidian o un MCP de Obsidian es «guardando»; leerlo no', () => {
    expect(estadoDeHerramienta('Write', { file_path: 'C:/Users/x/OneDrive/Obsidian/SEGUNDO_CEREBRO/nota.md' })).toBe('guardando')
    expect(estadoDeHerramienta('Bash', { command: 'obsidian create name="nota"' })).toBe('guardando')
    expect(estadoDeHerramienta('mcp__obsidian__update_note')).toBe('guardando')
    expect(estadoDeHerramienta('Read', { file_path: 'C:/Obsidian/nota.md' })).toBe('leyendo')
    expect(estadoDeHerramienta('Write', { file_path: 'C:/proyecto/a.ts' })).toBe('escribiendo')
  })
})

describe('5 fps en todos los estados', () => {
  test('cada dibujo dura 200 ms; el ciclo es de 1,6 s con 8 fotogramas y de 0,8 s con 4', () => {
    expect(PASO_MS).toBe(200)
    for (const [estado, tam, n] of [['pensando', 'A5', 8], ['hula', 'H5', 8], ['para', 'L', 4], ['falla', 'M', 4], ['nueva', 'XL', 4]] as const) {
      expect(fotogramas(estado, tam).length).toBe(n)
      for (let i = 0; i < n; i += 1) {
        expect(fotogramaEn(estado, tam, i * PASO_MS).join('/')).toBe(filasDe(estado, tam, i).join('/'))
        expect(fotogramaEn(estado, tam, i * PASO_MS + PASO_MS - 1).join('/')).toBe(filasDe(estado, tam, i).join('/'))
      }
      expect(fotogramaEn(estado, tam, n * PASO_MS).join('/')).toBe(filasDe(estado, tam, 0).join('/'))
    }
  })
})

describe('Emi en el escritorio (programa aparte)', () => {
  test('/emi escritorio y /emi sin-escritorio lo activan y lo apagan, y el estado lo cuenta', async ($, on) => {
    on('process.run', () => ({ value: { exitCode: 0, stdout: '', stderr: '' } }) as never)
    const apagado = await $.command.run({ command: 'emi', args: 'sin-escritorio' } as never)
    expect(JSON.stringify(apagado)).toContain('ya no flota')
    expect(JSON.stringify(await $.command.run({ command: 'emi', args: '' } as never))).toContain('escritorio no')
    const encendido = await $.command.run({ command: 'emi', args: 'escritorio' } as never)
    expect(JSON.stringify(encendido)).toContain('flota sobre el escritorio')
    expect(JSON.stringify(await $.command.run({ command: 'emi', args: '' } as never))).toContain('escritorio sí')
  })
})

describe('pensando con 8 fotogramas con 5 fps (60x60)', () => {
  test('la hoja tiene 8 fotogramas distintos, rectangulares y con colores válidos', () => {
    expect(ESPECIAL['pensando']).toEqual({ tam: 'A5', chico: 'A5S', tarjeta: false })
    expect(medidas('A5')).toEqual({ ancho: 60, alto: 60, filas: 30 })
    const vistos = new Set<string>()
    for (let i = 0; i < 8; i += 1) {
      const filas = filasDe('pensando', 'A5', i)
      expect(filas.length).toBe(60)
      expect(filas.every(f => f.length === 60)).toBe(true)
      expect(filas.join('').split('').every(c => c === '.' || ALFABETO.includes(c))).toBe(true)
      vistos.add(filas.join('/'))
    }
    expect(vistos.size).toBe(8)
    expect(fotogramas('pensando', 'A5').length).toBe(8)
  })

  test('el fotograma sale del tiempo: uno cada 200 ms y vuelve al principio a los 1,6 s', () => {
    const f = (ms: number) => fotogramaEn('pensando', 'A5', ms).join('/')
    expect(f(0)).toBe(filasDe('pensando', 'A5', 0).join('/'))
    expect(f(199)).toBe(f(0))
    expect(f(200)).toBe(filasDe('pensando', 'A5', 1).join('/'))
    expect(f(800)).toBe(filasDe('pensando', 'A5', 4).join('/'))
    expect(f(1400)).toBe(filasDe('pensando', 'A5', 7).join('/'))
    expect(f(1600)).toBe(f(0))
  })

  test('solo se usa si cabe con el texto debajo (60 columnas y 34 filas) y solo para «pensando»', () => {
    expect(especialQueCabe('pensando', 34, 60)).toBe('A5')
    expect(especialQueCabe('pensando', 38, 62)).toBe('A5')
    expect(especialQueCabe('pensando', 33, 62)).toBeNull()
    expect(especialQueCabe('pensando', 38, 59)).toBeNull()
    expect(especialQueCabe('hula', 52, 80)).toBe('H5')
    expect(especialQueCabe('falla', 52, 80)).toBeNull()
    expect(especialQueCabe('nueva', 52, 80)).toBeNull()
  })

  test('las celdas del panel caben en el motor: 60 columnas x 30 filas, menos de 1024 pares de color', () => {
    for (let i = 0; i < 5; i += 1) {
      const c = celdas('A5', filasDe('pensando', 'A5', i))
      expect([c.columnas, c.filas]).toEqual([60, 30])
      const v = leerCeldas(c)
      expect(new Set(v.arriba.map((a, k) => `${a}/${v.abajo[k]}`)).size).toBeLessThanOrEqual(1024)
    }
  })

  test('el fondo es transparente: los píxeles vacíos usan el color por defecto del terminal, sin tarjeta lila', () => {
    const SIN = 0x01000000
    for (let i = 0; i < 5; i += 1) {
      const c = celdas('A5', filasDe('pensando', 'A5', i))
      const bytes = (Uint8Array as unknown as { fromBase64: (s: string) => Uint8Array }).fromBase64(c.cells)
      const w = new Uint32Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / 4)
      let vacias = 0
      let mediasInferiores = 0
      for (let k = 0; k < c.columnas * c.filas; k += 1) {
        const [glifo, fg, bg] = [w[k * 3] ?? 0, w[k * 3 + 1] ?? 0, w[k * 3 + 2] ?? 0]
        expect([fg, bg]).not.toContain(TARJETA)
        if (glifo === 0x20 && bg === SIN) {
          vacias += 1
        }
        if (glifo === 0x2584) {
          mediasInferiores += 1
          expect(bg).toBe(SIN)
          expect(fg).not.toBe(SIN)
        }
        if (glifo === 0x2580) {
          expect(fg).not.toBe(SIN)
        }
      }
      expect(vacias).toBeGreaterThan(c.columnas * c.filas * 0.3)
      expect(mediasInferiores).toBeGreaterThan(0)
    }
  })

  test('en la app de escritorio el panel también usa la animación nueva (SVG 60x60, sin tarjeta) en «pensando»', async ($, on) => {
    on('turn.start', (_$, e) => ({ turnId: e.turnId }))
    await $.turn.start({ text: 'hola', turnId: 't10' })
    const ui = await $.ui.mount({ plugin: 'mascota', surface: 'desktop', component: 'Pane', requestId: 'emi', props: PANEL })
    const svg = JSON.stringify(await ui.find({ type: 'Svg' }))
    expect(svg).toContain('viewBox=\\"0 0 60 60\\"')
    expect(svg).not.toContain('<rect')
    await ui.unmount()
  })

  test('la banda de la app de escritorio también usa la animación nueva en «pensando»', async ($, on) => {
    on('turn.start', (_$, e) => ({ turnId: e.turnId }))
    await $.turn.start({ text: 'hola', turnId: 't11' })
    await $.command.run({ command: 'emi', args: 'app' })
    const ui = await $.ui.mount({ plugin: 'mascota', surface: 'desktop', component: 'AbovePrompt', props: BANDA })
    const svg = JSON.stringify(await ui.find({ type: 'Svg' }))
    expect(svg).toContain('viewBox=\\"0 0 60 60\\"')
    expect(svg).not.toContain('<rect')
    await ui.unmount()
  })

  test('banda del terminal: 60x60 si cabe, 28x28 en las 14 filas de siempre y nada si no hay sitio', () => {
    expect(especialEnBanda('pensando', 40, 140)).toBe('A5')
    expect(especialEnBanda('pensando', 14, 151)).toBe('A5S')
    expect(especialEnBanda('pensando', 13, 151)).toBeNull()
    expect(especialEnBanda('pensando', 14, 40)).toBeNull()
    expect(especialEnBanda('hula', 40, 140)).toBe('H5')
    expect(especialEnBanda('hula', 14, 151)).toBe('H5S')
    expect(especialEnBanda('falla', 40, 140)).toBeNull()
    expect(medidas('A5S')).toEqual({ ancho: 28, alto: 28, filas: 14 })
    for (let i = 0; i < 5; i += 1) {
      const filas = filasDe('pensando', 'A5S', i)
      expect(filas.length).toBe(28)
      expect(filas.every(f => f.length === 28)).toBe(true)
    }
  })

  test('la banda del terminal dibuja la animación de «pensando» con 14 filas', async ($, on) => {
    on('turn.start', (_$, e) => ({ turnId: e.turnId }))
    await $.turn.start({ text: 'hola', turnId: 't12' })
    const ui = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'AbovePrompt', props: { ...BANDA, maxRows: 15, bodyColumns: 151 } })
    expect(await ui.find({ type: 'Raster' })).toBeDefined()
    expect(await ui.find({ type: 'Button', text: 'compacta' })).toBeDefined()
    await ui.unmount()
  })

  test('el panel dibuja 60 x 60 en «pensando» cuando cabe y el sprite de siempre cuando no', async ($, on) => {
    on('turn.start', (_$, e) => ({ turnId: e.turnId }))
    await $.turn.start({ text: 'hola', turnId: 't9' })
    const ancho = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'Pane', requestId: 'emi', props: { ...PANEL, bodyColumns: 62, scroll: { offset: 0, bodyRows: 38 } } })
    expect(await ancho.find({ type: 'Text', text: '60 x 60' })).toBeDefined()
    await ancho.unmount()
    const estrecho = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'Pane', requestId: 'emi', props: { ...PANEL, bodyColumns: 42, scroll: { offset: 0, bodyRows: 38 } } })
    expect(await estrecho.find({ type: 'Text', text: '60 x 60' })).toBeUndefined()
    expect(await estrecho.find({ type: 'Text', text: '40 x 60' })).toBeDefined()
    await estrecho.unmount()
  })
})
