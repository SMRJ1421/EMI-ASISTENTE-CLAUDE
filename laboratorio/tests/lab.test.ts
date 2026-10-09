import { expect, test } from 'claude-code/testing'

import { celdas, descomprimir, dibujoSvg, elegirTam, fotograma, fotogramas, medidas, ORDEN, planPanel } from '../hooks/dibujo'
import { ALFABETO, TAMANOS } from '../hooks/sprites'
import type { Tam } from '../hooks/sprites'

const BANDA = {
  hasSurvey: false,
  isWorking: false,
  maxRows: 15,
  bodyColumns: 151,
  scroll: { offset: 0, bodyRows: 14 },
  view: {},
}
const PANEL = { title: 'Emi (laboratorio)', isFocused: false, bodyColumns: 62, placement: 'dock' as const, scroll: { offset: 0, bodyRows: 38 }, view: {} }
const ESTADOS = ['nueva', 'pensando', 'responde', 'leyendo', 'escribiendo', 'necesita', 'falla', 'para', 'terminado', 'baile', 'hula', 'duerme']

test('los datos: 12 estados x 4 fotogramas x 5 tamaños, rectangulares y con colores válidos', () => {
  for (const t of ORDEN) {
    const d = TAMANOS[t]
    expect(d.alto % 2).toBe(0)
    for (const estado of ESTADOS) {
      const frames = fotogramas(estado, t)
      expect(frames.length).toBe(4)
      for (let i = 0; i < 4; i += 1) {
        const filas = (frames[i] ?? '').split('/').map(descomprimir)
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

test('elegir el tamaño según el espacio', () => {
  expect(elegirTam(15, 151)).toBe('S')       // la banda de 15 filas: solo el mini
  expect(elegirTam(20, 151)).toBe('N')
  expect(elegirTam(30, 151)).toBe('M')
  expect(elegirTam(40, 151)).toBe('L')
  expect(elegirTam(48, 151)).toBe('XL')
  expect(elegirTam(48, 151, 'L')).toBe('L')   // tope
  expect(elegirTam(48, 40)).toBe('M')         // limitado por columnas
  expect(elegirTam(9, 151)).toBeNull()
})

test('plan del panel: el mayor sprite, con el texto debajo o al lado', () => {
  expect(planPanel(38, 62)?.tam).toBe('M')                       // 30 filas + 4 de texto
  expect(planPanel(38, 80)).toEqual({ tam: 'M', texto: 'abajo' })  // 40 filas no caben en 38, ni con el texto al lado
  expect(planPanel(39, 80)).toEqual({ tam: 'M', texto: 'abajo' })
  expect(planPanel(40, 80)).toEqual({ tam: 'L', texto: 'lado' })  // 40 filas justas, texto al lado
  expect(planPanel(44, 62)).toEqual({ tam: 'L', texto: 'abajo' })
  expect(planPanel(52, 80)).toEqual({ tam: 'XL', texto: 'abajo' })
  expect(planPanel(5, 62)).toBeNull()
})

test('celdas y SVG de cada tamaño: dimensiones y límites del motor', () => {
  for (const t of ORDEN) {
    const m = medidas(t)
    const filas = fotograma('escribiendo', t, 0)
    const c = celdas(t, filas)
    expect([c.columnas, c.filas]).toEqual([m.ancho, m.filas])
    expect(c.columnas).toBeLessThanOrEqual(512)
    expect(c.filas).toBeLessThanOrEqual(256)
    const d = dibujoSvg(t, filas)
    expect(d.source.length).toBeLessThan(131072)
  }
})

test('la banda se dibuja en terminal con cualquier espacio (el laboratorio solo dibuja si se pide)', async ($, on) => {
  on('ui.render', () => ({ type: 'engine', ref: 1 }) as never)
  const ui = await $.ui.mount({ plugin: 'mascota-lab', surface: 'terminal', component: 'AbovePrompt', props: BANDA })
  expect(await ui.find({ type: 'Text', text: 'Laboratorio' })).toBeUndefined()
  await ui.unmount()
})

test('cada tamaño de la banda de prueba dice si cabe', async $ => {
  for (const [n, t] of [['13', 'S'], ['26', 'N'], ['40', 'M'], ['52', 'L'], ['64', 'XL']] as const satisfies readonly (readonly [string, Tam])[]) {
    await $.command.run({ command: 'emilab', args: n } as never)
    const ui = await $.ui.mount({ plugin: 'mascota-lab', surface: 'terminal', component: 'AbovePrompt', props: { ...BANDA, maxRows: 60 } })
    expect(await ui.find({ type: 'Text', text: `Laboratorio · ${n}` })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: 'Cabe entero' })).toBeDefined()
    await ui.unmount()
    const justo = await $.ui.mount({ plugin: 'mascota-lab', surface: 'terminal', component: 'AbovePrompt', props: { ...BANDA, maxRows: medidas(t).filas - 1 } })
    expect(await justo.find({ type: 'Text', text: 'NO cabe entero' })).toBeDefined()
    await justo.unmount()
  }
  await $.command.run({ command: 'emilab', args: 'off' } as never)
})

test('el panel de prueba se dibuja con el espacio que le da el motor', async $ => {
  for (const [filas, columnas] of [[38, 62], [38, 80], [52, 80], [14, 62]] as const) {
    const ui = await $.ui.mount({
      plugin: 'mascota-lab',
      surface: 'terminal',
      component: 'Pane',
      requestId: 'emilab',
      props: { ...PANEL, bodyColumns: columnas, scroll: { offset: 0, bodyRows: filas } },
    })
    expect(await ui.find({ type: 'Text', text: 'dock' })).toBeDefined()
    await ui.unmount()
  }
})
