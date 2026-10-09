// Qué cuenta como un fallo de verdad. Técnica vista en dgokcin/claude-pokemon-mod (sin licencia: solo la idea, reimplementada aquí):
// una herramienta denegada, un permiso rechazado o una interrupción voluntaria no son un fallo y Emi no debe asustarse.

// Frases con las que Claude Code devuelve un rechazo del usuario o una interrupción.
export const RECHAZO =
  /(doesn['’]?t want to proceed|does not want to proceed|user (rejected|denied|declined)|was (rejected|denied|blocked)|permission (to use [^ ]+ )?(has been )?denied|interrupted by user|request interrupted|tool use was rejected)/i

export type ResultadoHerramienta = { isError?: boolean; deny?: string; text?: string }
export type ContextoFallo = { denegadoPorCheck: boolean; turnoAbortado: boolean }

// ¿Debe Emi asustarse? Solo si la herramienta falló de verdad: ni denegación de un hook, ni permiso denegado, ni interrupción.
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

// Un rechazo no es un fallo, pero tampoco un éxito: Claude va a seguir pensando qué hacer.
export function esRechazo(r: ResultadoHerramienta, ctx: ContextoFallo): boolean {
  return (r.deny !== undefined || Boolean(r.isError)) && !esFalloReal(r, ctx)
}
