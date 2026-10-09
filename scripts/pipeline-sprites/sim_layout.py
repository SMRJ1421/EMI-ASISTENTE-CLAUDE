# SIMULACIÓN (no es una captura): cómo se repartiría un terminal de 156 x 41 celdas con la banda y con el panel acoplado.
import json, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ts = open(r"C:/Users/Admin0011/.claude/dev-mods/da5e8c78-c252-4d1c-9f43-47016e40a9d5/mascota/hooks/sprites.ts", encoding="utf-8").read()
alf = re.search(r'export const ALFABETO = "(.*?)"\n', ts).group(1)
def tam(t):
    b = re.search(rf"  {t}: \{{\n    ancho: (\d+),\n    alto: (\d+),\n    paleta: (\[.*?\]),\n    estados: \{{\n(.*?)\n    \}},\n  \}},", ts, re.S)
    ancho, alto = int(b.group(1)), int(b.group(2))
    pal = [[int(h[i:i+2], 16) for i in (1, 3, 5)] for h in json.loads(b.group(3))]
    est = {}
    for m in re.finditer(r"      (\w+): (\[.*?\]),\n", b.group(4)):
        est[m.group(1)] = json.loads(m.group(2))
    return ancho, alto, pal, est
def unrle(t):
    o = []; i = 0
    while i < len(t):
        if t[i] == "§":
            o.append(t[i+2] * "0123456789abcdefghijklmnopqrstuvwxyz".index(t[i+1])); i += 3
        else:
            o.append(t[i]); i += 1
    return "".join(o)
def sprite(t, estado, f):
    ancho, alto, pal, est = tam(t)
    filas = [unrle(r) for r in est[estado][f].split("/")]
    R = np.zeros((alto, ancho, 3), np.uint8); A = np.zeros((alto, ancho), bool)
    for y, r in enumerate(filas):
        for x, c in enumerate(r):
            if c != ".": R[y, x] = pal[alf.index(c)]; A[y, x] = True
    return R, A
CW, CH = 8, 16
COLS, ROWS = 156, 41
img = Image.new("RGB", (COLS * CW, ROWS * CH), (12, 12, 12))
dr = ImageDraw.Draw(img)
def pegar(R, A, col, fila):
    h, w = A.shape
    for r in range(h // 2):
        for x in range(w):
            for m in (0, 1):
                y = r * 2 + m
                c = tuple(int(v) for v in R[y, x]) if A[y, x] else (245, 230, 253)
                x0, y0 = (col + x) * CW, (fila + r) * CH + m * (CH // 2)
                dr.rectangle([x0, y0, x0 + CW - 1, y0 + CH // 2 - 1], fill=c)
def texto(col, fila, s, color=(200, 200, 200)):
    dr.text((col * CW, fila * CH + 1), s, fill=color)
def hoja(titulo, fn, modo):
    global img, dr
    img = Image.new("RGB", (COLS * CW, ROWS * CH), (12, 12, 12)); dr = ImageDraw.Draw(img)
    texto(1, 0, titulo, (255, 220, 120))
    for i in range(1, 36): texto(2, i, "conversación con Claude Code ..." if i % 3 == 0 else "", (110, 110, 110))
    if modo == "banda":
        R, A = sprite("S", "escribiendo", 0)
        base = ROWS - 5 - 10
        pegar(R, A, 1, base); texto(15, base + 1, "Emi", (183, 154, 224)); texto(15, base + 2, "tecleando…", (242, 201, 76)); texto(15, base + 3, "Edit informe.docx", (140, 140, 140)); texto(15, base + 4, "más grande: /emi panel", (140, 140, 140))
        dr.rectangle([8, (ROWS - 4) * CH, COLS * CW - 8, (ROWS - 1) * CH], outline=(120, 120, 120)); texto(3, ROWS - 3, "> escribe aquí", (160, 160, 160))
        texto(1, 1, "[ banda: 15 filas como máximo -> Emi mini 13x20 = 10 filas ]", (255, 120, 120))
    else:
        R, A = sprite("M", "escribiendo", 0)
        x0 = COLS - 44
        for y in range(0, ROWS): dr.line([x0 * CW - 4, y * CH, x0 * CW - 4, (y + 1) * CH], fill=(90, 90, 110))
        pegar(R, A, x0, 2); texto(x0, 33, "Emi · 40 x 60", (183, 154, 224)); texto(x0, 34, "tecleando…", (242, 201, 76)); texto(x0, 35, "Edit informe.docx", (140, 140, 140)); texto(x0, 36, "[ volver a la banda ]", (140, 140, 140))
        dr.rectangle([8, (ROWS - 4) * CH, (x0 - 1) * CW, (ROWS - 1) * CH], outline=(120, 120, 120)); texto(3, ROWS - 3, "> escribe aquí", (160, 160, 160))
        texto(1, 1, "[ panel acoplado: de suelo a techo -> Emi 40x60 = 30 filas (L 52x80 = 40 filas necesita algo más de altura) ]", (120, 255, 160))
    img.save(fn)
import os
os.makedirs("diag/final_mod", exist_ok=True)
hoja("SIMULACIÓN (no es una captura): terminal 156 x 41 con la banda", "diag/final_mod/simulacion_banda.png", "banda")
hoja("SIMULACIÓN (no es una captura): terminal 156 x 41 con el panel acoplado (altura del dock supuesta)", "diag/final_mod/simulacion_panel.png", "panel")
print("ok")
