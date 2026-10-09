# Datos finales de Emi: 5 tamaños (13x20, 26x40, 40x60, 52x80, 64x96), todos regenerados desde el PNG original.
# - 26x40 y 13x20: rejilla nativa del dibujo (build6.py). 40x60, 52x80 y 64x96: muestreo directo del PNG (hires.py).
# - Limpieza de píxeles sueltos grises; paleta propia por tamaño; compresión por tramos (RLE) para sprites.ts.
import json
import os
import numpy as np
from PIL import Image, ImageDraw

alta = json.load(open("diag/alta_res/sprites_alta_res.json"))
act = json.load(open("diag/sprites_corregidos.json"))
ALFA = alta["alfabeto"]
assert ALFA == act["alfabeto"], "los alfabetos deben coincidir"
MARCA = "§"
assert MARCA not in ALFA and "." not in ALFA and "/" not in ALFA
NAMES = ["nueva", "pensando", "responde", "leyendo", "escribiendo", "necesita", "falla", "para", "terminado", "baile", "hula", "duerme"]
TAMS = {
    "S": (13, 20, act["paleta"], lambda n: act["sprites"][n]["X"]),
    "N": (26, 40, act["paleta"], lambda n: act["sprites"][n]["L"]),
    "M": (40, 60, alta["paletas"]["40x60"], lambda n: alta["sprites"][n]["40x60"]),
    "L": (52, 80, alta["paletas"]["52x80"], lambda n: alta["sprites"][n]["52x80"]),
    "XL": (64, 96, alta["paletas"]["64x96"], lambda n: alta["sprites"][n]["64x96"]),
}
CUENTA = "0123456789abcdefghijklmnopqrstuvwxyz"
informe = open("diag/informe_datos_finales.txt", "w", encoding="utf-8")


def P(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    informe.write(s + "\n")


def rgb_de(h):
    return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def limpiar(filas, paleta):
    """Quita píxeles opacos sin ningún vecino opaco (8 vecinos) y de color gris (poca saturación): restos del antialiasing."""
    h, w = len(filas), len(filas[0])
    op = np.array([[c != "." for c in r] for r in filas])
    pad = np.pad(op, 1)
    vec = sum(pad[1 + dy:1 + dy + h, 1 + dx:1 + dx + w].astype(int) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0))
    quitados = 0
    out = []
    for y, r in enumerate(filas):
        fila = list(r)
        for x, c in enumerate(fila):
            if c != "." and vec[y, x] == 0:
                rgb = rgb_de(paleta[ALFA.index(c)])
                if max(rgb) - min(rgb) < 45:
                    fila[x] = "."
                    quitados += 1
        out.append("".join(fila))
    return out, quitados


def rle(fila):
    out = []
    i = 0
    while i < len(fila):
        j = i
        while j < len(fila) and fila[j] == fila[i] and j - i < 35:
            j += 1
        n = j - i
        out.append(MARCA + CUENTA[n] + fila[i] if n >= 4 else fila[i] * n)
        i = j
    return "".join(out)


def unrle(texto):
    out = []
    i = 0
    while i < len(texto):
        if texto[i] == MARCA:
            out.append(texto[i + 2] * CUENTA.index(texto[i + 1]))
            i += 3
        else:
            out.append(texto[i])
            i += 1
    return "".join(out)


datos = {}
total_quitados = 0
for tam, (w, h, pal, fuente) in TAMS.items():
    est = {}
    for n in NAMES:
        frames = []
        for f in fuente(n):
            assert len(f) == h and all(len(r) == w for r in f), (tam, n, len(f), len(f[0]))
            f2, q = limpiar(f, pal)
            total_quitados += q
            frames.append(f2)
        est[n] = frames
    datos[tam] = {"ancho": w, "alto": h, "paleta": pal, "estados": est}
P(f"píxeles grises sueltos eliminados: {total_quitados}")

# ---- TypeScript ----
o = []
o.append("// Generado desde «animacion de Emilia pixel de estados.png»: 12 estados x 4 fotogramas x 5 tamaños (scripts en Downloads\\diagnostico-emi\\scripts).")
o.append("// S 13x20 y N 26x40 usan la rejilla nativa del dibujo (4,75 px del PNG); M 40x60, L 52x80 y XL 64x96 muestrean el PNG directamente.")
o.append("// Cada fotograma son filas separadas por «/»; cada carácter es un color de la paleta del tamaño (orden de ALFABETO) y «.» es transparente.")
o.append("// Para ahorrar espacio, un tramo de 4 o más píxeles iguales se escribe «§» + longitud (0-9, a-z) + color.")
o.append("export const ALFABETO = " + json.dumps(ALFA))
o.append("export const MARCA = '" + MARCA + "'")
o.append("export type Tam = 'S' | 'N' | 'M' | 'L' | 'XL'")
o.append("export type Hoja = { ancho: number; alto: number; paleta: readonly string[]; estados: Record<string, readonly string[]> }")
o.append("export const TAMANOS: Record<Tam, Hoja> = {")
for tam, d in datos.items():
    o.append(f"  {tam}: {{")
    o.append(f"    ancho: {d['ancho']},")
    o.append(f"    alto: {d['alto']},")
    o.append("    paleta: " + json.dumps(d["paleta"]) + ",")
    o.append("    estados: {")
    for n in NAMES:
        fr = ["/".join(rle(r) for r in f) for f in d["estados"][n]]
        o.append(f"      {n}: {json.dumps(fr, ensure_ascii=False)},")
    o.append("    },")
    o.append("  },")
o.append("}")
ruta = r"C:/Users/Admin0011/Proyectos/mods-claude/emilia-mascota/laboratorio/hooks/sprites_nuevo.ts"
open(ruta, "w", encoding="utf-8").write("\n".join(o) + "\n")
P(f"sprites_nuevo.ts: {os.path.getsize(ruta):,} bytes (sin comprimir serían ~{sum(len(f) for d in datos.values() for e in d['estados'].values() for f in ['/'.join(r) for fr in e for r in [fr]]):,})")

# ---- ida y vuelta: leer el .ts escrito y comprobar que es idéntico ----
import re
ts = open(ruta, encoding="utf-8").read()
mal = 0
cuenta = 0
for tam, d in datos.items():
    bloque = re.search(rf"  {tam}: \{{\n(.*?)\n  \}},\n", ts, re.S).group(1)
    for n in NAMES:
        m = re.search(rf"      {n}: (\[.*?\]),\n", bloque)
        lista = json.loads(m.group(1))
        for i, texto in enumerate(lista):
            filas = [unrle(r) for r in texto.split("/")]
            cuenta += 1
            if filas != d["estados"][n][i]:
                mal += 1
P(f"ida y vuelta (TS -> filas): {cuenta} fotogramas comparados, {mal} diferencias")

# ---- comparativa visual de todos los tamaños, desde los datos ya codificados ----
def decod(filas, pal):
    h, w = len(filas), len(filas[0])
    R = np.zeros((h, w, 3), np.uint8)
    A = np.zeros((h, w), bool)
    for y, r in enumerate(filas):
        for x, c in enumerate(r):
            if c != ".":
                R[y, x] = rgb_de(pal[ALFA.index(c)])
                A[y, x] = True
    return R, A


def pintar(R, A, esc):
    img = np.zeros((*A.shape, 3), np.uint8) + np.array([245, 230, 253], np.uint8)
    img[A] = R[A]
    return Image.fromarray(img).resize((A.shape[1] * esc, A.shape[0] * esc), Image.NEAREST)


os.makedirs("diag/final_mod", exist_ok=True)
for n in NAMES:
    for f in (0, 2):
        ims = []
        for tam, d in datos.items():
            R, A = decod(d["estados"][n][f], d["paleta"])
            ims.append((f"{tam} {d['ancho']}x{d['alto']}", pintar(R, A, 8 if tam == "S" else 6 if tam == "N" else 4 if tam == "M" else 3 if tam == "L" else 3)))
        alto = 440
        esc = [(t, im.resize((max(1, int(im.size[0] * alto / im.size[1])), alto), Image.NEAREST)) for t, im in ims]
        W = sum(e.size[0] for _, e in esc) + 10 * (len(esc) + 1)
        sh = Image.new("RGB", (W, alto + 40), (30, 30, 36))
        dr = ImageDraw.Draw(sh)
        x = 10
        for t, e in esc:
            sh.paste(e, (x, 30))
            dr.text((x, 8), t, fill=(255, 255, 255))
            x += e.size[0] + 10
        sh.save(f"diag/final_mod/tamanos_{n}_{f}.png")
informe.close()
print("ok")
