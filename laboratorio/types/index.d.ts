export type LabSeleccion = { tam: 'off' | '13' | '26' | '40' | '52' | '64'; inicio: number }

declare module 'claude-code' {
  interface PluginState {
    'mascota-lab': {
      seleccion: LabSeleccion
      tic: number
      ticProto: number
      ticConv: number
    }
  }
}
