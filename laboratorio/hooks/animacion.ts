// PROTOTIPO (técnica vista en dgokcin/claude-pokemon-mod, idea reimplementada aquí): el fotograma se elige por el tiempo transcurrido,
// no contando redibujos, y cada perfil fija los fotogramas por segundo. Así el ritmo no depende de cuántas veces se dibuje.

export type Perfil = 'actual' | 'fluido'

// Fotogramas por segundo según el estado: «vivo» (escribir, bailar...) y «calmo» (pensar, leer, dormir...).
export const FPS: Record<Perfil, { vivo: number; calmo: number }> = {
  actual: { vivo: 4, calmo: 2 },
  fluido: { vivo: 8, calmo: 4 },
}

const CALMOS = new Set(['nueva', 'pensando', 'leyendo', 'duerme'])

export function indiceEn(estado: string, ms: number, perfil: Perfil, cuantos: number): number {
  if (cuantos <= 1) {
    return 0
  }
  const fps = CALMOS.has(estado) ? FPS[perfil].calmo : FPS[perfil].vivo
  return Math.floor((Math.max(0, ms) * fps) / 1000) % cuantos
}
