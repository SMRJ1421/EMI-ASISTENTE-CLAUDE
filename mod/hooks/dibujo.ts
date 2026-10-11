import { ANIM, ESPECIAL } from './animaciones'
import type { TamAnim } from './animaciones'
import { ALFABETO, MARCA, TAMANOS } from './sprites'
import type { Hoja, Tam } from './sprites'

// Los cinco tamaños de siempre más las hojas de los estados con animación propia (pensando, hula): solo se eligen a propósito, nunca por espacio.
export type TamX = Tam | TamAnim
const esAnim = (tam: TamX): tam is TamAnim => tam in ANIM
// ¿Esta hoja posa sobre la tarjeta lila? Sí si su arte lleva contorno negro (hula); no si no lo lleva (pensando): deja ver el fondo.
const sobreTarjeta = (tam: TamX) => !esAnim(tam) || Object.values(ESPECIAL).some(e => (e.tam === tam || e.chico === tam) && e.tarjeta)
const hoja = (tam: TamX): Hoja => (esAnim(tam) ? ANIM[tam] : TAMANOS[tam])

// Poses, fotogramas, elección del tamaño según el espacio y conversión a celdas Raster o a SVG: funciones puras, sin `$`.

// El color de la tarjeta donde posa Emi: el mismo lila del PNG, para que el contorno negro se vea también en un terminal oscuro.
export const TARJETA = 0xf5e6fd

// De mayor a menor. S 13x20 (10 filas), N 26x40 (20), M 40x60 (30), L 52x80 (40), XL 64x96 (48).
export const ORDEN: readonly Tam[] = ['XL', 'L', 'M', 'N', 'S']

// Todos los estados avanzan un fotograma por tic (4 fps); ya no hay estados lentos (antes nueva, pensando, leyendo y duerme iban a 2 fps).

const CUENTA = '0123456789abcdefghijklmnopqrstuvwxyz'
const memoria = new Map<string, unknown>()

function recordar<T>(clave: string, crear: () => T): T {
  const hecho = memoria.get(clave)
  if (hecho !== undefined) {
    return hecho as T
  }
  const nuevo = crear()
  memoria.set(clave, nuevo)
  return nuevo
}

// ---------- Datos ----------

export function medidas(tam: TamX) {
  const d = hoja(tam)
  return { ancho: d.ancho, alto: d.alto, filas: d.alto / 2 }
}

// «§» + longitud (0-9, a-z) + color es un tramo de píxeles iguales.
export function descomprimir(texto: string): string {
  let salida = ''
  let i = 0
  while (i < texto.length) {
    if (texto[i] === MARCA) {
      salida += (texto[i + 2] ?? '.').repeat(CUENTA.indexOf(texto[i + 1] ?? '0'))
      i += 3
    } else {
      salida += texto[i] ?? ''
      i += 1
    }
  }
  return salida
}

export function fotogramas(estado: string, tam: TamX): readonly string[] {
  const d = hoja(tam)
  return d.estados[estado] ?? d.estados['hula'] ?? []
}

export function filasDe(estado: string, tam: TamX, indiceFotograma: number): string[] {
  const lista = fotogramas(estado, tam)
  const i = lista.length ? ((indiceFotograma % lista.length) + lista.length) % lista.length : 0
  return recordar(`f:${estado}:${tam}:${i}`, () => (lista[i] ?? '').split('/').map(descomprimir))
}

// Qué fotograma toca en el tic `tic` (uno cada cuarto de segundo).
export function indice(estado: string, tic: number, cuantos: number): number {
  if (cuantos <= 1) {
    return 0
  }
  return tic % cuantos
}

export function fotograma(estado: string, tam: Tam, tic: number): string[] {
  return filasDe(estado, tam, indice(estado, tic, fotogramas(estado, tam).length))
}

// ---------- Qué fotograma toca, y los estados con su propia animación (8 fotogramas, 60x60) ----------

// Todos los estados van a 5 fps (cada dibujo dura 200 ms): el ciclo dura 1,6 s con 8 fotogramas y 0,8 s con 4. El fotograma sale del tiempo.
export const PASO_MS = 200

// El fotograma que toca `ms` milisegundos después de empezar el estado (no cuenta redibujos).
export function fotogramaEn(estado: string, tam: TamX, ms: number): string[] {
  const cuantos = fotogramas(estado, tam).length
  return filasDe(estado, tam, cuantos <= 1 ? 0 : Math.floor(Math.max(0, ms) / PASO_MS) % cuantos)
}

// La hoja especial del estado, si la tiene y cabe en `filas` x `columnas` con el texto debajo (si no, null y se usa el sprite de siempre).
export function especialQueCabe(estado: string, filas: number, columnas: number): TamAnim | null {
  const e = ESPECIAL[estado]
  if (!e) {
    return null
  }
  const m = medidas(e.tam)
  return m.ancho <= columnas && m.filas + TEXTO_FILAS <= filas ? e.tam : null
}

// La hoja especial del estado para la banda del terminal: la de 60x60 si cabe (banda alta) y si no la de 28x28 (14 filas), con el texto al lado.
export function especialEnBanda(estado: string, filas: number, columnas: number): TamAnim | null {
  const e = ESPECIAL[estado]
  if (!e) {
    return null
  }
  return [e.tam, e.chico].find(t => medidas(t).filas <= filas && medidas(t).ancho + TEXTO_COLUMNAS <= columnas) ?? null
}

// ---------- Elegir el tamaño que cabe ----------

// El mayor tamaño, no mayor que `tope`, que cabe en `filas` x `columnas` de terminal; null si ni el menor.
export function elegirTam(filas: number, columnas: number, tope: Tam = 'XL'): Tam | null {
  for (const t of ORDEN.slice(ORDEN.indexOf(tope))) {
    const m = medidas(t)
    if (m.filas <= filas && m.ancho <= columnas) {
      return t
    }
  }
  return null
}

// Filas que ocupan el nombre, la frase, el detalle y los botones cuando van debajo del dibujo, y columnas que pide el texto
// cuando va al lado.
export const TEXTO_FILAS = 4
export const TEXTO_COLUMNAS = 24

export type PlanPanel = { tam: Tam; texto: 'abajo' | 'lado' }

// Qué sprite y dónde va el texto en un panel de `filas` x `columnas`: el mayor sprite posible; a igualdad, con el texto debajo.
export function planPanel(filas: number, columnas: number, tope: Tam = 'XL'): PlanPanel | null {
  for (const t of ORDEN.slice(ORDEN.indexOf(tope))) {
    const m = medidas(t)
    if (m.ancho > columnas) {
      continue
    }
    if (m.filas + TEXTO_FILAS <= filas) {
      return { tam: t, texto: 'abajo' }
    }
    if (m.filas <= filas && m.ancho + TEXTO_COLUMNAS <= columnas) {
      return { tam: t, texto: 'lado' }
    }
  }
  return null
}

// ---------- Pintar ----------

const color = (tam: TamX, c: string) => {
  const i = ALFABETO.indexOf(c)
  const hex = i >= 0 ? hoja(tam).paleta[i] : undefined
  return hex ? parseInt(hex.slice(1), 16) : TARJETA
}

export const colorDe = (tam: TamX, c: string) => color(tam, c)

const SIN_COLOR = 0x01000000

export type Celdas = { columnas: number; filas: number; cells: string; glifos: number }

// Para el terminal: dos píxeles por celda sobre la tarjeta. Si las dos mitades tienen el mismo color no hace falta el glifo «▀»:
// basta un espacio con ese color de fondo (técnica vista en dgokcin/claude-pokemon-mod, reimplementada aquí). La imagen es idéntica.
export function celdas(tam: TamX, filas: readonly string[]): Celdas {
  return recordar(`c:${tam}:${filas.join('/')}`, () => {
    const ancho = filas[0]?.length ?? 0
    const pares = Math.ceil(filas.length / 2)
    const palabras = new Uint32Array(ancho * pares * 3)
    // Los sprites de siempre posan sobre la tarjeta lila (llevan contorno negro); la hoja de «pensando» (sin contorno) deja ver el fondo del terminal.
    const vacio = sobreTarjeta(tam) ? TARJETA : SIN_COLOR
    let k = 0
    let glifos = 0
    for (let r = 0; r < pares; r += 1) {
      const arriba = filas[r * 2] ?? ''
      const abajo = filas[r * 2 + 1] ?? ''
      for (let x = 0; x < ancho; x += 1) {
        const a = arriba[x] ?? '.'
        const b = abajo[x] ?? '.'
        const ca = a === '.' ? vacio : color(tam, a)
        const cb = b === '.' ? vacio : color(tam, b)
        if (ca === cb) {
          palabras[k] = 0x20
          palabras[k + 1] = SIN_COLOR
          palabras[k + 2] = cb
        } else if (ca === SIN_COLOR) {
          // Arriba transparente y abajo con color: medio bloque inferior con el color de abajo, y el fondo del terminal arriba.
          palabras[k] = 0x2584
          palabras[k + 1] = cb
          palabras[k + 2] = SIN_COLOR
          glifos += 1
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

export type Dibujo = { source: string; ancho: number; alto: number }

// Para la app de escritorio: un SVG con la tarjeta y un trazo por color (cada tramo horizontal es un rectángulo de una fila).
export function dibujoSvg(tam: TamX, filas: readonly string[]): Dibujo {
  return recordar(`s:${tam}:${filas.join('/')}`, () => {
    const ancho = filas[0]?.length ?? 0
    const trazos = new Map<string, string>()
    filas.forEach((fila, y) => {
      let x = 0
      while (x < fila.length) {
        const c = fila[x] ?? '.'
        let fin = x
        while (fin < fila.length && fila[fin] === c) {
          fin += 1
        }
        if (c !== '.') {
          trazos.set(c, `${trazos.get(c) ?? ''}M${x} ${y}h${fin - x}v1h-${fin - x}z`)
        }
        x = fin
      }
    })
    const hex = (n: number) => n.toString(16).padStart(6, '0')
    const caminos = [...trazos].map(([c, d]) => `<path fill="#${hex(color(tam, c))}" d="${d}"/>`).join('')
    // Sin tarjeta en la hoja de «pensando» (sin contorno negro): el dibujo queda sobre el fondo del panel.
    const fondo = !sobreTarjeta(tam) ? '' : `<rect width="${ancho}" height="${filas.length}" rx="2" fill="#${hex(TARJETA)}"/>`
    const source = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${ancho} ${filas.length}" shape-rendering="crispEdges">${fondo}${caminos}</svg>`
    return { source, ancho, alto: filas.length }
  })
}
