import type { Register } from 'claude-code'

// Dibuja un Raster de bodyColumns x maxRows celdas con un patrón de muchos colores distintos.
export const register: Register = on => {
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.surface !== 'terminal') {
      return next(e)
    }
    const { Raster } = $.ui.resolve(e)
    const columns = e.props.bodyColumns
    const rows = e.props.maxRows
    const palabras = new Uint32Array(columns * rows * 3)
    for (let y = 0; y < rows; y += 1) {
      for (let x = 0; x < columns; x += 1) {
        const k = (y * columns + x) * 3
        palabras[k] = 0x2580
        palabras[k + 1] = ((x * 7 + y * 13) * 4099) & 0xffffff
        palabras[k + 2] = ((x * 11 + y * 5) * 2999) & 0xffffff
      }
    }
    const cells = (new Uint8Array(palabras.buffer) as Uint8Array & { toBase64: () => string }).toBase64()
    return <Raster key="prueba" columns={columns} rows={rows} cells={cells} />
  })
}
