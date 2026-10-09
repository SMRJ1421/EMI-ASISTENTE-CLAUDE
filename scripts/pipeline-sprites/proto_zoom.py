# Prototipo de laboratorio: ¿mejora el reescalado «por votación» (idea de dgokcin/claude-pokemon-mod, implementada por mí desde cero)
# a nuestros métodos actuales para llenar las 14 filas útiles de la banda (sprite de 18 x 28)?
import json
import pickle
import re
import numpy as np
from PIL import Image, ImageDraw
import emi_lib as L

TS = r"C:/Users/Admin0011/Proyectos/mods-claude/emilia-mascota/laboratorio/hooks/sprites.ts"
ts = open(TS, encoding="utf-8").read()
ALFA = re.search(r'export const ALFABETO = "(.*?)"\n', ts).group(1)
NAMES = L.NAMES
out = open("diag/informe_proto_zoom.txt", "w", encoding="utf-8")


def P(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.write(s + "\n")


def unrle(t):
    o = []
    i = 0
    while i < len(t):
        if t[i] == "§":
            o.append(t[i + 2] * "0123456789abcdefghijklmnopqrstuvwxyz".index(t[i + 1]))
            i += 3
        else:
            o.append(t[i])
            i += 1
    return "".join(o)


def cargar(t):
    b = re.search(rf"  {t}: \{{\n    ancho: (\d+),\n    alto: (\d+),\n    paleta: (\[.*?\]),\n    estados: \{{\n(.*?)\n    \}},\n  \}},", ts, re.S)
    pal = [[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in json.loads(b.group(3))]
    est = {}
    for m in re.finditer(r"      (\w+): (\[.*?\]),(?:\n|$)", b.group(4)):
        est[m.group(1)] = [[unrle(r) for r in f.split("/")] for f in json.loads(m.group(2))]
    return int(b.group(1)), int(b.group(2)), pal, est


SPR = {t: cargar(t) for t in ("S", "N", "L", "XL")}


def luz_de(pal):
    return lambda c: 0.299 * pal[ALFA.index(c)][0] + 0.587 * pal[ALFA.index(c)][1] + 0.114 * pal[ALFA.index(c)][2]


def zoom_voto(filas, w2, h2, luz):
    """Cada píxel de salida reúne un bloque del original: gana el color con más votos; si empatan, el más oscuro.
    El bloque con menos de la mitad opaco queda transparente, salvo que su trazo cruce el bloque de borde a borde (líneas finas)."""
    H, W = len(filas), len(filas[0])
    salida = []
    for j in range(h2):
        y0, y1 = (j * H) // h2, -(-((j + 1) * H) // h2)
        fila = []
        for i in range(w2):
            x0, x1 = (i * W) // w2, -(-((i + 1) * W) // w2)
            votos = {}
            opacos = 0
            mnx = mny = 10**9
            mxx = mxy = -1
            for y in range(y0, y1):
                for x in range(x0, x1):
                    c = filas[y][x]
                    if c != ".":
                        opacos += 1
                        votos[c] = votos.get(c, 0) + 1
                        mnx, mxx, mny, mxy = min(mnx, x), max(mxx, x), min(mny, y), max(mxy, y)
            total = (y1 - y0) * (x1 - x0)
            if opacos == 0:
                fila.append(".")
                continue
            if opacos * 2 < total and not ((mnx == x0 and mxx == x1 - 1) or (mny == y0 and mxy == y1 - 1)):
                fila.append(".")
                continue
            fila.append(max(votos, key=lambda c: (votos[c], -luz(c), -ALFA.index(c))))
        salida.append("".join(fila))
    return salida


def vecino(filas, w2, h2):
    H, W = len(filas), len(filas[0])
    return ["".join(filas[min(H - 1, int((j + 0.5) * H / h2))][min(W - 1, int((i + 0.5) * W / w2))] for i in range(w2)) for j in range(h2)]


def a_rgb(filas, pal):
    h, w = len(filas), len(filas[0])
    R = np.zeros((h, w, 3), np.uint8)
    A = np.zeros((h, w), bool)
    for y, r in enumerate(filas):
        for x, c in enumerate(r):
            if c != ".":
                R[y, x] = pal[ALFA.index(c)]
                A[y, x] = True
    return R, A


# ---- geometría del lienzo (igual que hires.py) ----
celdas = pickle.load(open("diag/celdas.pkl", "rb"))
par = pickle.load(open("diag/params5.pkl", "rb"))
K0 = par["kx"]
fases = par["fases"]
info, dims = {}, {}
for n in NAMES:
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
    info[n] = (j0 + ys.min(), i0 + xs.min())
    dims[n] = (ys.max() + 1 - ys.min(), xs.max() + 1 - xs.min())
GH = max(d[0] for d in dims.values())
GW = max(d[1] for d in dims.values())
GW += GW % 2
GH += (-GH) % 4

W2, H2 = 18, 28
k = GH * K0 / H2
P(f"destino {W2}x{H2} ({H2 // 2} filas): paso sobre el PNG k={k:.3f}; lienzo actual {GW}x{GH}")

metodos = ["A nearest desde N (26x40)", "B votos desde N (26x40)", "C votos desde L (52x80)", "D votos desde XL (64x96)", "E muestreo directo del PNG", "G directo del PNG + regla de trazo", "F mini actual S 13x20 (para tamaño)"]
err = {m: [] for m in metodos}
dist = {m: [] for m in metodos}
aislados = {m: [] for m in metodos}
ojos = {m: [] for m in metodos}
imgs = {}
palN, palL, palXL, palS = SPR["N"][2], SPR["L"][2], SPR["XL"][2], SPR["S"][2]
lz = {"N": luz_de(palN), "L": luz_de(palL), "XL": luz_de(palXL)}



def suavizar(a):
    p = np.pad(a.astype(float), ((1, 1), (1, 1), (0, 0)), mode="edge")
    return sum(p[dy:dy + a.shape[0], dx:dx + a.shape[1]] for dy in range(3) for dx in range(3)) / 9


def referencia(win, fg, x0, Y0, kk, h2, w2):
    """La reducción ideal: el PNG (primer plano sobre la tarjeta) promediado por área al tamaño del destino."""
    H, W = fg.shape
    comp = np.zeros((H, W, 3), float) + np.array([245, 230, 253], float)
    comp[fg] = win[fg]
    ref = np.zeros((h2, w2, 3), float) + np.array([245, 230, 253], float)
    for j in range(h2):
        for i in range(w2):
            ya, yb = int(round(Y0 + j * kk)), int(round(Y0 + (j + 1) * kk))
            xa, xb = int(round(x0 + i * kk)), int(round(x0 + (i + 1) * kk))
            ya, yb, xa, xb = max(0, ya), min(H, yb), max(0, xa), min(W, xb)
            if yb > ya and xb > xa:
                ref[j, i] = comp[ya:yb, xa:xb].reshape(-1, 3).mean(axis=0)
    return ref


def distancia(R, A, ref):
    img = np.zeros((*A.shape, 3), float) + np.array([245, 230, 253], float)
    img[A] = R[A]
    return float(np.abs(suavizar(img) - suavizar(ref)).mean())

def metricas(nombre, R, A, win, fg, x0, Y0, kk):
    e, _ = L.error_reconstruccion(win, fg, R, A, kk, kk, x0, Y0, 0, 0)
    err[nombre].append(e)
    dist[nombre].append(distancia(R, A, referencia(win, fg, x0, Y0, kk, A.shape[0], A.shape[1])))
    osc = (R.astype(int).sum(axis=2) < 150) & A
    pad = np.pad(osc, 1)
    vec = pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
    aislados[nombre].append((osc & ~vec).sum() / max(1, osc.sum()))
    r = R.astype(int)
    cian = A & (r[..., 2] > 170) & (r[..., 2] > r[..., 0] + 40)
    ojos[nombre].append(int(cian.sum()))


for n in NAMES:
    px, py = fases[n]
    jt = info[n][0] - (GH - dims[n][0])
    il = info[n][1] - (GW - dims[n][1]) // 2
    Y0 = py + jt * K0
    X0 = px + il * K0
    x0 = X0 - (W2 * k - GW * K0) / 2
    for f in range(4):
        c = celdas[(n, f)]
        win, fg = c["win"], c["fg"]
        cands = {}
        cands[metodos[0]] = (vecino(SPR["N"][3][n][f], W2, H2), palN)
        cands[metodos[1]] = (zoom_voto(SPR["N"][3][n][f], W2, H2, lz["N"]), palN)
        cands[metodos[2]] = (zoom_voto(SPR["L"][3][n][f], W2, H2, lz["L"]), palL)
        cands[metodos[3]] = (zoom_voto(SPR["XL"][3][n][f], W2, H2, lz["XL"]), palXL)
        for m, (filas, pal) in cands.items():
            R, A = a_rgb(filas, pal)
            metricas(m, R, A, win, fg, x0, Y0, k)
            if f == 0 and n in ("nueva", "escribiendo", "terminado", "hula"):
                imgs[(n, m)] = (R, A)
        R, A = L.muestrear(win, fg, k, k, x0, Y0, 0, H2, 0, W2, "centro")
        metricas(metodos[4], R, A, win, fg, x0, Y0, k)
        if f == 0 and n in ("nueva", "escribiendo", "terminado", "hula"):
            imgs[(n, metodos[4])] = (R, A)
        R, A = L.muestrear(win, fg, k, k, x0, Y0, 0, H2, 0, W2, "borde")
        metricas(metodos[5], R, A, win, fg, x0, Y0, k)
        if f == 0 and n in ("nueva", "escribiendo", "terminado", "hula"):
            imgs[(n, metodos[5])] = (R, A)
        # S actual (13x20) solo para comparar el tamaño: su geometría es otra, se mide con el mismo método sobre su lienzo
        R, A = a_rgb(SPR["S"][3][n][f], palS)
        if f == 0 and n in ("nueva", "escribiendo", "terminado", "hula"):
            imgs[(n, metodos[6])] = (R, A)

P("\nresultados medios sobre 48 fotogramas (menor error = más fiel al PNG; contorno aislado = % de píxeles de trazo sin vecino; píxeles celestes = ojos conservados)")
for m in metodos[:6]:
    P(f"  {m}: error {np.mean(err[m]):.1f}/255 | apariencia a distancia {np.mean(dist[m]):.2f} | contorno aislado {np.mean(aislados[m]) * 100:.1f}% | píxeles de ojo celestes por fotograma {np.mean(ojos[m]):.1f}")

# ---- imágenes ----
card = np.array([245, 230, 253], np.uint8)


def pintar(R, A, esc):
    img = np.zeros((*A.shape, 3), np.uint8) + card
    img[A] = R[A]
    return Image.fromarray(img).resize((A.shape[1] * esc, A.shape[0] * esc), Image.NEAREST)


for n in ("nueva", "escribiendo", "terminado", "hula"):
    ims = [(m.split(" ")[0] + " " + " ".join(m.split(" ")[1:3]), pintar(*imgs[(n, m)], 14 if m.startswith("F") else 9)) for m in metodos]
    alto = max(i.size[1] for _, i in ims) + 40
    W = sum(i.size[0] for _, i in ims) + 10 * (len(ims) + 1)
    sh = Image.new("RGB", (W, alto), (30, 30, 36))
    dr = ImageDraw.Draw(sh)
    x = 10
    for t, im in ims:
        sh.paste(im, (x, 30))
        dr.text((x, 8), t, fill=(255, 255, 255))
        x += im.size[0] + 10
    sh.save(f"diag/final_mod/proto_zoom_{n}.png")
out.close()
print("ok")
