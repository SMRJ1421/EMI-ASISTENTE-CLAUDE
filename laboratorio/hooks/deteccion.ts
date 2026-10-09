// PROTOTIPO (técnicas vistas en dgokcin/claude-pokemon-mod: «fallo real» sin contar denegaciones ni interrupciones, y avisos de
// «te necesita» por ExitPlanMode / PermissionRequest; ideas reimplementadas aquí).

// Frases con las que Claude Code devuelve un rechazo del usuario o una interrupción: no son un fallo de la herramienta.
export const RECHAZO =
  /(doesn['’]?t want to proceed|does not want to proceed|user (rejected|denied|declined)|was (rejected|denied|blocked)|permission (to use [^ ]+ )?(has been )?denied|interrupted by user|request interrupted|tool use was rejected)/i

export type ResultadoHerramienta = { isError?: boolean; deny?: string; text?: string }
export type ContextoFallo = { denegadoPorCheck: boolean; turnoAbortado: boolean }

// ¿Debe Emi asustarse? Solo si la herramienta falló de verdad: ni denegación de un hook, ni permiso negado, ni interrupción.
export function esFalloReal(r: ResultadoHerramienta, ctx: ContextoFallo): boolean {
  if (r.deny !== undefined) {
    return false
  }
  if (!r.isError) {
    return false
  }
  if (ctx.denegadoPorCheck || ctx.turnoAbortado) {
    return false
  }
  return !RECHAZO.test(r.text ?? '')
}

// Herramientas que piden algo a la persona: responder una pregunta o aprobar un plan.
export const PIDEN_PERSONA = new Set(['AskUserQuestion', 'ExitPlanMode'])

export const pidePersona = (tool: string) => PIDEN_PERSONA.has(tool)

// Escribir en el cuadro de texto despierta a Emi si estaba de guardia o dormida (y reinicia la cuenta de la siesta).
export function despierta(estado: string): boolean {
  return estado === 'duerme' || estado === 'hula'
}
