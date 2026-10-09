# Pipeline corregido de Emi: sprites nativos, mini por vecino más cercano, paleta, validación y comparativas.
import json
import pickle
import sys
import numpy as np
from PIL import Image, ImageDraw
import emi_lib as L
import emi_lib2 as L2

VARIANTE = sys.argv[1] if len(sys.argv) > 1 else "centro"   # centro (V1) o area (V3)
NCOLORES = 88
ALFABETO = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!#$%&*+,-:;<=>?@^_~()[]{}|"
out = open("diag/informe_correccion_final.txt", "w", encoding="utf-8")


def P(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.write(s + "\n")


par = pickle.load(open("diag/params5.pkl", "rb"))
kx, ky, fases = par["kx"], par["ky"], par["fases"]
celdas = pickle.load(open('diag/celdas.pkl', 'rb'))
P(f"rejilla global kx={kx:.2f} ky={ky:.2f} | muestreo: {VARIANTE}")

# ---------- sprites nativos por estado (los 4 fotogramas comparten rejilla y fase) ----------
nativos = {}
info = {}
for n in L.NAMES:
    px, py = fases[n]
    fgs = [celdas[(n, i)]["fg"] for i in range(4)]
    y0, y1, x0, x1 = L.bbox_union(fgs)
    j0, j1 = int(np.floor((y0 - py) / ky)), int(np.ceil((y1 - py) / ky))
    i0, i1 = int(np.floor((x0 - px) / kx)), int(np.ceil((x1 - px) / kx))
    fr = []
    for i in range(4):
        c = celdas[(n, i)]
        rgb, al = L.muestrear(c["win"], c["fg"], kx, ky, px, py, j0, j1, i0, i1, VARIANTE)
        fr.append((rgb, al))
        info[(n, i)] = (j0, i0, px, py)
    # recorte común a la unión de los 4
    u = np.zeros(fr[0][1].shape, bool)
    for _, a in fr:
        u |= a
    ys, xs = np.where(u)
    ya, yb, xa, xb = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    nativos[n] = [(r[ya:yb, xa:xb], a[ya:yb, xa:xb]) for r, a in fr]
    info[n] = (j0 + ya, i0 + xa)

# ---------- lienzo común (alto múltiplo de 4 para que la mitad siga siendo par) ----------
GW = max(nativos[n][0][1].shape[1] for n in L.NAMES)
GH = max(nativos[n][0][1].shape[0] for n in L.NAMES)
GW += GW % 2
GH += (-GH) % 4
P(f"lienzo común: {GW} x {GH} píxeles -> {GH // 2} filas de terminal en grande/normal, {GH // 4} en mini")
lienzo = {}
for n in L.NAMES:
    h, w = nativos[n][0][1].shape
    ox, oy = (GW - w) // 2, GH - h
    fr = []
    for rgb, al in nativos[n]:
        R = np.zeros((GH, GW, 3), np.uint8)
        Al = np.zeros((GH, GW), bool)
        R[oy:oy + h, ox:ox + w] = rgb
        Al[oy:oy + h, ox:ox + w] = al
        fr.append((R, Al))
    lienzo[n] = fr

# ---------- mini: vecino más cercano 1/2, con el desfase (0/1) que menos error da por estado ----------
def mitad(R, Al, oy, ox):
    return R[oy::2, ox::2][: GH // 2, : GW // 2], Al[oy::2, ox::2][: GH // 2, : GW // 2]


mini = {}
for n in L.NAMES:
    best = None
    for oy in (0, 1):
        for ox in (0, 1):
            e = 0.0
            for R, Al in lienzo[n]:
                r2, a2 = mitad(R, Al, oy, ox)
                up_r = np.repeat(np.repeat(r2, 2, axis=0), 2, axis=1)[:GH, :GW]
                up_a = np.repeat(np.repeat(a2, 2, axis=0), 2, axis=1)[:GH, :GW]
                e += np.abs(up_r.astype(int) - R.astype(int)).sum(axis=2)[Al & up_a].mean() / 3 + 60 * (Al ^ up_a).mean() * 100 / 100
            if best is None or e < best[0]:
                best = (e, oy, ox)
    mini[n] = [mitad(R, Al, best[1], best[2]) for R, Al in lienzo[n]]
mh, mw = mini[L.NAMES[0]][0][1].shape
P(f"mini: {mw} x {mh} píxeles")

# ---------- paleta ----------
cols = []
for n in L.NAMES:
    for tam in (lienzo, mini):
        for R, Al in tam[n]:
            cols.append(R[Al])
            sat = (R[Al].astype(int).max(axis=1) - R[Al].astype(int).min(axis=1)) > 110
            if sat.any():
                cols.extend([R[Al][sat]] * 5)   # los colores vivos y minoritarios (ojos, confeti) pesan más al elegir la paleta
allc = np.concatenate(cols)
strip = Image.fromarray(allc.reshape(1, -1, 3).astype(np.uint8), "RGB")
q = strip.quantize(colors=NCOLORES, method=Image.MEDIANCUT, dither=Image.NONE)
pal = np.array(q.getpalette()[:NCOLORES * 3]).reshape(-1, 3)
P(f"paleta: {len(pal)} colores (había 60)")


def idx(R):
    d = ((R[..., None, :].astype(int) - pal[None, None, :, :]) ** 2).sum(-1)
    return d.argmin(-1)


def filas(R, Al):
    ix = idx(R)
    return ["".join(ALFABETO[ix[y, x]] if Al[y, x] else "." for x in range(Al.shape[1])) for y in range(Al.shape[0])]


salida = {"paleta": ["#%02x%02x%02x" % tuple(int(v) for v in c) for c in pal], "alfabeto": ALFABETO, "sprites": {}, "tam": {"L": [GW, GH], "X": [mw, mh]}}
errq = []
for n in L.NAMES:
    salida["sprites"][n] = {"L": [filas(R, Al) for R, Al in lienzo[n]], "X": [filas(R, Al) for R, Al in mini[n]]}
    for R, Al in lienzo[n]:
        ix = idx(R)
        errq.append(np.abs(pal[ix].astype(int) - R.astype(int)).sum(axis=2)[Al].mean() / 3)
P(f"error medio de cuantización: {np.mean(errq):.1f}/255 (antes 6,1)")
json.dump(salida, open("diag/sprites_corregidos.json", "w"))

# ---------- VALIDACIÓN de los 48 fotogramas ----------
P("\n== VALIDACIÓN DE LOS 48 FOTOGRAMAS ==")
probs = []
solapados = []
cobs = []
for n in L.NAMES:
    for i in range(4):
        c = celdas[(n, i)]
        px, py = fases[n]
        j0, i0 = info[(n, i)][0], info[(n, i)][1]
        # completitud: cobertura del primer plano original tras subir el sprite nativo
        rgb, al = nativos[n][i]
        jj0, ii0 = info[n]
        e, cov = L.error_reconstruccion(c["win"], c["fg"], rgb, al, kx, ky, px, py, jj0, ii0)
        cobs.append(cov)
        if cov < 0.93:
            probs.append((n, i, "cobertura baja %.1f%%" % (cov * 100)))
        if c["tocado"]:
            solapados.append((n, i, c["contacto"]))
        if c["foraneo"] > 0:
            probs.append((n, i, "contaminación: %d px de otro sprite" % c["foraneo"]))
        R, Al = lienzo[n][i]
        lab, k = L.label_components(Al)
        # restos: manchas sueltas de menos de 4 píxeles nativos que no son efectos (se miran los colores muy pálidos)
        for m in range(1, k + 1):
            ys_, xs_ = np.where(lab == m)
            if len(ys_) <= 3:
                col = R[ys_, xs_].astype(int)
                if (np.abs(col - np.array([245, 230, 253])).sum(axis=1) < 90).all():
                    probs.append((n, i, "resto pálido suelto de %d px" % len(ys_)))
P("partición de los paneles (píxeles que pertenecen a dos fotogramas vecinos):", L2.verificar_particion(celdas) or "ninguno")
P(f"cobertura media del primer plano: {np.mean(cobs) * 100:.1f}% (mínima {np.min(cobs) * 100:.1f}%)")
P("fotogramas con sprites vecinos solapados (se separan por el punto de menor contacto):", len(solapados))
for sv in solapados:
    P("   ", sv)
P("problemas reales (contaminación, restos, cobertura baja):", len(probs))
for p in probs:
    P("   ", p)

# alineación: desviación del movimiento nativo frente al movimiento del original
P("\nalineación (desviación entre el movimiento del centro de masa original y el nativo, en píxeles nativos):")
peor = 0
for n in L.NAMES:
    orig = []
    nat = []
    for i in range(4):
        c = celdas[(n, i)]
        lab, k = L.label_components(c["fg"])
        masa = np.zeros(c["fg"].shape, bool)
        for m in range(1, k + 1):
            if (lab == m).sum() > 1500:
                masa |= lab == m
        ys_, xs_ = np.where(masa)
        orig.append((xs_.mean() / kx, ys_.max() / ky))
        R, Al = lienzo[n][i]
        cuerpo = [y for y in range(GH) if Al[y].sum() >= 8]
        cols_ = np.where(Al[min(cuerpo):max(cuerpo) + 1].sum(axis=0) >= 6)[0]
        nat.append(((cols_.min() + cols_.max()) / 2, max(cuerpo)))
    dx = max(abs((nat[i][0] - nat[0][0]) - (orig[i][0] - orig[0][0])) for i in range(4))
    dy = max(abs((nat[i][1] - nat[0][1]) - (orig[i][1] - orig[0][1])) for i in range(4))
    peor = max(peor, dx, dy)
    P(f"  {n:12s} desviación x {dx:.1f}  y {dy:.1f}")
P(f"desviación máxima: {peor:.1f} píxeles nativos")
out.close()


# ---------- comparativas antes / después ----------
def decodificar(filas_, paleta, alf):
    h, w = len(filas_), len(filas_[0])
    R = np.zeros((h, w, 3), np.uint8)
    Al = np.zeros((h, w), bool)
    for y, r in enumerate(filas_):
        for x, ch in enumerate(r):
            if ch != ".":
                R[y, x] = paleta[alf.index(ch)]
                Al[y, x] = True
    return R, Al


def sim_terminal(R, Al, celda=(8, 16)):
    cw, ch = celda
    h, w = Al.shape
    img = np.zeros((h // 2 * ch, w * cw, 3), np.uint8) + np.array([245, 230, 253], np.uint8)
    for r in range(h // 2):
        for x in range(w):
            for medio in (0, 1):
                y = r * 2 + medio
                if Al[y, x]:
                    img[r * ch + medio * (ch // 2): r * ch + (medio + 1) * (ch // 2), x * cw:(x + 1) * cw] = R[y, x]
    return Image.fromarray(img)


viejo = json.load(open("sprites3.json"))
pal_v = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in viejo["paleta"]])
alf_v = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
pal_n = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in salida["paleta"]])


def hoja(titulos, imgs, fn, alto=380):
    esc = [im.resize((max(1, int(im.size[0] * alto / im.size[1])), alto), Image.NEAREST) for im in imgs]
    W = sum(e.size[0] for e in esc) + 10 * (len(esc) + 1)
    sh = Image.new("RGB", (W, alto + 40), (30, 30, 36))
    dr = ImageDraw.Draw(sh)
    x = 10
    for e, t in zip(esc, titulos):
        sh.paste(e, (x, 30))
        dr.text((x, 8), t, fill=(255, 255, 255))
        x += e.size[0] + 10
    sh.save(fn)


for n in L.NAMES:
    for i in (0, 2):
        c = celdas[(n, i)]
        orig = c["win"].astype(np.uint8).copy()
        orig[~c["fg"]] = (245, 230, 253)
        Rv, Av = decodificar(viejo["sprites"][n]["L"][i], pal_v, alf_v)
        Rn, An = lienzo[n][i]
        Rq, Aq = decodificar(salida["sprites"][n]["L"][i], pal_n, ALFABETO)
        Rm, Am = decodificar(salida["sprites"][n]["X"][i], pal_n, ALFABETO)
        hoja(["original (sin vecinos)", "ANTES (K=4, ventana fija)", "DESPUÉS (rejilla real)", "DESPUÉS en terminal grande", "DESPUÉS mini 1/2"],
             [Image.fromarray(orig), sim_terminal(Rv, Av), sim_terminal(Rq, Aq), sim_terminal(Rq, Aq), sim_terminal(Rm, Am, (16, 32))],
             f"diag/antes_despues_{n}_{i}.png")
# contactos de 12 x 4
for etiqueta, fuente in (("L", lienzo), ):
    ancho = GW * 5
    alto = GH * 5
    sh = Image.new("RGB", (ancho * 8, alto * 6), (245, 230, 253))
    for k, n in enumerate(L.NAMES):
        for f in range(4):
            R, Al = fuente[n][f]
            t = np.dstack([R, (Al * 255).astype(np.uint8)])
            im = Image.fromarray(t, "RGBA").resize((ancho, alto), Image.NEAREST)
            sh.paste(im, ((((k % 2) * 4) + f) * ancho, (k // 2) * alto), im)
    sh.save("diag/contacto_corregido_L.png")
print("ok")
