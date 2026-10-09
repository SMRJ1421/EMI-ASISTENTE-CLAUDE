import { expect, test } from 'claude-code/testing'

import { FRASES } from '../hooks/estados'

const BANDA = { hasSurvey: false, isWorking: false, maxRows: 40, bodyColumns: 140, scroll: { offset: 0, bodyRows: 40 }, view: {} }
const cualquiera = (frases: readonly string[]) => new RegExp(frases.map(f => f.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'))

test('CARACTERIZACIÓN del mod actual: una denegación de un hook se muestra como fallo', async ($, on) => {
  on('tool.call', () => ({ deny: 'bloqueada por otro plugin' }))
  await $.tool.call({ tool: 'Bash', command: 'ls' })
  const ui = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'AbovePrompt', props: BANDA })
  expect(await ui.find({ type: 'Text', text: cualquiera(FRASES.falla) })).toBeDefined()
  await ui.unmount()
})

test('CARACTERIZACIÓN del mod actual: un rechazo del usuario (isError) se muestra como fallo', async ($, on) => {
  on('tool.call', () => ({ result: "The user doesn't want to proceed with this tool use.", isError: true }) as never)
  await $.tool.call({ tool: 'Bash', command: 'rm x' })
  const ui = await $.ui.mount({ plugin: 'mascota', surface: 'terminal', component: 'AbovePrompt', props: BANDA })
  expect(await ui.find({ type: 'Text', text: cualquiera(FRASES.falla) })).toBeDefined()
  await ui.unmount()
})
