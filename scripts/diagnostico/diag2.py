# Diagnóstico etapas 3 (cuadrícula fina), 1 (recorte ancho), 6, 7 y 8, y prototipo de corrección. No modifica el mod.
from PIL import Image, ImageDraw
import numpy as np, collections, json, re
from collections import deque

SRC = r"C:\Users\Admin0011\Proyectos\mods-claude\emilia-mascota\arte\animacion de Emilia pixel de estados.png"
A = np.array(Image.open(SRC).convert("RGB")).astype(int)
H0, W0 = A.shape[:2]
names = ["nueva", "pensando", "responde", "leyendo", "escribiendo", "necesita", "falla", "para", "terminado", "baile", "hula", "duerme"]
cols = [(15, 473), (490, 955), (975, 1435)]
rows = [(30, 262), (283, 515), (538, 777), (795, 1043)]
out = open("diag/informe_etapas_3_8.txt", "w", encoding="utf-8")


def P(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.write(s + "\n")


def label_components(mask):
    H, W = mask.shape
    lab = np.zeros((H, W), np.int32)
    n = 0
    for y in range(H):
        for x in range(W):
            if mask[y, x] and not lab[y, x]:
                n += 1
                lab[y, x] = n
                dq = deque([(y, x)])
                while dq:
                    cy, cx = dq.popleft()
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not lab[ny, nx]:
                                lab[ny, nx] = n
                                dq.append((ny, nx))
    return lab, n


def flood_bg(win, bg, tol=28):
    cand = np.abs(win - bg).sum(axis=2) <= tol
    H, W = cand.shape
    seen = np.zeros((H, W), bool)
    dq = deque()
    for x in range(W):
        for y in (0, H - 1):
            if cand[y, x] and not seen[y, x]:
                seen[y, x] = True
                dq.append((y, x))
    for y in range(H):
        for x in (0, W - 1):
            if cand[y, x] and not seen[y, x]:
                seen[y, x] = True
                dq.append((y, x))
    while dq:
        y, x = dq.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and cand[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                dq.append((ny, nx))
    return ~seen


# ---------- ventanas nominales (las que usa el mod) y anchas (para medir el recorte) ----------
frames = {}
k = 0
for (y0, y1) in rows:
    for (x0, x1) in cols:
        fy1 = y1 - 40
        ix0, ix1 = x0 + 8, x1 - 8
        pw = (ix1 - ix0) / 4
        fig = A[y0 + 10:fy1, ix0:ix1]
        bg = np.array(collections.Counter(map(tuple, fig.reshape(-1, 3)[::7])).most_common(1)[0][0])
        for i in range(4):
            xs = int(round(ix0 + i * pw))
            xe = int(round(ix0 + (i + 1) * pw))
            frames[(names[k], i)] = dict(bg=bg, xs=xs, xe=xe, ys=y0 + 10, ye=fy1, panel=(x0, x1))
        k += 1

P("== ETAPA 1 (ampliada): cuánto sobresale la figura de la ventana de recorte actual ==")
MARGEN = 28
sobresale = []
for key, d in frames.items():
    px0 = max(d["panel"][0] + 8, d["xs"] - MARGEN)
    px1 = min(d["panel"][1] - 8, d["xe"] + MARGEN)
    win = A[d["ys"]:d["ye"], px0:px1]
    fg = flood_bg(win, d["bg"])
    # quitar líneas de borde: filas casi completas arriba y abajo
    for r in list(range(min(14, fg.shape[0]))) + list(range(max(0, fg.shape[0] - 18), fg.shape[0])):
        if fg[r].mean() > 0.6:
            fg[r] = False
    lab, n = label_components(fg)
    nom0, nom1 = d["xs"] - px0, d["xe"] - px0
    keep = np.zeros(fg.shape, bool)
    for c in range(1, n + 1):
        ys_, xs_ = np.where(lab == c)
        if len(ys_) < 6:
            continue
        cx = xs_.mean()
        if nom0 <= cx < nom1:
            keep |= lab == c
    ys_, xs_ = np.where(keep)
    if len(xs_) == 0:
        continue
    izq = max(0, nom0 - xs_.min())
    der = max(0, xs_.max() + 1 - nom1)
    d.update(wide=win, wide_fg=fg, keep=keep, wide_x0=px0, nom=(nom0, nom1))
    if izq or der:
        sobresale.append((key[0], key[1], int(izq), int(der)))
P("fotogramas cuya figura sobresale de la ventana (px a la izquierda, px a la derecha):")
for s in sobresale:
    P("  ", s)
P("total con recorte >0:", len(sobresale), "de 48; máximo recorte:", max([max(s[2], s[3]) for s in sobresale] or [0]), "px")

# ---------- cuadrícula real ----------
P("\n== ETAPA 3: periodo real de la cuadrícula (contraste de fase; mayor = cuadrícula más nítida) ==")


def grid_error(win, fg, kx, ky, px, py):
    H, W = fg.shape
    xx = np.arange(W)
    yy = np.arange(H)
    ix = np.floor((xx - px) / kx)
    iy = np.floor((yy - py) / ky)
    cx = np.clip(np.round(px + (ix + 0.5) * kx).astype(int), 0, W - 1)
    cy = np.clip(np.round(py + (iy + 0.5) * ky).astype(int), 0, H - 1)
    rec = win[np.ix_(cy, cx)]
    valid = fg & (ix[None, :] >= 0) & (iy[:, None] >= 0)
    if valid.sum() == 0:
        return 255.0
    return np.abs(rec - win).sum(axis=2)[valid].mean() / 3


def contraste(win, fg, kk, axis):
    # error del mejor y del peor desfase para un periodo kk (en un eje; el otro eje a 1 px para aislarlo)
    errs = []
    for p in np.arange(0, kk, 0.5):
        errs.append(grid_error(win, fg, kk if axis == "x" else 1.0, kk if axis == "y" else 1.0, p if axis == "x" else 0, p if axis == "y" else 0))
    return (max(errs) - min(errs)) / max(1e-6, max(errs)), int(np.argmin(errs))


muestra = [("nueva", 0), ("escribiendo", 1), ("hula", 0), ("necesita", 2), ("responde", 0), ("duerme", 3)]
res = {"x": [], "y": []}
for key in muestra:
    d = frames[key]
    win, fg = d["wide"], d["wide_fg"]
    for axis in ("x", "y"):
        best = (-1, 0)
        for kk in np.arange(3.0, 6.6, 0.1):
            c, _ = contraste(win, fg, kk, axis)
            if c > best[0]:
                best = (c, kk)
        res[axis].append(best[1])
        P(f"  {key} eje {axis}: periodo con mayor contraste = {best[1]:.1f} px (contraste {best[0] * 100:.0f}%)")
kx = float(np.median(res["x"]))
ky = float(np.median(res["y"]))
P(f"  -> periodo mediano estimado: kx={kx:.2f} px, ky={ky:.2f} px (el mod usa K=4 entero)")
P("  deriva acumulada con K=4 sobre una figura de 24 píxeles de ancho: %.1f px (≈ %.1f píxeles del dibujo)" % (24 * (kx - 4), 24 * (kx - 4) / kx))

# ---------- datos actuales del mod: paleta, L/S/X ----------
J = json.load(open("sprites3.json"))
PAL = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in J["paleta"]])
ALF = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
FL = np.load("frames_L.npy", allow_pickle=True).item()


def decode(rows_):
    h, w = len(rows_), len(rows_[0])
    rgb = np.zeros((h, w, 3), np.uint8)
    al = np.zeros((h, w), bool)
    for y, r in enumerate(rows_):
        for x, c in enumerate(r):
            if c != ".":
                rgb[y, x] = PAL[ALF.index(c)]
                al[y, x] = True
    return rgb, al


P("\n== ETAPA 6: cuantización a 60 colores (error frente al sprite nativo antes de cuantizar) ==")
errs = []
p99 = []
perdidos = collections.Counter()
for n in names:
    for f in range(4):
        rgb0, al0 = FL[n][f]
        rgb1, al1 = decode(J["sprites"][n]["L"][f])
        m = (al0 > 0) & al1
        d = np.abs(rgb0.astype(int) - rgb1.astype(int)).sum(axis=2)[m] / 3
        errs.append(d.mean())
        p99.append(np.percentile(d, 99))
        # colores del nativo cuyo vecino de paleta queda lejos
        px = rgb0[al0 > 0]
        dist = np.sqrt(((px[:, None, :].astype(int) - PAL[None, :, :]) ** 2).sum(-1)).min(axis=1)
        for c, dd in zip(map(tuple, px[dist > 40]), dist[dist > 40]):
            perdidos[(tuple(int(v) // 16 * 16 for v in c))] += 1
P(f"  error medio por píxel: {np.mean(errs):.1f}/255 | percentil 99: {np.mean(p99):.1f}/255")
P("  colores del dibujo que quedan a más de 40 de distancia de su color de paleta (cubeta de 16, nº de píxeles):")
for c, v in perdidos.most_common(8):
    P("   ", c, v)

P("\n== ETAPA 7: conversión a datos de TypeScript (¿se pierde algo al escribir sprites.ts?) ==")
ts = open(r"C:\Users\Admin0011\Proyectos\mods-claude\emilia-mascota\mod\hooks\sprites.ts", encoding="utf-8").read()
mism = 0
total = 0
for n in names:
    for t in ("L", "S", "X"):
        m = re.search(rf"  {n}: \{{.*?    {t}: (\[.*?\]),", ts, re.S)
        lst = json.loads(m.group(1))
        for f in range(4):
            total += 1
            if lst[f].split("/") != J["sprites"][n][t][f]:
                mism += 1
P(f"  fotogramas comparados: {total} | diferencias entre sprites.ts y la cuantización: {mism}  (0 = la escritura es exacta)")

P("\n== ETAPA 8: renderizado Raster con medios bloques ==")
pares_max = {}
for t in ("L", "S", "X"):
    mx = 0
    colores = set()
    for n in names:
        for f in range(4):
            rows_ = J["sprites"][n][t][f]
            pares = set()
            for r in range(0, len(rows_), 2):
                for x in range(len(rows_[0])):
                    a = rows_[r][x]
                    b = rows_[r + 1][x] if r + 1 < len(rows_) else "."
                    pares.add((a, b))
                    colores.update((a, b))
            mx = max(mx, len(pares))
    pares_max[t] = mx
    P(f"  tamaño {t}: pares (arriba, abajo) distintos por fotograma, máximo = {mx} (límite del Raster: 1024) | colores usados: {len(colores) - ('.' in colores)}")
P("  proporción de celda medida en tu captura del terminal: ~8,7 px de ancho x ~17,3 px de alto = 1:2,0 -> cada medio bloque es un píxel cuadrado (sin deformación)")
out.close()

# ---------- prototipo de corrección (solo para comparar; no toca el mod) ----------


def sample_native(win, keep, kx, ky):
    ys_, xs_ = np.where(keep)
    y0, y1, x0, x1 = ys_.min(), ys_.max() + 1, xs_.min(), xs_.max() + 1
    best = None
    sub = win[y0:y1, x0:x1]
    subk = keep[y0:y1, x0:x1]
    for px in np.arange(0, kx, 0.5):
        for py in np.arange(0, ky, 0.5):
            e = grid_error(sub, subk, kx, ky, px, py)
            if best is None or e < best[0]:
                best = (e, px, py)
    _, px, py = best
    h = int(np.ceil((sub.shape[0] - py) / ky))
    w = int(np.ceil((sub.shape[1] - px) / kx))
    rgb = np.zeros((h, w, 3), np.uint8)
    al = np.zeros((h, w), bool)
    for j in range(h):
        for i in range(w):
            ya, yb = int(round(py + j * ky)), int(round(py + (j + 1) * ky))
            xa, xb = int(round(px + i * kx)), int(round(px + (i + 1) * kx))
            m = subk[ya:yb, xa:xb]
            if m.size and m.mean() >= 0.5:
                al[j, i] = True
                # color: mediana del 60 % central del bloque, sin mezclar con el vecino
                ci = win[y0:y1, x0:x1][ya:yb, xa:xb]
                cy0, cy1 = ci.shape[0] // 5, max(ci.shape[0] // 5 + 1, ci.shape[0] - ci.shape[0] // 5)
                cx0, cx1 = ci.shape[1] // 5, max(ci.shape[1] // 5 + 1, ci.shape[1] - ci.shape[1] // 5)
                core = ci[cy0:cy1, cx0:cx1].reshape(-1, 3)
                rgb[j, i] = np.median(core, axis=0)
    return rgb, al, sub, subk, (px, py)


def show(rgb, al, scale):
    o = np.zeros((*rgb.shape[:2], 3), np.uint8) + np.array([245, 230, 253], np.uint8)
    o[al] = rgb[al]
    return Image.fromarray(o).resize((rgb.shape[1] * scale, rgb.shape[0] * scale), Image.NEAREST)


def terminal_sim(rows_, celda=(10, 20)):
    # cada celda: mitad superior con el color de arriba, mitad inferior con el de abajo (fondo de tarjeta si es transparente)
    cw, ch = celda
    h, w = len(rows_), len(rows_[0])
    img = np.zeros((h // 2 * ch, w * cw, 3), np.uint8) + np.array([245, 230, 253], np.uint8)
    for r in range(h // 2):
        for x in range(w):
            for half, c in enumerate((rows_[r * 2][x], rows_[r * 2 + 1][x])):
                if c != ".":
                    img[r * ch + half * (ch // 2): r * ch + (half + 1) * (ch // 2), x * cw:(x + 1) * cw] = PAL[ALF.index(c)]
    return Image.fromarray(img)


metr = []
P2 = []
for key in [("nueva", 0), ("escribiendo", 0), ("terminado", 0), ("duerme", 1), ("hula", 0), ("necesita", 1)]:
    d = frames[key]
    orig = d["wide"][:, :].astype(np.uint8)
    rgb, al, sub, subk, ph = sample_native(d["wide"], d["keep"], kx, ky)
    # reconstruir y medir error de la propuesta con su propia cuadrícula
    e_prop = grid_error(sub, subk, kx, ky, ph[0], ph[1])
    # actual: sprite L del mod (sin cuantizar) -> vuelve a 4 px
    rgbA, alA = FL[key[0]][key[1]]
    metr.append((key, e_prop))
    P2.append(key)
    nat_actual = show(rgbA, alA > 0, 4)
    nat_prop = show(rgb, al, 4)
    term_actual = terminal_sim(J["sprites"][key[0]]["L"][key[1]], (6, 12))
    # contornos de comparación a la misma altura
    th = 420
    ims = [Image.fromarray(orig), nat_actual, nat_prop, term_actual]
    labs = ["original (ventana ancha)", "actual: bloques de 4 px, ventana fija", f"propuesta: rejilla {kx:.1f}x{ky:.1f}, sin recorte", "actual en terminal (grande, medios bloques)"]
    scaled = []
    for im in ims:
        s = th / im.size[1]
        scaled.append(im.resize((max(1, int(im.size[0] * s)), th), Image.NEAREST))
    W = sum(i.size[0] for i in scaled) + 10 * (len(scaled) + 1)
    sheet = Image.new("RGB", (W, th + 40), (30, 30, 36))
    dr = ImageDraw.Draw(sheet)
    x = 10
    for im, lab in zip(scaled, labs):
        sheet.paste(im, (x, 30))
        dr.text((x, 8), lab, fill=(255, 255, 255))
        x += im.size[0] + 10
    sheet.save(f"diag/comparativa_{key[0]}_{key[1]}.png")
print("prototipo: error de reconstrucción con la rejilla propuesta", [(k[0], round(e, 1)) for k, e in metr])
print("ok")
