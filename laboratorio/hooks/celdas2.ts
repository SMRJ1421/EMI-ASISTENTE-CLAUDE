import { colorDe, TARJETA } from './dibujo'
import type { Tam } from './sprites'

// PROTOTIPO (técnica vista en dgokcin/claude-pokemon-mod y TeXmeijin/claude-code-mascot-statusline, idea reimplementada aquí):
// si las dos mitades de una celda tienen el mismo color, no hace falta el glifo «▀»: basta un espacio con ese color de fondo.
// Resultado idéntico a la vista y menos glifos que el terminal tiene que pintar.

const SIN_COLOR = 0x01000000
const memoria = new Map<string, Celdas2>()

export type Celdas2 = { columnas: number; filas: number; cells: string; glifos: number; espacios: number }

export function celdas2(tam: Tam, filas: readonly string[]): Celdas2 {
  const clave = `${tam}:${filas.join('/')}`
  const hecho = memoria.get(clave)
  if (hecho) {
    return hecho
  }
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
      const ca = a === '.' ? TARJETA : colorDe(tam, a)
      const cb = b === '.' ? TARJETA : colorDe(tam, b)
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
  const nuevo = {
    columnas: ancho,
    filas: pares,
    cells: (new Uint8Array(palabras.buffer) as Uint8Array & { toBase64: () => string }).toBase64(),
    glifos,
    espacios: ancho * pares - glifos,
  }
  memoria.set(clave, nuevo)
  return nuevo
}

// Lee las celdas de vuelta: los colores de arriba y de abajo de cada celda (para comprobar que no se pierde nada).
export function leerCeldas(c: { columnas: number; filas: number; cells: string }): { arriba: number[]; abajo: number[] } {
  const bytes: Uint8Array = (Uint8Array as unknown as { fromBase64?: (s: string) => Uint8Array }).fromBase64
    ? (Uint8Array as unknown as { fromBase64: (s: string) => Uint8Array }).fromBase64(c.cells)
    : Uint8Array.from(atob(c.cells), ch => ch.charCodeAt(0))
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
