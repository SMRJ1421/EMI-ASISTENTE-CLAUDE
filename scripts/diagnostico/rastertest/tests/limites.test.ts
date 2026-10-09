import { expect, test } from 'claude-code/testing'

const base = { hasSurvey: false, isWorking: false, scroll: { offset: 0, bodyRows: 1 }, view: {} }

async function intenta($: Parameters<Parameters<typeof test>[1]>[0], columnas: number, filas: number) {
  try {
    const ui = await $.ui.mount({
      plugin: 'rastertest',
      surface: 'terminal',
      component: 'AbovePrompt',
      props: { ...base, bodyColumns: columnas, maxRows: filas },
    })
    await ui.unmount()
    return true
  } catch {
    return false
  }
}

test('el motor acepta los tamaños de Emi y llega al límite documentado', async $ => {
  for (const [c, f] of [[26, 20], [40, 30], [52, 40], [64, 48], [128, 96], [512, 256]] as const) {
    expect([c, f, await intenta($, c, f)]).toEqual([c, f, true])
  }
})

test('rechaza lo que pasa del límite (más de 512 columnas o de 256 filas)', async $ => {
  expect(await intenta($, 513, 10)).toBe(false)
  expect(await intenta($, 10, 257)).toBe(false)
})
