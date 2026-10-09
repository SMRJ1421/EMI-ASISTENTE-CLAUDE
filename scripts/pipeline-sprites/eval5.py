# Evaluación: recorte corregido, cuadrícula real y comparación de las tres variantes de muestreo.
import pickle
import numpy as np
from PIL import Image, ImageDraw
import emi_lib as L

out = open("diag/informe_correccion_evaluacion.txt", "w", encoding="utf-8")


def P(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.write(s + "\n")


celdas = pickle.load(open('diag/celdas.pkl', 'rb'))
P("== RECORTE CORREGIDO (cortes en los huecos entre figuras) ==")
mov = [(k, c["cutL"] - c["nom0"], c["cutR"] - c["nom1"]) for k, c in celdas.items()]
P("desplazamiento del corte respecto a la celda nominal (px): máximo izq %d, der %d" % (max(abs(m[1]) for m in mov), max(abs(m[2]) for m in mov)))
con_contacto = [(k, c["contacto"], c["sliver"]) for k, c in celdas.items() if max(c["contacto"]) > 0]
P("cortes donde NO hay hueco limpio (px de figura cortados en la columna de corte) :", len(con_contacto), "de 48")
for k, cont, sl in con_contacto:
    P("   ", k, "contacto(izq,der)=", cont, "| sliver de vecino eliminado =", sl, "px")
P("fotogramas cuya figura propia sigue tocando el corte:", [k for k, c in celdas.items() if c["tocado"]])

# ---- cuadrícula: curva de contraste (medida aparte en curvas.py) ----
P("== CUADRÍCULA REAL (24 fotogramas, contraste de fase medio por periodo, en %) ==")
P("  eje x: 3.8:12.3 4.0:6.5 4.2:9.1 4.4:10.4 4.6:11.0 4.75:19.8 4.9:18.5 5.1:19.6 5.3:16.3 5.6:23.0 5.9:19.2 6.2:13.9")
P("  eje y: 3.8:12.0 4.0:9.8 4.2:11.6 4.4:12.9 4.6:13.8 4.75:17.9 4.9:16.1 5.1:11.7 5.3:13.3 5.6:12.6 5.9:13.6 6.2:14.5")
P("  grosor medio del contorno oscuro: horizontal 4,4 px, vertical 4,2 px (relación 1,05: píxel casi cuadrado)")
kx = ky = 4.75
P(f"  -> rejilla elegida: cuadrada, k={kx} px (único periodo con pico en los dos ejes; K=4 daba 6,5 % y 9,8 %)")

# ---- fase por estado (compartida por sus 4 fotogramas) ----
P("\n== FASE POR ESTADO (compartida por los 4 fotogramas, así no hay saltos entre ellos) ==")
fases = {}
for n in L.NAMES:
    best = None
    for px in np.arange(0, kx, 0.25):
        for py in np.arange(0, ky, 0.25):
            e = sum(L.grid_error(celdas[(n, i)]["win"], celdas[(n, i)]["fg"], kx, ky, px, py) for i in range(4))
            if best is None or e < best[0]:
                best = (e, px, py)
    fases[n] = (best[1], best[2])
    P(f"  {n:12s} fase=({best[1]:.2f}, {best[2]:.2f}) error medio {best[0] / 4:.1f}/255")

# ---- variantes ----
P("\n== VARIANTES DE MUESTREO (48 fotogramas) ==")
res = {"V1 rejilla global (centro, fase compartida)": [], "V2 rejilla por fotograma (centro)": [], "V3 sin rejilla (promedio de área 1/5)": []}
gris = {k: 0 for k in res}
cobert = {k: [] for k in res}
mapas = {}
for n in L.NAMES:
    fgs = [celdas[(n, i)]["fg"] for i in range(4)]
    y0, y1, x0, x1 = L.bbox_union(fgs)
    px, py = fases[n]
    j0, j1 = int(np.floor((y0 - py) / ky)), int(np.ceil((y1 - py) / ky))
    i0, i1 = int(np.floor((x0 - px) / kx)), int(np.ceil((x1 - px) / kx))
    for i in range(4):
        c = celdas[(n, i)]
        win, fg = c["win"], c["fg"]
        # V1
        rgb, al = L.muestrear(win, fg, kx, ky, px, py, j0, j1, i0, i1, "centro")
        e, cv = L.error_reconstruccion(win, fg, rgb, al, kx, ky, px, py, j0, i0)
        res["V1 rejilla global (centro, fase compartida)"].append(e)
        cobert["V1 rejilla global (centro, fase compartida)"].append(cv)
        gris["V1 rejilla global (centro, fase compartida)"] += L.grises(rgb, al) if n != "leyendo" else 0
        mapas[(n, i, 1)] = (rgb, al, (kx, ky, px, py, j0, i0))
        # V2: busca k y fase propios cerca de la rejilla global
        best = None
        ys_, xs_ = np.where(fg)
        for dkx in (-0.2, 0, 0.2):
            for dky in (-0.2, 0, 0.2):
                for ppx in np.arange(0, kx + dkx, 0.75):
                    for ppy in np.arange(0, ky + dky, 0.75):
                        ee = L.grid_error(win, fg, kx + dkx, ky + dky, ppx, ppy)
                        if best is None or ee < best[0]:
                            best = (ee, kx + dkx, ky + dky, ppx, ppy)
        _, k2x, k2y, p2x, p2y = best
        jj0, jj1 = int(np.floor((ys_.min() - p2y) / k2y)), int(np.ceil((ys_.max() + 1 - p2y) / k2y))
        ii0, ii1 = int(np.floor((xs_.min() - p2x) / k2x)), int(np.ceil((xs_.max() + 1 - p2x) / k2x))
        rgb2, al2 = L.muestrear(win, fg, k2x, k2y, p2x, p2y, jj0, jj1, ii0, ii1, "centro")
        e2, cv2 = L.error_reconstruccion(win, fg, rgb2, al2, k2x, k2y, p2x, p2y, jj0, ii0)
        res["V2 rejilla por fotograma (centro)"].append(e2)
        cobert["V2 rejilla por fotograma (centro)"].append(cv2)
        gris["V2 rejilla por fotograma (centro)"] += L.grises(rgb2, al2) if n != "leyendo" else 0
        mapas[(n, i, 2)] = (rgb2, al2, (k2x, k2y, p2x, p2y, jj0, ii0))
        # V3: promedio de área con la rejilla global (equivale a reducir 1/k sin detectar bordes de píxel)
        rgb3, al3 = L.muestrear(win, fg, kx, ky, px, py, j0, j1, i0, i1, "area")
        e3, cv3 = L.error_reconstruccion(win, fg, rgb3, al3, kx, ky, px, py, j0, i0)
        res["V3 sin rejilla (promedio de área 1/5)"].append(e3)
        cobert["V3 sin rejilla (promedio de área 1/5)"].append(cv3)
        gris["V3 sin rejilla (promedio de área 1/5)"] += L.grises(rgb3, al3) if n != "leyendo" else 0
        mapas[(n, i, 3)] = (rgb3, al3, (kx, ky, px, py, j0, i0))
for k, v in res.items():
    P(f"  {k}: error medio {np.mean(v):.1f}/255 | cobertura {np.mean(cobert[k]) * 100:.1f}% | píxeles grises sueltos {gris[k]}")
pickle.dump(dict(kx=kx, ky=ky, fases=fases), open("diag/params5.pkl", "wb"))


def mostrar(rgb, al, escala):
    o = np.zeros((*rgb.shape[:2], 3), np.uint8) + np.array([245, 230, 253], np.uint8)
    o[al] = rgb[al]
    return Image.fromarray(o).resize((rgb.shape[1] * escala, rgb.shape[0] * escala), Image.NEAREST)


for n, i in (("nueva", 1), ("duerme", 1), ("terminado", 1), ("escribiendo", 2)):
    c = celdas[(n, i)]
    orig = c["win"].astype(np.uint8).copy()
    orig[~c["fg"]] = (245, 230, 253)
    ims = [Image.fromarray(orig)] + [mostrar(*mapas[(n, i, v)][:2], 1) for v in (1, 2, 3)]
    labs = ["original recortado (sin vecinos)", "V1 rejilla global", "V2 rejilla por fotograma", "V3 promedio de área"]
    th = 400
    esc = [im.resize((max(1, int(im.size[0] * th / im.size[1])), th), Image.NEAREST) for im in ims]
    W = sum(e.size[0] for e in esc) + 10 * (len(esc) + 1)
    sheet = Image.new("RGB", (W, th + 40), (30, 30, 36))
    dr = ImageDraw.Draw(sheet)
    x = 10
    for e, lab in zip(esc, labs):
        sheet.paste(e, (x, 30))
        dr.text((x, 8), lab, fill=(255, 255, 255))
        x += e.size[0] + 10
    sheet.save(f"diag/variantes_{n}_{i}.png")
out.close()
print("ok")
