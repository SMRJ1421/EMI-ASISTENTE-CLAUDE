# Pruebas de resolución: 40x60, 52x80 y 64x96 generadas desde el PNG original (no desde los sprites reducidos).
import json
import pickle
import numpy as np
from PIL import Image, ImageDraw
import emi_lib as L

import os
os.makedirs("diag/alta_res", exist_ok=True)
out = open("diag/alta_res/informe_alta_resolucion.txt", "w", encoding="utf-8")


def P(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.write(s + "\n")


celdas = pickle.load(open("diag/celdas.pkl", "rb"))
par = pickle.load(open("diag/params5.pkl", "rb"))
K0 = par["kx"]            # 4,75 px: rejilla real del dibujo
fases = par["fases"]
ALFA = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!#$%&*+,-:;<=>?@^_~()[]{}|"

# ---- geometría del sprite actual (26 x 40): posición del lienzo sobre la ventana original ----
info = {}
dims = {}
for n in L.NAMES:
    px, py = fases[n]
    fgs = [celdas[(n, i)]["fg"] for i in range(4)]
    y0, y1, x0, x1 = L.bbox_union(fgs)
    j0, j1 = int(np.floor((y0 - py) / K0)), int(np.ceil((y1 - py) / K0))
    i0, i1 = int(np.floor((x0 - px) / K0)), int(np.ceil((x1 - px) / K0))
    al_u = np.zeros((j1 - j0, i1 - i0), bool)
    for i in range(4):
        c = celdas[(n, i)]
        _, al = L.muestrear(c["win"], c["fg"], K0, K0, px, py, j0, j1, i0, i1, "borde")
        al_u |= al
    ys, xs = np.where(al_u)
    ya, yb, xa, xb = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    info[n] = (j0 + ya, i0 + xa)
    dims[n] = (yb - ya, xb - xa)
GH = max(d[0] for d in dims.values())
GW = max(d[1] for d in dims.values())
GW += GW % 2
GH += (-GH) % 4
P(f"lienzo actual: {GW} x {GH} píxeles de sprite (rejilla de {K0} px del original) -> cubre {GW * K0:.1f} x {GH * K0:.1f} px del PNG")

RESOLUCIONES = {"40x60": (40, 60), "52x80": (52, 80), "64x96": (64, 96)}
alto_px = GH * K0
datos = {}   # (res, estado, frame) -> (rgb, al)
geo = {}
P("\n== GEOMETRÍA DE CADA RESOLUCIÓN (siempre el mismo alto de PNG, píxel cuadrado) ==")
for nombre, (W, H) in RESOLUCIONES.items():
    k = alto_px / H
    P(f"  {nombre}: paso de muestreo {k:.3f} px del original (los dos ejes iguales) | píxeles de muestreo por píxel del dibujo = {K0 / k:.2f} | cubre {W * k:.1f} x {H * k:.1f} px | celdas de terminal: {W} columnas x {H // 2} filas")
    geo[nombre] = k

cortes = {r: 0 for r in RESOLUCIONES}
cov = {r: [] for r in RESOLUCIONES}
err = {r: [] for r in RESOLUCIONES}
dif = {r: [] for r in RESOLUCIONES}
for n in L.NAMES:
    px, py = fases[n]
    jt = info[n][0] - (GH - dims[n][0])
    il = info[n][1] - (GW - dims[n][1]) // 2
    Y0 = py + jt * K0
    X0 = px + il * K0
    for nombre, (W, H) in RESOLUCIONES.items():
        k = geo[nombre]
        x0 = X0 - (W * k - GW * K0) / 2
        for i in range(4):
            c = celdas[(n, i)]
            rgb, al = L.muestrear(c["win"], c["fg"], k, k, x0, Y0, 0, H, 0, W, "centro")
            datos[(nombre, n, i)] = (rgb, al)
            e, cv = L.error_reconstruccion(c["win"], c["fg"], rgb, al, k, k, x0, Y0, 0, 0)
            err[nombre].append(e)
            cov[nombre].append(cv)
            # cortes: primer plano del original que cae fuera del lienzo
            Hh, Ww = c["fg"].shape
            m = np.zeros((Hh, Ww), bool)
            ya, yb = max(0, int(np.floor(Y0))), min(Hh, int(np.ceil(Y0 + H * k)))
            xa, xb = max(0, int(np.floor(x0))), min(Ww, int(np.ceil(x0 + W * k)))
            m[ya:yb, xa:xb] = True
            cortes[nombre] += int((c["fg"] & ~m).sum())
            # cuánto detalle nuevo hay frente al sprite actual: muestras cuyo color no coincide con el píxel nativo que las contiene
            nj, ni = int(Hh / K0) + 2, int(Ww / K0) + 2
            nat_rgb, nat_al = L.muestrear(c["win"], c["fg"], K0, K0, px, py, 0, nj, 0, ni, "centro")
            ys_, xs_ = np.where(al)
            if len(ys_):
                gj = np.floor((Y0 + (ys_ + 0.5) * k - py) / K0).astype(int)
                gi = np.floor((x0 + (xs_ + 0.5) * k - px) / K0).astype(int)
                ok = (gj >= 0) & (gj < nj) & (gi >= 0) & (gi < ni)
                ok[ok] = nat_al[gj[ok], gi[ok]]
                if ok.any():
                    d = np.abs(rgb[ys_[ok], xs_[ok]].astype(int) - nat_rgb[gj[ok], gi[ok]].astype(int)).sum(axis=1) / 3
                    dif[nombre].append(float((d > 30).mean()))

P("\n== FIDELIDAD FRENTE AL PNG ORIGINAL (48 fotogramas) ==")
for nombre in RESOLUCIONES:
    P(f"  {nombre}: error medio {np.mean(err[nombre]):.1f}/255 | cobertura del primer plano {np.mean(cov[nombre]) * 100:.1f}% (mín {np.min(cov[nombre]) * 100:.1f}%) | píxeles del original fuera del lienzo (cortados): {cortes[nombre]} | muestras que difieren del píxel nativo: {np.mean(dif[nombre]) * 100:.1f}%")
P("  (para comparar: el sprite actual 26x40 tiene cobertura 96,3% y por definición 0% de muestras distintas)")


import colorsys


def hacer_paleta(px, nc):
    """Paleta con colores reales del dibujo: 3 semillas por cada tono vivo (para que ojos y confeti no se fundan con otros verdes
    o azules) y el resto por corte de medianas sobre el resto de píxeles."""
    p = px.astype(int)
    sat = (p.max(axis=1) - p.min(axis=1)) > 110
    semillas = []
    vivos = px[sat]
    if len(vivos):
        hsv = np.array([colorsys.rgb_to_hsv(*(c / 255.0)) for c in vivos[:: max(1, len(vivos) // 20000)]])
        mues = vivos[:: max(1, len(vivos) // 20000)]
        h = hsv[:, 0] * 360
        for lo, hi in ((0, 20), (340, 361), (20, 45), (45, 70), (70, 170), (170, 200), (200, 260), (260, 340)):
            sel = mues[(h >= lo) & (h < hi)]
            if len(sel) >= 15:
                qq = Image.fromarray(sel.reshape(1, -1, 3).astype(np.uint8), "RGB").quantize(colors=3, method=Image.MEDIANCUT, dither=Image.NONE)
                semillas.extend(np.array(qq.getpalette()[:9]).reshape(-1, 3).tolist())
    resto = px[~sat]
    n_resto = max(8, nc - len(semillas))
    qq = Image.fromarray(resto.reshape(1, -1, 3).astype(np.uint8), "RGB").quantize(colors=n_resto, method=Image.MEDIANCUT, dither=Image.NONE)
    base = np.array(qq.getpalette()[:n_resto * 3]).reshape(-1, 3)
    return np.vstack([np.array(semillas).reshape(-1, 3), base])[:nc]

# ---- paletas y límite de pares de colores del Raster ----
P("\n== LÍMITES DEL RASTER (medidos sobre los datos reales) ==")
NC = 88
paletas = {}
cuant = {}
for nombre, (W, H) in RESOLUCIONES.items():
    cols = []
    for n in L.NAMES:
        for i in range(4):
            rgb, al = datos[(nombre, n, i)]
            cols.append(rgb[al])
    allc = np.concatenate(cols).astype(np.uint8)
    pal = hacer_paleta(allc, NC)
    paletas[nombre] = pal
    mx = 0
    errq = []
    for n in L.NAMES:
        for i in range(4):
            rgb, al = datos[(nombre, n, i)]
            d = ((rgb[..., None, :].astype(int) - pal[None, None]) ** 2).sum(-1)
            ix = d.argmin(-1)
            ix = np.where(al, ix, 255)
            cuant[(nombre, n, i)] = (pal[np.where(al, ix, 0)].astype(np.uint8), al, ix)
            errq.append(np.abs(pal[np.where(al, ix, 0)].astype(int) - rgb.astype(int)).sum(axis=2)[al].mean() / 3)
            pares = set()
            for r in range(0, H, 2):
                a = ix[r]
                b = ix[r + 1]
                pares.update(zip(a.tolist(), b.tolist()))
            mx = max(mx, len(pares))
    celdas_n = W * (H // 2)
    P(f"  {nombre}: {celdas_n} celdas por fotograma | datos por redibujo {celdas_n * 12 / 1024:.1f} KB ({celdas_n * 12 * 4 / 3 / 1024:.1f} KB en base64) | pares (arriba,abajo) distintos por fotograma, máximo = {mx} (límite del Raster: 1024) | error de cuantización {np.mean(errq):.1f}/255")
P("  límites del motor: Raster hasta 512 columnas x 256 filas; el motor redibuja el band como mucho 30 veces por segundo en terminal (el mod usa 4)")
P("  límite de filas disponible: e.props.maxRows. En el modo de pantalla completa el hueco se limita a la mitad de las filas del terminal (incluido el cuadro de texto); fuera de él, a la altura del terminal. Hace falta medirlo en tu terminal.")

# ---- comparaciones visuales ----
def terminal(rgb, al, celda=(6, 12)):
    cw, ch = celda
    h, w = al.shape
    img = np.zeros((h // 2 * ch, w * cw, 3), np.uint8) + np.array([245, 230, 253], np.uint8)
    for r in range(h // 2):
        for x in range(w):
            for m_ in (0, 1):
                y = r * 2 + m_
                if al[y, x]:
                    img[r * ch + m_ * (ch // 2):r * ch + (m_ + 1) * (ch // 2), x * cw:(x + 1) * cw] = rgb[y, x]
    return Image.fromarray(img)


actual = json.load(open("diag/sprites_corregidos.json"))
pal_a = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in actual["paleta"]])


def dec_actual(n, f):
    filas = actual["sprites"][n]["L"][f]
    h, w = len(filas), len(filas[0])
    R = np.zeros((h, w, 3), np.uint8)
    A_ = np.zeros((h, w), bool)
    for y, r in enumerate(filas):
        for x, ch_ in enumerate(r):
            if ch_ != ".":
                R[y, x] = pal_a[actual["alfabeto"].index(ch_)]
                A_[y, x] = True
    return R, A_


for n in ["nueva", "escribiendo", "terminado", "duerme", "hula", "necesita"]:
    for f in (0, 2):
        c = celdas[(n, f)]
        orig = c["win"].astype(np.uint8).copy()
        orig[~c["fg"]] = (245, 230, 253)
        imgs = [("original (PNG)", Image.fromarray(orig))]
        ra, aa = dec_actual(n, f)
        imgs.append(("ACTUAL 26x40", terminal(ra, aa, (6, 12))))
        for nombre in RESOLUCIONES:
            rgb, al, ix = cuant[(nombre, n, f)]
            imgs.append((nombre, terminal(rgb, al, (6, 12))))
        # a la misma altura de pantalla para comparar detalle
        alto = 560
        esc = [(t, im.resize((max(1, int(im.size[0] * alto / im.size[1])), alto), Image.NEAREST)) for t, im in imgs]
        W = sum(e.size[0] for _, e in esc) + 10 * (len(esc) + 1)
        sh = Image.new("RGB", (W, alto + 40), (30, 30, 36))
        dr = ImageDraw.Draw(sh)
        x = 10
        for t, e in esc:
            sh.paste(e, (x, 30))
            dr.text((x, 8), t, fill=(255, 255, 255))
            x += e.size[0] + 10
        sh.save(f"diag/alta_res/misma_altura_{n}_{f}.png")

# tamaño real relativo en pantalla (cada celda 8x16 px)
fila = []
for t, (rgb, al) in [("ACTUAL 26x40 (20 filas)", dec_actual("escribiendo", 0))] + [(f"{r} ({RESOLUCIONES[r][1] // 2} filas)", cuant[(r, "escribiendo", 0)][:2]) for r in RESOLUCIONES]:
    fila.append((t, terminal(rgb, al, (8, 16))))
H = max(im.size[1] for _, im in fila)
W = sum(im.size[0] for _, im in fila) + 10 * (len(fila) + 1)
sh = Image.new("RGB", (W, H + 40), (12, 12, 12))
dr = ImageDraw.Draw(sh)
x = 10
for t, im in fila:
    sh.paste(im, (x, 30))
    dr.text((x, 8), t, fill=(255, 255, 255))
    x += im.size[0] + 10
sh.save("diag/alta_res/tamano_real_en_pantalla.png")

# datos para el mod de laboratorio (3 estados) y para pruebas
paq = {"paletas": {r: ["#%02x%02x%02x" % tuple(int(v) for v in c) for c in paletas[r]] for r in RESOLUCIONES}, "alfabeto": ALFA, "sprites": {}}
for nombre, (W, H) in RESOLUCIONES.items():
    for n in L.NAMES:
        frames = []
        for i in range(4):
            rgb, al, ix = cuant[(nombre, n, i)]
            frames.append(["".join(ALFA[ix[y, x]] if al[y, x] else "." for x in range(W)) for y in range(H)])
        paq["sprites"].setdefault(n, {})[nombre] = frames
json.dump(paq, open("diag/alta_res/sprites_alta_res.json", "w"))
out.close()
print("ok")
