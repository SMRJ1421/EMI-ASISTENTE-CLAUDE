import { CONV } from './conversacion'
import { descomprimir, TARJETA } from './dibujo'
import { ESCR } from './escribiendo'
import { HULA } from './hula'
import { LEER } from './leyendo'
import { NECE } from './necesita'
import { DUER } from './duerme'
import { GUAR } from './guardando'
import { PENS } from './pensando'
import { RESP } from './responde'
import { TERM } from './terminado'

// PROTOTIPOS de estados con más fotogramas que el mod actual (datos generados en conversacion.ts y pensando.ts). Funciones puras, sin `$`.

export type VarianteConv = { ancho: number; alto: number; paleta: readonly string[]; fotogramas: readonly string[] }

// Estado del mod -> variantes. «nueva» tiene 8 fotogramas (8 fps); «pensando» tiene 5 (5 fps); «hula», 5 (4 fps).
export const ANIMACIONES: Record<string, { variantes: Record<string, VarianteConv>; fps: number }> = {
  nueva: { variantes: CONV, fps: 8 },
  pensando: { variantes: PENS, fps: 5 },
  hula: { variantes: HULA, fps: 4 },
  escribiendo: { variantes: ESCR, fps: 5 },
  terminado: { variantes: TERM, fps: 5 },
  responde: { variantes: RESP, fps: 5 },
  leyendo: { variantes: LEER, fps: 8 },
  necesita: { variantes: NECE, fps: 8 },
  duerme: { variantes: DUER, fps: 8 },
  guardando: { variantes: GUAR, fps: 8 },
}
export const VARIANTES_CONV = Object.keys(CONV)
export const FOTOGRAMAS_CONV = 8

const SIN_COLOR = 0x01000000
const memoria = new Map<string, ReturnType<typeof construir>>()

export function filasConv(nombre: string, i: number, estado = 'nueva'): string[] {
  const v = ANIMACIONES[estado]?.variantes[nombre]
  const lista = v?.fotogramas ?? []
  return (lista[((i % lista.length) + lista.length) % lista.length] ?? '').split('/').map(descomprimir)
}

const colorDe = (v: VarianteConv, c: string, alfabeto: string) => {
  const hex = v.paleta[alfabeto.indexOf(c)]
  return hex ? parseInt(hex.slice(1), 16) : TARJETA
}

const ALFABETO = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!#$%&*+,-:;<=>?@^_~()[]{}|'

function construir(v: VarianteConv, filas: readonly string[]) {
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
      const ca = a === '.' ? TARJETA : colorDe(v, a, ALFABETO)
      const cb = b === '.' ? TARJETA : colorDe(v, b, ALFABETO)
      // Mismo color arriba y abajo: un espacio con fondo, sin glifo (la técnica ya probada en celdas2).
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
}

export function celdasConv(nombre: string, i: number, estado = 'nueva') {
  const v = ANIMACIONES[estado]?.variantes[nombre]
  if (!v) {
    return null
  }
  const clave = `${estado}:${nombre}:${i % v.fotogramas.length}`
  const hecho = memoria.get(clave)
  if (hecho) {
    return hecho
  }
  const nuevo = construir(v, filasConv(nombre, i, estado))
  memoria.set(clave, nuevo)
  return nuevo
}

// El fotograma sale del tiempo transcurrido y de los fotogramas por segundo (como animacion.ts), no de contar redibujos.
export function indiceConv(ms: number, fps: number, cuantos = FOTOGRAMAS_CONV): number {
  return cuantos <= 1 ? 0 : Math.floor((Math.max(0, ms) * fps) / 1000) % cuantos
}
