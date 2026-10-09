import shutil

BASE = "C:/Users/Admin0011/.claude/dev-mods/da5e8c78-c252-4d1c-9f43-47016e40a9d5/"
MAIN = BASE + "mascota/"
LAB = BASE + "mascota-lab/"

# 1) Datos y dibujo ya probados en el laboratorio
shutil.copyfile(LAB + "hooks/sprites.ts", MAIN + "hooks/sprites.ts")
shutil.copyfile(LAB + "hooks/dibujo.ts", MAIN + "hooks/dibujo.ts")

# 2) Contrato de estado
t = open(MAIN + "types/index.d.ts", encoding="utf-8").read()
assert "modo" not in t
t = t.replace(
    "export type MascotaAjustes = { tamano: MascotaTamano; sonido: boolean; avisos: boolean }",
    "// `modo`: dónde vive Emi, la banda sobre el cuadro de texto o un panel acoplado junto a la conversación.\nexport type MascotaModo = 'banda' | 'panel'\n\nexport type MascotaAjustes = { tamano: MascotaTamano; sonido: boolean; avisos: boolean; modo: MascotaModo }",
)
t = t.replace("      otras: number\n", "      otras: number\n      panel: boolean\n")
open(MAIN + "types/index.d.ts", "w", encoding="utf-8").write(t)

# 3) register.tsx
p = MAIN + "hooks/register.tsx"
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b, 1)


rep(
    "import type { MascotaAjustes, MascotaAnimo, MascotaEstado, MascotaTamano } from '../types'\nimport { celdas, dibujoSvg, fotograma } from './dibujo'\n",
    "import type { MascotaAjustes, MascotaAnimo, MascotaEstado, MascotaTamano } from '../types'\nimport { celdas, dibujoSvg, elegirTam, fotograma, medidas, planPanel, TEXTO_COLUMNAS } from './dibujo'\nimport type { Tam } from './sprites'\n",
)
rep("const AJUSTES: MascotaAjustes = { tamano: 'normal', sonido: true, avisos: true }", "const AJUSTES: MascotaAjustes = { tamano: 'normal', sonido: true, avisos: true, modo: 'banda' }\nconst PANEL = 'emi'")
rep("const otras = atom({ plugin: 'mascota', key: 'otras' } as const, 0)\n", "const otras = atom({ plugin: 'mascota', key: 'otras' } as const, 0)\nconst panel = atom({ plugin: 'mascota', key: 'panel' } as const, false)\n")
rep("let vueltas = 0\n", "let vueltas = 0\n// Lo último que midió el motor al dibujar la banda: sirve para estimar el hueco de un panel antes de abrirlo.\nlet vista = { columnas: 0, filas: 0, isFullscreen: null as boolean | null }\n")

# helpers antes de «Cómo se ve»
rep(
    "// ---------- Cómo se ve ----------\n",
    """// ---------- El panel acoplado ----------

// El mayor tamaño que pide cada ajuste; el real depende del espacio que dé el motor.
const topeDe = (t: MascotaTamano): Tam => (t === 'grande' ? 'XL' : t === 'mini' ? 'S' : 'L')

async function guardarAjustes($: $, cambio: Partial<MascotaAjustes>) {
  const nuevo = await update($, ajustes, x => ({ ...x, ...cambio }))
  await $.store.set('ajustes', nuevo).catch(() => undefined)
}

// Abre el panel y dice por qué no se pudo ('' si quedó colocado). Si no se coloca, no se deja a medias: se cierra y Emi sigue en la banda.
async function abrirPanel($: $): Promise<string> {
  const a = await read($, ajustes)
  const filasEst = Math.max(10, (vista.filas || 41) - 2)
  const columnasEst = Math.max(40, Math.floor((vista.columnas || 156) * 0.45))
  const plan = planPanel(filasEst, columnasEst, topeDe(a.tamano))
  const m = plan ? medidas(plan.tam) : null
  const columns = m ? m.ancho + (plan?.texto === 'lado' ? TEXTO_COLUMNAS : 0) + 2 : 40
  const rows = m ? m.filas + 4 : 10
  const r = await $.ui.open({ id: PANEL, title: NOMBRE, columns, rows }).catch((error: unknown) => ({ isPlaced: false as const, reason: String(error) }))
  if (!r.isPlaced) {
    await $.ui.close({ id: PANEL }).catch(() => undefined)
    await update($, panel, () => false).catch(() => undefined)
    return r.reason
  }
  await update($, panel, () => true).catch(() => undefined)
  return ''
}

async function aBanda($: $) {
  await guardarAjustes($, { modo: 'banda' })
  await update($, panel, () => false).catch(() => undefined)
  await $.ui.close({ id: PANEL }).catch(() => undefined)
}

// ---------- Cómo se ve ----------
""",
)

# session.start: leer el modo y reabrir el panel
rep(
    "        avisos: typeof guardado.avisos === 'boolean' ? guardado.avisos : a.avisos,\n      }))",
    "        avisos: typeof guardado.avisos === 'boolean' ? guardado.avisos : a.avisos,\n        modo: guardado.modo === 'panel' || guardado.modo === 'banda' ? guardado.modo : a.modo,\n      }))",
)
rep(
    "      description: 'Emi, la mascota: /emi grande | normal | mini | compacta | oculta | sonido | silencio | avisos | sin-avisos | probar',\n      argumentHint: '[grande | normal | mini | compacta | oculta | sonido | silencio | avisos | sin-avisos | probar]',",
    "      description: 'Emi, la mascota: /emi grande | normal | mini | compacta | oculta | panel | banda | sonido | silencio | avisos | sin-avisos | probar',\n      argumentHint: '[grande | normal | mini | compacta | oculta | panel | banda | sonido | silencio | avisos | sin-avisos | probar]',",
)
rep(
    "    await publicar($)\n    await contarOtras($)\n    return hecho\n  })\n\n  on('session.end'",
    """    await publicar($)
    await contarOtras($)
    // Una recarga cierra el panel sin avisar: se parte de «sin panel» y, si ese es el modo guardado, se reabre.
    await update($, panel, () => false).catch(() => undefined)
    if ((await read($, ajustes)).modo === 'panel') {
      const motivo = await abrirPanel($)
      if (motivo) {
        $.ui.toast(`Emi: el panel necesita más sitio (${motivo}). Sigue en la banda; /emi panel lo prueba de nuevo.`, { timeoutMs: 8000 })
      }
    }
    return hecho
  })

  on('session.end'""",
)

# comando: guardar compartido + panel/banda + ayuda
rep(
    "    const guardar = async (cambio: Partial<MascotaAjustes>) => {\n      const nuevo = await update($, ajustes, x => ({ ...x, ...cambio }))\n      await $.store.set('ajustes', nuevo).catch(() => undefined)\n    }\n",
    "    const guardar = (cambio: Partial<MascotaAjustes>) => guardarAjustes($, cambio)\n",
)
rep(
    "    if (orden === 'probar') {",
    """    if (orden === 'panel') {
      const motivo = await abrirPanel($)
      if (motivo) {
        return { text: `No pude abrir el panel acoplado: ${motivo}\\nEmi sigue en la banda.` }
      }
      await guardar({ modo: 'panel' })
      return { text: 'Emi está en el panel acoplado, con el mayor tamaño que cabe. /emi banda la devuelve a la banda. Se queda así en las próximas sesiones.' }
    }
    if (orden === 'banda') {
      await aBanda($)
      return { text: 'Emi vuelve a la banda sobre el cuadro de texto.' }
    }
    if (orden === 'probar') {""",
)
rep(
    "        `${NOMBRE} · tamaño ${a.tamano} · sonido ${a.sonido ? 'sí' : 'no'} · avisos ${a.avisos ? 'sí' : 'no'}${esWindows ? '' : ' (sonido y avisos solo en Windows)'}\\n` +\n        'Uso: /emi grande | normal | mini | compacta | oculta · /emi sonido | silencio · /emi avisos | sin-avisos · /emi probar',",
    "        `${NOMBRE} · tamaño ${a.tamano} · ${a.modo === 'panel' ? 'panel acoplado' : 'banda'} · sonido ${a.sonido ? 'sí' : 'no'} · avisos ${a.avisos ? 'sí' : 'no'}${esWindows ? '' : ' (sonido y avisos solo en Windows)'}\\n` +\n        'Uso: /emi grande | normal | mini | compacta | oculta · /emi panel | banda · /emi sonido | silencio · /emi avisos | sin-avisos · /emi probar',",
)

# 4) la barra y el panel: se reescribe todo desde la marca hasta el final
marca = "  // ---------- La barra de Emi, encima del cuadro de texto ----------\n"
i = s.index(marca)
s = s[:i] + open("nuevo_final_register.txt", encoding="utf-8").read()
open(p, "w", encoding="utf-8").write(s)
print("register.tsx parcheado:", len(s), "caracteres")
