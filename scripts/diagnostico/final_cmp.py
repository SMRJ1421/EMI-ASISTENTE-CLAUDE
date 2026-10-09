# Comparación final desde los sprites.ts reales: el anterior (copia de seguridad) frente al corregido, en cada tamaño.
import json
import re
import numpy as np
from PIL import Image, ImageDraw

NUEVO = r"C:\Users\Admin0011\.claude\dev-mods\da5e8c78-c252-4d1c-9f43-47016e40a9d5\mascota\hooks\sprites.ts"
VIEJO = r"C:\Users\Admin0011\.claude\dev-mods-backup\mascota-2026-10-08-antes-de-fidelidad\hooks\sprites.ts"
NAMES = ["nueva", "pensando", "responde", "leyendo", "escribiendo", "necesita", "falla", "para", "terminado", "baile", "hula", "duerme"]


def leer(ruta):
    ts = open(ruta, encoding="utf-8").read()
    alf = re.search(r"export const ALFABETO = (['\"])(.*?)\1\n", ts).group(2)
    pal = json.loads(re.search(r"export const PALETA: readonly string\[\] = (\[.*?\])\n", ts).group(1))
    pal = [[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in pal]
    sp = {}
    for n in NAMES:
        bloque = re.search(rf"  {n}: \{{(.*?)\n  \}},", ts, re.S).group(1)
        sp[n] = {}
        for t in re.finditer(r"    ([LSX]): (\[.*?\]),", bloque):
            sp[n][t.group(1)] = [f.split("/") for f in json.loads(t.group(2))]
    return alf, pal, sp


def dec(filas, alf, pal):
    h, w = len(filas), len(filas[0])
    R = np.zeros((h, w, 3), np.uint8)
    A = np.zeros((h, w), bool)
    for y, r in enumerate(filas):
        for x, c in enumerate(r):
            if c != ".":
                R[y, x] = pal[alf.index(c)]
                A[y, x] = True
    return R, A


def terminal(R, A, celda=(8, 16)):
    cw, ch = celda
    h, w = A.shape
    img = np.zeros((h // 2 * ch, w * cw, 3), np.uint8) + np.array([245, 230, 253], np.uint8)
    for r in range(h // 2):
        for x in range(w):
            for m in (0, 1):
                y = r * 2 + m
                if A[y, x]:
                    img[r * ch + m * (ch // 2):r * ch + (m + 1) * (ch // 2), x * cw:(x + 1) * cw] = R[y, x]
    return Image.fromarray(img)


alf_v, pal_v, sp_v = leer(VIEJO)
alf_n, pal_n, sp_n = leer(NUEVO)
print("anterior: tamaños", {t: (len(sp_v["nueva"][t][0][0]), len(sp_v["nueva"][t][0])) for t in sp_v["nueva"]})
print("corregido: tamaños", {t: (len(sp_n["nueva"][t][0][0]), len(sp_n["nueva"][t][0])) for t in sp_n["nueva"]})
ESTADOS = ["nueva", "escribiendo", "terminado", "duerme", "hula", "necesita"]
for n in ESTADOS:
    for f in (0, 2):
        imgs = [
            ("ANTES grande (28 x 24 filas)", terminal(*dec(sp_v[n]["L"][f], alf_v, pal_v))),
            ("ANTES normal 70% (20 x 17 filas)", terminal(*dec(sp_v[n]["S"][f], alf_v, pal_v))),
            ("AHORA grande = normal (26 x 20 filas)", terminal(*dec(sp_n[n]["L"][f], alf_n, pal_n))),
            ("AHORA mini (13 x 10 filas)", terminal(*dec(sp_n[n]["X"][f], alf_n, pal_n))),
        ]
        alto = 520
        esc = []
        for t, im in imgs:
            esc.append((t, im.resize((max(1, int(im.size[0] * alto / im.size[1])), alto), Image.NEAREST)))
        # mismas proporciones de pantalla: cada imagen se pinta a la misma escala real (8x16 por celda) escalada igual
        W = sum(e.size[0] for _, e in esc) + 10 * (len(esc) + 1)
        sheet = Image.new("RGB", (W, alto + 40), (30, 30, 36))
        dr = ImageDraw.Draw(sheet)
        x = 10
        for t, e in esc:
            sheet.paste(e, (x, 30))
            dr.text((x, 8), t, fill=(255, 255, 255))
            x += e.size[0] + 10
        sheet.save(f"diag/final_{n}_{f}.png")

# tamaños reales relativos (misma escala de celdas) para ver cuánto ocupa cada uno en la pantalla
esc = 3
fila = []
for t, (alf, pal, sp, tam) in {"ANTES grande": (alf_v, pal_v, sp_v, "L"), "ANTES normal": (alf_v, pal_v, sp_v, "S"), "AHORA grande/normal": (alf_n, pal_n, sp_n, "L"), "AHORA mini": (alf_n, pal_n, sp_n, "X")}.items():
    fila.append((t, terminal(*dec(sp["escribiendo"][tam][0], alf, pal), celda=(4 * esc // 3 * 3 // 3, 8 * esc // 3 * 3 // 3))))
H = max(im.size[1] for _, im in fila)
W = sum(im.size[0] for _, im in fila) + 10 * (len(fila) + 1)
sheet = Image.new("RGB", (W, H + 40), (12, 12, 12))
dr = ImageDraw.Draw(sheet)
x = 10
for t, im in fila:
    sheet.paste(im, (x, 30))
    dr.text((x, 8), t, fill=(255, 255, 255))
    x += im.size[0] + 10
sheet.save("diag/final_tamanos_relativos.png")

# fotogramas completos del estado "escribiendo" y "duerme": 4 de 4, para ver la animación
for n in ("escribiendo", "duerme", "terminado"):
    ims = [terminal(*dec(sp_n[n]["L"][f], alf_n, pal_n), celda=(10, 20)) for f in range(4)]
    W = sum(i.size[0] for i in ims) + 10 * 5
    sheet = Image.new("RGB", (W, ims[0].size[1] + 20), (12, 12, 12))
    x = 10
    for im in ims:
        sheet.paste(im, (x, 10))
        x += im.size[0] + 10
    sheet.save(f"diag/final_animacion_{n}.png")
print("ok")
