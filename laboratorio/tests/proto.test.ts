import { expect, mock, test } from 'claude-code/testing'

import { FPS, indiceEn } from '../hooks/animacion'
import { celdas2, leerCeldas } from '../hooks/celdas2'
import { esFalloReal, despierta, pidePersona, RECHAZO } from '../hooks/deteccion'
import { celdas, fotograma, ORDEN } from '../hooks/dibujo'

const ESTADOS = ['nueva', 'pensando', 'responde', 'leyendo', 'escribiendo', 'necesita', 'falla', 'para', 'terminado', 'baile', 'hula', 'duerme']
const PANEL = { title: 'Emi (prototipo)', isFocused: false, bodyColumns: 64, placement: 'dock' as const, scroll: { offset: 0, bodyRows: 35 }, view: {} }

test('celdas2: se ve exactamente igual que la codificación actual, en los 240 fotogramas', () => {
  let glifos = 0
  let total = 0
  for (const t of ORDEN) {
    for (const estado of ESTADOS) {
      for (let i = 0; i < 4; i += 1) {
        const filas = fotograma(estado, t, i)
        const a = celdas(t, filas)
        const b = celdas2(t, filas)
        expect([b.columnas, b.filas]).toEqual([a.columnas, a.filas])
        const va = leerCeldas(a)
        const vb = leerCeldas(b)
        expect(vb.arriba).toEqual(va.arriba)
        expect(vb.abajo).toEqual(va.abajo)
        glifos += b.glifos
        total += b.columnas * b.filas
      }
    }
  }
  // La codificación actual pinta un glifo en cada celda; la nueva solo donde las dos mitades difieren.
  expect(glifos / total).toBeLessThan(0.6)
})

test('animacion: el fotograma sale del tiempo transcurrido y de los fotogramas por segundo', () => {
  expect(FPS.actual.vivo).toBe(4)
  expect(indiceEn('escribiendo', 0, 'actual', 4)).toBe(0)
  expect(indiceEn('escribiendo', 249, 'actual', 4)).toBe(0)
  expect(indiceEn('escribiendo', 250, 'actual', 4)).toBe(1)
  expect(indiceEn('escribiendo', 1000, 'actual', 4)).toBe(0)
  expect(indiceEn('escribiendo', 125, 'fluido', 4)).toBe(1)
  expect(indiceEn('duerme', 499, 'actual', 4)).toBe(0)
  expect(indiceEn('duerme', 500, 'actual', 4)).toBe(1)
  expect(indiceEn('baile', -50, 'fluido', 4)).toBe(0)
})

test('deteccion: solo un fallo real asusta; denegaciones, rechazos e interrupciones no', () => {
  const normal = { denegadoPorCheck: false, turnoAbortado: false }
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

test('deteccion: qué herramientas piden algo a la persona y quién despierta', () => {
  expect(pidePersona('AskUserQuestion')).toBe(true)
  expect(pidePersona('ExitPlanMode')).toBe(true)
  expect(pidePersona('Read')).toBe(false)
  expect(despierta('duerme')).toBe(true)
  expect(despierta('hula')).toBe(true)
  expect(despierta('escribiendo')).toBe(false)
})

test('el panel de prototipo se dibuja en el terminal', async ($, on) => {
  mock.clock(on)
  const ui = await $.ui.mount({ plugin: 'mascota-lab', surface: 'terminal', component: 'Pane', requestId: 'emiproto', props: PANEL })
  expect(await ui.find({ type: 'Text', text: 'prototipo' })).toBeDefined()
  await ui.unmount()
})

function numero(texto: string, patron: RegExp): number {
  return Number(patron.exec(texto)?.[1] ?? Number.NaN)
}

test('blit anima sin repetir el dibujo; el control redibuja en cada tic (reloj simulado, 5 s)', async ($, on) => {
  const reloj = mock.clock(on)
  on('ui.open', () => ({ value: { isPlaced: true } }) as never)
  on('ui.blit', () => ({ value: {} }) as never)
  on('ui.close', () => ({ value: undefined }) as never)

  const medir = async (modo: 'atomo' | 'atomo8' | 'blit' | 'fluido') => {
    const ui = await $.ui.mount({ plugin: 'mascota-lab', surface: 'terminal', component: 'Pane', requestId: 'emiproto', props: PANEL })
    await $.command.run({ command: 'emiproto', args: modo } as never)
    await reloj.advance(5000)
    const r = await $.command.run({ command: 'emiproto', args: '' } as never)
    const texto = JSON.stringify(r)
    await $.command.run({ command: 'emiproto', args: 'off' } as never)
    await ui.unmount()
    return {
      renders: numero(texto, /pasadas de dibujo: (\d+)/),
      blits: numero(texto, /envíos blit: (\d+)/),
      denegados: numero(texto, /denegados: (\d+)/),
    }
  }

  const control = await medir('atomo')
  const blit4 = await medir('blit')
  const blit8 = await medir('fluido')
  const atomo8 = await medir('atomo8')

  // Control: el dibujo se ejecuta una vez por tic de 250 ms (≈ 20 en 5 s) y no hay envíos.
  expect(control.renders).toBeGreaterThanOrEqual(15)
  expect(control.blits).toBe(0)
  // Blit: el dibujo se hace una vez (más la reposición al arrancar) y el resto son envíos de celdas.
  expect(blit4.renders).toBeLessThanOrEqual(4)
  expect(blit4.blits).toBeGreaterThanOrEqual(15)
  expect(blit4.denegados).toBe(0)
  // A 8 fotogramas por segundo caben el doble de envíos sin una sola pasada de dibujo más.
  expect(blit8.renders).toBeLessThanOrEqual(4)
  expect(blit8.blits).toBeGreaterThanOrEqual(blit4.blits * 1.6)
  // Redibujar a 8 fps sin blit: unas 40 pasadas en 5 s y ningún envío (es la alternativa que no depende de $.ui.blit).
  expect(atomo8.renders).toBeGreaterThanOrEqual(35)
  expect(atomo8.blits).toBe(0)
})
