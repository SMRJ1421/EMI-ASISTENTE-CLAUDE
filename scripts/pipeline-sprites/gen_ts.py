# Escribe hooks/sprites.ts a partir de sprites_corregidos.json (tamaños L nativo y X mitad).
import json
import os

d = json.load(open("diag/sprites_corregidos.json"))
mod = r"C:/Users/Admin0011/.claude/dev-mods/da5e8c78-c252-4d1c-9f43-47016e40a9d5/mascota/hooks/sprites.ts"
o = []
o.append("// Generado a partir de «animacion de Emilia pixel de estados.png»: 12 estados, 4 fotogramas cada uno.")
o.append("// L es la resolución nativa del dibujo (rejilla real de 4,75 px del original, muestreada sin mezclar colores) y X la mitad por vecino más cercano.")
o.append("// Cada fotograma son filas de píxeles separadas por «/»; cada carácter es un color de PALETA (en el orden de ALFABETO)")
o.append("// y «.» es transparente.")
o.append("export const ALFABETO = " + json.dumps(d["alfabeto"]))
o.append("export const PALETA: readonly string[] = " + json.dumps(d["paleta"]))
o.append("export type Tam = 'L' | 'X'")
o.append("export type Hoja = Record<Tam, readonly string[]>")
o.append("export const SPRITES: Record<string, Hoja> = {")
for n, hs in d["sprites"].items():
    o.append(f"  {n}: {{")
    for t in ("L", "X"):
        o.append(f"    {t}: {json.dumps(['/'.join(f) for f in hs[t]])},")
    o.append("  },")
o.append("}")
open(mod, "w", encoding="utf-8").write("\n".join(o) + "\n")
print(os.path.getsize(mod), "bytes;", d["tam"])
