# Diagnóstico etapas 1-4: recorte, fondo, cuadrícula, reducción. No modifica el mod.
from PIL import Image, ImageDraw
import numpy as np, collections
from collections import deque

SRC = r"C:\Users\Admin0011\Downloads\animacion de Emilia pixel de estados.png"
A = np.array(Image.open(SRC).convert("RGB")).astype(int)
names = ["nueva", "pensando", "responde", "leyendo", "escribiendo", "necesita", "falla", "para", "terminado", "baile", "hula", "duerme"]
cols = [(15, 473), (490, 955), (975, 1435)]
rows = [(30, 262), (283, 515), (538, 777), (795, 1043)]
K = 4


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


def phase(win):
    g = np.abs(np.diff(win, axis=1)).sum(axis=(0, 2))
    h = np.abs(np.diff(win, axis=0)).sum(axis=(1, 2))
    px = max(range(K), key=lambda p: g[p::K].sum())
    py = max(range(K), key=lambda p: h[p::K].sum())
    return (px + 1) % K, (py + 1) % K


wins = {}
k = 0
for (y0, y1) in rows:
    for (x0, x1) in cols:
        fy1 = y1 - 40
        ix0 = x0 + 8
        ix1 = x1 - 8
        pw = (ix1 - ix0) / 4
        fig = A[y0 + 10:fy1, ix0:ix1]
        bg = np.array(collections.Counter(map(tuple, fig.reshape(-1, 3)[::7])).most_common(1)[0][0])
        for i in range(4):
            xs = int(round(ix0 + i * pw))
            xe = int(round(ix0 + (i + 1) * pw))
            wins[(names[k], i)] = dict(win=A[y0 + 10:fy1, xs:xe], bg=bg)
        k += 1


def up(arr, s):
    return np.kron(arr, np.ones((s, s, 1), dtype=arr.dtype)) if arr.ndim == 3 else np.kron(arr, np.ones((s, s), dtype=arr.dtype))


out = open("diag/informe_etapas_1_4.txt", "w", encoding="utf-8")


def P(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.write(s + "\n")


P("== ETAPA 1: recorte de ventanas ==")
clip = []
for (n, i), d in wins.items():
    d["fg"] = flood_bg(d["win"], d["bg"])
    fg = d["fg"]
    L, R, T, B = int(fg[:, 0].sum()), int(fg[:, -1].sum()), int(fg[0, :].sum()), int(fg[-1, :].sum())
    if L or R or T:
        clip.append((n, i, L, R, T, B))
P("ventanas:", len(wins), "tamaño de ventana (alto, ancho):", wins[("nueva", 0)]["win"].shape[:2])
P("fotogramas cuya figura toca el borde de la ventana (izq, der, arriba, abajo en px):")
for c in clip:
    P("  ", c)
if not clip:
    P("   ninguno")

P("\n== ETAPA 2: eliminación de fondo (flood-fill, tol=28) ==")
for key in [("nueva", 0), ("escribiendo", 0), ("terminado", 0), ("hula", 0), ("duerme", 0)]:
    d = wins[key]
    win, fg, bg = d["win"], d["fg"], d["bg"]
    diff = np.abs(win - bg).sum(axis=2)
    perdido = int(((diff > 28) & (~fg)).sum())
    halo = int(((diff > 10) & (diff <= 60) & (~fg)).sum())
    resto = int(((diff <= 28) & fg).sum())
    P(f"  {key}: figura={int(fg.sum())} px | primer plano perdido={perdido} | franja suave descartada={halo} | interior casi-fondo conservado={resto}")


def recon_error(win, fg, k, px, py):
    H, W = fg.shape
    h = int((H - py) / k)
    w = int((W - px) / k)
    rec = np.zeros_like(win)
    for j in range(h):
        for i in range(w):
            y0 = int(py + j * k)
            x0 = int(px + i * k)
            y1 = int(py + (j + 1) * k)
            x1 = int(px + (i + 1) * k)
            cy = min(H - 1, int(py + (j + 0.5) * k))
            cx = min(W - 1, int(px + (i + 0.5) * k))
            rec[y0:y1, x0:x1] = win[cy, cx]
    m = np.zeros(fg.shape, bool)
    m[int(py):int(py + h * k), int(px):int(px + w * k)] = True
    mm = m & fg
    return np.abs(rec - win).sum(axis=2)[mm].mean() / 3


P("\n== ETAPA 3: cuadrícula de píxeles (error de reconstruir con una cuadrícula de lado k; menor = más nítida) ==")
for key in [("nueva", 0), ("escribiendo", 0), ("terminado", 0), ("hula", 0)]:
    d = wins[key]
    win, fg = d["win"], d["fg"]
    best = None
    for kk in np.arange(3.0, 5.51, 0.1):
        for px in range(0, 5):
            for py in range(0, 5):
                e = recon_error(win, fg, kk, px, py)
                if best is None or e < best[0]:
                    best = (e, kk, px, py)
    e4 = min(recon_error(win, fg, 4.0, px, py) for px in range(4) for py in range(4))
    P(f"  {key}: mejor k={best[1]:.1f} (error {best[0]:.1f}/255) | k=4 entero: {e4:.1f}/255")


def down(win, fg, modo, k=4):
    px, py = phase(win)
    win = win[py:, px:]
    fg = fg[py:, px:]
    H, W = fg.shape
    h, w = H // k, W // k
    rgb = np.zeros((h, w, 3), np.uint8)
    al = np.zeros((h, w), bool)
    for j in range(h):
        for i in range(w):
            m = fg[j * k:(j + 1) * k, i * k:(i + 1) * k]
            blk = win[j * k:(j + 1) * k, i * k:(i + 1) * k]
            if modo == "centro":
                if fg[j * k + k // 2, i * k + k // 2]:
                    al[j, i] = True
                    rgb[j, i] = win[j * k + k // 2, i * k + k // 2]
            elif m.mean() >= 0.5:
                al[j, i] = True
                px_ = blk.reshape(-1, 3)[m.reshape(-1)]
                if modo == "mediana":
                    rgb[j, i] = np.median(px_, axis=0)
                else:
                    c = collections.Counter(map(tuple, px_ // 8)).most_common(1)[0][0]
                    rgb[j, i] = np.array(c) * 8 + 4
    return rgb, al, win, fg


def err(rgb, al, win, fg, k=4):
    r = up(rgb, k)
    a = up(al.astype(np.uint8), k).astype(bool)
    H, W = a.shape
    m = a & fg[:H, :W]
    d = np.abs(r.astype(int) - win[:H, :W]).sum(axis=2) / 3
    cover = (fg[:H, :W] & a).sum() / max(1, fg[:H, :W].sum())
    return d[m].mean(), cover


P("\n== ETAPA 4: reducción a la cuadrícula nativa (error medio frente al original; cobertura del primer plano) ==")
for etiqueta, modo in (("bloque-mediana (actual)", "mediana"), ("muestreo central (nearest)", "centro"), ("moda del bloque", "moda")):
    es, cv = [], []
    for key, d in wins.items():
        r = down(d["win"], d["fg"], modo)
        e, c = err(*r)
        es.append(e)
        cv.append(c)
    P(f"  {etiqueta}: error medio {np.mean(es):.1f}/255 | cobertura {np.mean(cv) * 100:.1f}%")
out.close()


def tile(imgs, labels, fn, scale_h=360):
    ims = []
    for im, lab in zip(imgs, labels):
        im = Image.fromarray(im) if isinstance(im, np.ndarray) else im
        w, h = im.size
        s = scale_h / h
        ims.append((im.resize((int(w * s), scale_h), Image.NEAREST), lab))
    W = sum(i.size[0] for i, _ in ims) + 10 * (len(ims) + 1)
    sheet = Image.new("RGB", (W, scale_h + 40), (30, 30, 36))
    dr = ImageDraw.Draw(sheet)
    x = 10
    for im, lab in ims:
        sheet.paste(im, (x, 30))
        dr.text((x, 8), lab, fill=(255, 255, 255))
        x += im.size[0] + 10
    sheet.save(fn)


def show(rgb, al):
    o = np.zeros((*rgb.shape[:2], 3), np.uint8) + np.array([245, 230, 253], np.uint8)
    o[al] = rgb[al]
    return o


for key in [("nueva", 0), ("escribiendo", 0), ("terminado", 0), ("hula", 0)]:
    d = wins[key]
    win = d["win"].astype(np.uint8)
    fg = d["fg"]
    mask = np.zeros_like(win)
    mask[fg] = win[fg]
    mask[~fg] = (60, 60, 60)
    diff = np.abs(d["win"] - d["bg"]).sum(axis=2)
    ov = win.copy()
    ov[(~fg) & (diff > 10)] = (255, 0, 0)
    ov[(diff <= 28) & fg] = (0, 200, 255)
    rM = down(d["win"], fg, "mediana")
    rC = down(d["win"], fg, "centro")
    tile([win, mask, ov, show(rM[0], rM[1]), show(rC[0], rC[1])],
         ["1 original", "2 mascara", "2 rojo=franja perdida azul=interior", "4 bloque-mediana", "4 muestreo central"],
         f"diag/etapas_1_4_{key[0]}.png")
print("ok")
