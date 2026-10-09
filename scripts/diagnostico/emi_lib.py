# Biblioteca del pipeline corregido de Emi (recorte sin cortes, cuadrícula real, muestreo). No toca el mod.
from PIL import Image
import numpy as np
import collections
from collections import deque

SRC = r"C:\Users\Admin0011\Proyectos\mods-claude\emilia-mascota\arte\animacion de Emilia pixel de estados.png"
A = np.array(Image.open(SRC).convert("RGB")).astype(int)
NAMES = ["nueva", "pensando", "responde", "leyendo", "escribiendo", "necesita", "falla", "para", "terminado", "baile", "hula", "duerme"]
COLS = [(15, 473), (490, 955), (975, 1435)]
ROWS = [(30, 262), (283, 515), (538, 777), (795, 1043)]
MARG = 28          # margen a cada lado de la celda nominal, para no cortar figuras que se salen
BUSCA = 34         # hasta dónde se busca un hueco para cortar entre vecinos
FONDO = np.array([245, 230, 253])


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


def cargar_celdas():
    """Devuelve {(estado, i): dict(win, fg, nom0, nom1, cutL, cutR, aviso...)} con coordenadas relativas a la celda."""
    celdas = {}
    k = 0
    for (y0, y1) in ROWS:
        for (x0, x1) in COLS:
            fy1 = y1 - 40
            ix0, ix1 = x0 + 8, x1 - 8
            pw = (ix1 - ix0) / 4
            fig = A[y0 + 10:fy1, ix0:ix1]
            bg = np.array(collections.Counter(map(tuple, fig.reshape(-1, 3)[::7])).most_common(1)[0][0])
            for i in range(4):
                xs = int(round(ix0 + i * pw))
                xe = xs + int(round(pw))      # ancho de celda fijo: todos los fotogramas comparten forma y coordenadas
                X0, X1 = xs - MARG, xe + MARG
                H = fy1 - (y0 + 10)
                win = np.zeros((H, X1 - X0, 3), int) + bg
                a0, a1 = max(X0, ix0), min(X1, ix1)
                win[:, a0 - X0:a1 - X0] = A[y0 + 10:fy1, a0:a1]
                fg = flood_bg(win, bg)
                for r in list(range(min(14, H))) + list(range(max(0, H - 18), H)):
                    if fg[r].mean() > 0.6:
                        fg[r] = False
                nom0, nom1 = MARG, MARG + (xe - xs)
                perfil = fg.sum(axis=0)
                cands_l = range(max(0, nom0 - BUSCA), nom0 + BUSCA + 1)
                cands_r = range(nom1 - BUSCA, min(fg.shape[1], nom1 + BUSCA + 1))
                cutL = min(cands_l, key=lambda c: perfil[c] + 0.15 * abs(c - nom0))
                cutR = min(cands_r, key=lambda c: perfil[c] + 0.15 * abs(c - nom1))
                fgc = fg.copy()
                fgc[:, :cutL] = False
                fgc[:, cutR:] = False
                lab, n = label_components(fgc)
                quitados = 0
                foraneo = 0
                tocado = False
                diff = np.abs(win - bg).sum(axis=2)
                for c in range(1, n + 1):
                    ys_, xs_ = np.where(lab == c)
                    area = len(ys_)
                    toca_l = xs_.min() == cutL
                    toca_r = xs_.max() == cutR - 1
                    if area < 12:
                        fgc[lab == c] = False
                        continue
                    # restos de borde de panel: manchas pálidas (poco contraste) o líneas planas
                    if diff[ys_, xs_].max() < 90 and area < 600:
                        fgc[lab == c] = False
                        quitados += area
                        continue
                    if (ys_.max() - ys_.min() + 1) <= 7 and (xs_.max() - xs_.min() + 1) >= 40:
                        fgc[lab == c] = False
                        quitados += area
                        continue
                    if area >= 100 and not (nom0 <= xs_.mean() < nom1):
                        foraneo += area
                    if (toca_l and xs_.max() - cutL < 12 and area < 500) or (toca_r and cutR - xs_.min() < 12 and area < 500):
                        fgc[lab == c] = False
                        quitados += area
                        continue
                    if area > 1500 and (toca_l or toca_r):
                        tocado = True
                celdas[(NAMES[k], i)] = dict(
                    win=win, fg=fgc, bg=bg, nom0=nom0, nom1=nom1, cutL=cutL, cutR=cutR,
                    contacto=(int(perfil[cutL]), int(perfil[cutR])), sliver=quitados, tocado=tocado, foraneo=foraneo,
                )
            k += 1
    return celdas


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
    return float(np.abs(rec - win).sum(axis=2)[valid].mean() / 3)


def contraste(win, fg, kk, eje):
    errs = []
    for p in np.arange(0, kk, 0.5):
        if eje == "x":
            errs.append(grid_error(win, fg, kk, 1.0, p, 0))
        else:
            errs.append(grid_error(win, fg, 1.0, kk, 0, p))
    return (max(errs) - min(errs)) / max(1e-6, max(errs))


def bbox_union(fgs):
    u = np.zeros(fgs[0].shape, bool)
    for f in fgs:
        u |= f
    ys, xs = np.where(u)
    return ys.min(), ys.max() + 1, xs.min(), xs.max() + 1


def muestrear(win, fg, kx, ky, px, py, j0, j1, i0, i1, modo="centro"):
    """Un píxel nativo por bloque (j,i) de la rejilla (kx,ky,px,py). modo: centro (mediana del 60 % central), area (media)."""
    h, w = j1 - j0, i1 - i0
    rgb = np.zeros((h, w, 3), np.uint8)
    al = np.zeros((h, w), bool)
    H, W = fg.shape
    for j in range(j0, j1):
        ya = int(round(py + j * ky))
        yb = int(round(py + (j + 1) * ky))
        if yb <= ya or ya >= H or yb <= 0:
            continue
        ya, yb = max(0, ya), min(H, yb)
        for i in range(i0, i1):
            xa = int(round(px + i * kx))
            xb = int(round(px + (i + 1) * kx))
            if xb <= xa or xa >= W or xb <= 0:
                continue
            xa, xb = max(0, xa), min(W, xb)
            m = fg[ya:yb, xa:xb]
            if m.size == 0 or m.mean() < 0.5:
                continue
            blk = win[ya:yb, xa:xb]
            if modo == "borde":
                # el trazo oscuro del dibujo (4,2 px) es más fino que la celda (4,75): si el bloque tiene bastante trazo,
                # se toma el color oscuro real del propio bloque, para que el contorno no se parta
                oscuros = blk[m & (blk.sum(axis=2) < 150)]
                if len(oscuros) >= 0.3 * m.sum():
                    al[j - j0, i - i0] = True
                    rgb[j - j0, i - i0] = np.clip(np.median(oscuros, axis=0), 0, 255).astype(np.uint8)
                    continue
            if modo == "area":
                c = blk[m].mean(axis=0)
            else:
                dy = max(1, (yb - ya) // 5)
                dx = max(1, (xb - xa) // 5)
                core = blk[dy:max(dy + 1, (yb - ya) - dy), dx:max(dx + 1, (xb - xa) - dx)]
                cm = m[dy:max(dy + 1, (yb - ya) - dy), dx:max(dx + 1, (xb - xa) - dx)]
                px_ = core[cm] if cm.any() else blk[m]
                c = np.median(px_, axis=0)
            al[j - j0, i - i0] = True
            rgb[j - j0, i - i0] = np.clip(c, 0, 255).astype(np.uint8)
    return rgb, al


def error_reconstruccion(win, fg, rgb, al, kx, ky, px, py, j0, i0):
    """Vuelve a subir el sprite nativo al tamaño original con vecino más cercano y mide el error en el primer plano."""
    H, W = fg.shape
    xx = np.arange(W)
    yy = np.arange(H)
    ix = np.floor((xx - px) / kx).astype(int) - i0
    iy = np.floor((yy - py) / ky).astype(int) - j0
    okx = (ix >= 0) & (ix < rgb.shape[1])
    oky = (iy >= 0) & (iy < rgb.shape[0])
    ixc = np.clip(ix, 0, rgb.shape[1] - 1)
    iyc = np.clip(iy, 0, rgb.shape[0] - 1)
    rec = rgb[np.ix_(iyc, ixc)].astype(int)
    a = al[np.ix_(iyc, ixc)] & oky[:, None] & okx[None, :]
    m = fg & a
    return float(np.abs(rec - win).sum(axis=2)[m].mean() / 3), float(m.sum() / max(1, fg.sum()))


def grises(rgb, al):
    r = rgb.astype(int)
    lum = r.sum(axis=2) / 3
    sat = r.max(axis=2) - r.min(axis=2)
    return int(((sat < 22) & (lum > 70) & (lum < 175) & al).sum())
