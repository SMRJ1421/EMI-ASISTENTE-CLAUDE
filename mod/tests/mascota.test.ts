import { describe, expect, test } from 'claude-code/testing'

import { esFalloReal, esRechazo, RECHAZO } from '../hooks/deteccion'
import { celdas, colorDe, descomprimir, dibujoSvg, elegirTam, fotograma, fotogramas, indice, leerCeldas, medidas, ORDEN, planPanel, TARJETA } from '../hooks/dibujo'
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

  test('el fotograma avanza con el tic, más despacio en los estados tranquilos', () => {
    expect(indice('escribiendo', 0, 4)).toBe(0)
    expect(indice('escribiendo', 1, 4)).toBe(1)
    expect(indice('duerme', 1, 4)).toBe(0)
    expect(indice('duerme', 2, 4)).toBe(1)
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
