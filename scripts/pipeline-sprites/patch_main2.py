BASE = "C:/Users/Admin0011/Proyectos/mods-claude/emilia-mascota/mod/hooks/"

# ---------- deteccion.ts (nuevo): qué cuenta como fallo real ----------
open(BASE + "deteccion.ts", "w", encoding="utf-8").write('''// Qué cuenta como un fallo de verdad. Técnica vista en dgokcin/claude-pokemon-mod (sin licencia: solo la idea, reimplementada aquí):
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
''')

# ---------- estados.ts: ExitPlanMode ----------
p = BASE + "estados.ts"
s = open(p, encoding="utf-8").read()
a = "  if (tool === 'AskUserQuestion') {\n    return 'necesita'\n  }"
assert a in s
s = s.replace(a, "  if (tool === 'AskUserQuestion' || tool === 'ExitPlanMode') {\n    return 'necesita'\n  }", 1)
b = "  if (tool === 'AskUserQuestion') {\n    return 'tiene una pregunta para ti'\n  }"
assert b in s
s = s.replace(b, "  if (tool === 'AskUserQuestion') {\n    return 'tiene una pregunta para ti'\n  }\n  if (tool === 'ExitPlanMode') {\n    return 'te pide aprobar el plan'\n  }", 1)
open(p, "w", encoding="utf-8").write(s)

# ---------- dibujo.ts: celdas con espacio cuando las dos mitades son iguales ----------
p = BASE + "dibujo.ts"
s = open(p, encoding="utf-8").read()
i = s.index("const color = (tam: Tam, c: string) => {")
j = s.index("export type Dibujo = ")
nuevo = '''const color = (tam: Tam, c: string) => {
  const i = ALFABETO.indexOf(c)
  const hex = i >= 0 ? TAMANOS[tam].paleta[i] : undefined
  return hex ? parseInt(hex.slice(1), 16) : TARJETA
}

export const colorDe = (tam: Tam, c: string) => color(tam, c)

const SIN_COLOR = 0x01000000

export type Celdas = { columnas: number; filas: number; cells: string; glifos: number }

// Para el terminal: dos píxeles por celda sobre la tarjeta. Si las dos mitades tienen el mismo color no hace falta el glifo «▀»:
// basta un espacio con ese color de fondo (técnica vista en dgokcin/claude-pokemon-mod, reimplementada aquí). La imagen es idéntica.
export function celdas(tam: Tam, filas: readonly string[]): Celdas {
  return recordar(`c:${tam}:${filas.join('/')}`, () => {
    const ancho = filas[0]?.length ?? 0
    const pares = Math.ceil(filas.length / 2)
    const palabras = new Uint32Array(ancho * pares * 3)
    let k = 0
    let glifos = 0
    for (let r = 0; r < pares; r += 1) {
      const arriba = filas[r * 2] ?? ''
      const abajo = filas[r * 2 + 1] ?? ''
      for (let x = 0; x < ancho; x += 1) {
        const a = arriba[x] ?? '.'
        const b = abajo[x] ?? '.'
        const ca = a === '.' ? TARJETA : color(tam, a)
        const cb = b === '.' ? TARJETA : color(tam, b)
        if (ca === cb) {
          palabras[k] = 0x20
          palabras[k + 1] = SIN_COLOR
          palabras[k + 2] = cb
        } else {
          palabras[k] = 0x2580
          palabras[k + 1] = ca
          palabras[k + 2] = cb
          glifos += 1
        }
        k += 3
      }
    }
    return { columnas: ancho, filas: pares, cells: (new Uint8Array(palabras.buffer) as Uint8Array & { toBase64: () => string }).toBase64(), glifos }
  })
}

// Lee las celdas de vuelta (colores de arriba y de abajo de cada celda): sirve para comprobar que no se pierde nada.
export function leerCeldas(c: { columnas: number; filas: number; cells: string }): { arriba: number[]; abajo: number[] } {
  const conMetodo = (Uint8Array as unknown as { fromBase64?: (s: string) => Uint8Array }).fromBase64
  const bytes: Uint8Array = conMetodo ? conMetodo(c.cells) : Uint8Array.from(atob(c.cells), ch => ch.charCodeAt(0))
  const palabras = new Uint32Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / 4)
  const arriba: number[] = []
  const abajo: number[] = []
  for (let i = 0; i < c.columnas * c.filas; i += 1) {
    const glifo = palabras[i * 3] ?? 0
    const fg = palabras[i * 3 + 1] ?? 0
    const bg = palabras[i * 3 + 2] ?? 0
    arriba.push(glifo === 0x20 ? bg : fg)
    abajo.push(bg)
  }
  return { arriba, abajo }
}

'''
s = s[:i] + nuevo + s[j:]
open(p, "w", encoding="utf-8").write(s)

# ---------- register.tsx ----------
p = BASE + "register.tsx"
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b, 1)


rep("import { celdas, dibujoSvg, elegirTam, fotograma, medidas, planPanel, TEXTO_COLUMNAS } from './dibujo'\n",
    "import { esFalloReal, esRechazo } from './deteccion'\nimport { celdas, dibujoSvg, elegirTam, fotograma, medidas, planPanel, TEXTO_COLUMNAS } from './dibujo'\n")
rep("let vueltas = 0\n", "let vueltas = 0\n// Herramientas que el permiso denegó (por id de llamada) y si el turno se interrumpió: ni una cosa ni la otra es un fallo.\nconst denegados = new Set<string>()\nlet abortado = false\n")
rep("    trabajando = true\n    inicioTurno = Date.now()\n", "    trabajando = true\n    abortado = false\n    inicioTurno = Date.now()\n")
old = """    const r = await next(e)
    if (e.agentId === undefined && (r.deny !== undefined || r.isError)) {
      await fijar($, 'falla', e.tool)
    }
    return r
  }).catch(($, e, next) => next(e))
"""
new = """    const r = await next(e)
    const denegado = e.tool_use_id !== undefined && denegados.delete(e.tool_use_id)
    const resultado = { isError: r.isError, deny: r.deny, text: r.text }
    const contexto = { denegadoPorCheck: denegado, turnoAbortado: abortado }
    if (e.agentId === undefined) {
      if (esFalloReal(resultado, contexto)) {
        await fijar($, 'falla', e.tool)
      } else if (esRechazo(resultado, contexto)) {
        // Un permiso rechazado, una herramienta denegada o una interrupción no son un fallo: Claude sigue pensando.
        await fijar($, 'pensando')
      }
    }
    return r
  }).catch(($, e, next) => next(e))

  // Las denegaciones del permiso se anotan aquí para no confundirlas luego con un fallo de la herramienta.
  on('tool.check', async ($, e, next) => {
    const r = await next(e)
    if (r.decision === 'deny' && e.tool_use_id !== undefined && e.agentId === undefined) {
      if (denegados.size > 200) {
        denegados.clear()
      }
      denegados.add(e.tool_use_id)
    }
    return r
  }).catch(($, e, next) => next(e))
"""
rep(old, new)
rep("    if (e.agentId === undefined) {\n      trabajando = false\n      const duro = Date.now() - inicioTurno\n", "    if (e.agentId === undefined) {\n      trabajando = false\n      abortado = e.reason === 'aborted'\n      const duro = Date.now() - inicioTurno\n")
open(p, "w", encoding="utf-8").write(s)
print("parche aplicado")
