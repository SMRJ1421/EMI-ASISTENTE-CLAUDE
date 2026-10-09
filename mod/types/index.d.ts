export type MascotaEstado =
  | 'nueva'
  | 'pensando'
  | 'responde'
  | 'leyendo'
  | 'escribiendo'
  | 'necesita'
  | 'falla'
  | 'para'
  | 'terminado'
  | 'baile'
  | 'hula'
  | 'duerme'

// Qué hace Emi ahora: `desde` es cuándo empezó, `hasta` cuándo vuelve a su sitio (0 = sin plazo).
export type MascotaAnimo = { estado: MascotaEstado; desde: number; hasta: number; detalle: string }

export type MascotaTamano = 'grande' | 'normal' | 'mini' | 'compacta' | 'oculta'

// `modo`: dónde vive Emi, la banda sobre el cuadro de texto o un panel acoplado junto a la conversación.
export type MascotaModo = 'banda' | 'panel'

export type MascotaAjustes = { tamano: MascotaTamano; sonido: boolean; avisos: boolean; modo: MascotaModo }

declare module 'claude-code' {
  interface PluginState {
    mascota: {
      animo: MascotaAnimo
      tic: number
      ajustes: MascotaAjustes
      otras: number
      panel: boolean
    }
  }
}
