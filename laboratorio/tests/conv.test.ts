import { expect, test } from 'claude-code/testing'

import { CONV } from '../hooks/conversacion'
import { ANIMACIONES, celdasConv, filasConv, FOTOGRAMAS_CONV, indiceConv, VARIANTES_CONV } from '../hooks/convdibujo'
import { leerCeldas } from '../hooks/celdas2'

test('conversación nueva: cada variante tiene 8 fotogramas rectangulares, distintos entre sí y con colores válidos', () => {
  expect(VARIANTES_CONV).toEqual(['nn30', 'nn40', 'nn48', 'nn60', 'nat60'])
  for (const nombre of VARIANTES_CONV) {
    const v = CONV[nombre]!
    expect(v.fotogramas.length).toBe(FOTOGRAMAS_CONV)
    expect(v.alto % 2).toBe(0)
    expect(v.paleta.length).toBeLessThanOrEqual(88)
    const textos = new Set<string>()
    for (let i = 0; i < FOTOGRAMAS_CONV; i += 1) {
      const filas = filasConv(nombre, i)
      expect(filas.length).toBe(v.alto)
      expect(filas.every(f => f.length === v.ancho)).toBe(true)
      expect(filas.join('').split('').every(c => c === '.' || c.charCodeAt(0) < 128)).toBe(true)
      textos.add(filas.join('/'))
    }
    expect(textos.size).toBe(FOTOGRAMAS_CONV)
  }
})

test('conversación nueva: las celdas de 60x60 caben en el panel acoplado (64 columnas, 35 filas con 3 de texto)', () => {
  const x = celdasConv('nat60', 0)!
  expect([x.columnas, x.filas]).toEqual([60, 30])
  expect(x.columnas).toBeLessThanOrEqual(64)
  expect(x.filas + 3).toBeLessThanOrEqual(35)
  const v = leerCeldas(x)
  expect(v.arriba.length).toBe(60 * 30)
  expect(x.glifos).toBeLessThan(60 * 30)
})

test('conversación nueva: a 8 fps se recorren los 8 fotogramas en un segundo, uno cada 125 ms', () => {
  expect(indiceConv(0, 8)).toBe(0)
  expect(indiceConv(124, 8)).toBe(0)
  expect(indiceConv(125, 8)).toBe(1)
  expect(indiceConv(875, 8)).toBe(7)
  expect(indiceConv(1000, 8)).toBe(0)
  expect(Array.from({ length: 8 }, (_, i) => indiceConv(i * 125, 8))).toEqual([0, 1, 2, 3, 4, 5, 6, 7])
  expect(indiceConv(500, 4)).toBe(2)
})

import { mock } from 'claude-code/testing'

const PANEL = { title: 'Emi · Conversación nueva', isFocused: false, bodyColumns: 64, placement: 'dock' as const, scroll: { offset: 0, bodyRows: 35 }, view: {} }

test('el panel de «Conversación nueva» avanza un fotograma cada 125 ms a 8 fps y cabe en el Dock (reloj simulado)', async ($, on) => {
  const reloj = mock.clock(on)
  on('ui.open', () => ({ value: { isPlaced: true } }) as never)
  on('ui.close', () => ({ value: undefined }) as never)
  const ui = await $.ui.mount({ plugin: 'mascota-lab', surface: 'terminal', component: 'Pane', requestId: 'emiconv', props: PANEL })
  await $.command.run({ command: 'emiconv', args: 'nat60 8' } as never)
  const vistos: number[] = []
  for (let i = 0; i < 8; i += 1) {
    await reloj.advance(125)
    const t = await ui.find({ type: 'Text', text: 'fotograma' })
    vistos.push(Number(/fotograma (\d)\/8/.exec(JSON.stringify(t))?.[1] ?? Number.NaN))
  }
  expect(new Set(vistos).size).toBe(8)
  expect(JSON.stringify(await ui.find({ type: 'Text', text: 'demasiado pequeño' }))).not.toContain('pequeño')
  await $.command.run({ command: 'emiconv', args: 'off' } as never)
  await ui.unmount()
})

test('pensando: 8 fotogramas distintos en cada variante (nat60 y nat28), rectangulares y que caben en el Dock; a 5 fps, uno cada 200 ms', () => {
  expect(ANIMACIONES['pensando']?.fps).toBe(5)
  for (const nombre of ['nat60', 'nat28']) {
    const v = ANIMACIONES['pensando']!.variantes[nombre]!
    expect(v.fotogramas.length).toBe(8)
    expect(v.paleta.length).toBeLessThanOrEqual(88)
    const textos = new Set<string>()
    for (let i = 0; i < 8; i += 1) {
      const filas = filasConv(nombre, i, 'pensando')
      expect(filas.length).toBe(v.alto)
      expect(filas.every(f => f.length === v.ancho)).toBe(true)
      textos.add(filas.join('/'))
    }
    expect(textos.size).toBe(8)
  }
  const x = celdasConv('nat60', 0, 'pensando')!
  expect(x.columnas).toBeLessThanOrEqual(64)
  expect(x.filas + 3).toBeLessThanOrEqual(35)
  expect(Array.from({ length: 8 }, (_, i) => indiceConv(i * 200, 5, 8))).toEqual([0, 1, 2, 3, 4, 5, 6, 7])
  expect(indiceConv(199, 5, 8)).toBe(0)
  expect(indiceConv(1600, 5, 8)).toBe(0)
})

test('el panel de «pensando» avanza a 5 fps por defecto (reloj simulado)', async ($, on) => {
  const reloj = mock.clock(on)
  on('ui.open', () => ({ value: { isPlaced: true } }) as never)
  on('ui.close', () => ({ value: undefined }) as never)
  const ui = await $.ui.mount({ plugin: 'mascota-lab', surface: 'terminal', component: 'Pane', requestId: 'emiconv', props: PANEL })
  await $.command.run({ command: 'emiconv', args: 'pensando nat60' } as never)
  const vistos: number[] = []
  for (let i = 0; i < 8; i += 1) {
    await reloj.advance(200)
    const t = await ui.find({ type: 'Text', text: 'fotograma' })
    const m = /pensando · nat60 · 5 fps · fotograma (\d)\/8/.exec(JSON.stringify(t))
    vistos.push(Number(m?.[1] ?? Number.NaN))
  }
  expect(new Set(vistos).size).toBe(8)
  await $.command.run({ command: 'emiconv', args: 'off' } as never)
  await ui.unmount()
})
