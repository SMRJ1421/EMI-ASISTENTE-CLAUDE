# Recorte por paneles con fronteras compartidas: los 4 fotogramas de un panel forman una partición exacta (sin píxeles en dos fotogramas).
import collections
import numpy as np
import emi_lib as L

BUSCA2 = 34


def cargar_celdas_v2():
    A = L.A
    celdas = {}
    informe = {"fronteras": []}
    k = 0
    for (y0, y1) in L.ROWS:
        for (x0, x1) in L.COLS:
            fy1 = y1 - 40
            ix0, ix1 = x0 + 8, x1 - 8
            pw = (ix1 - ix0) / 4
            ya, yb = y0 + 10, fy1
            fig = A[ya:yb, ix0:ix1]
            bg = np.array(collections.Counter(map(tuple, fig.reshape(-1, 3)[::7])).most_common(1)[0][0])
            # panel entero con unos píxeles de margen de fondo
            pad = L.MARG
            H = yb - ya
            panel = np.zeros((H, (ix1 - ix0) + 2 * pad, 3), int) + bg
            panel[:, pad:pad + (ix1 - ix0)] = A[ya:yb, ix0:ix1]
            fg = L.flood_bg(panel, bg)
            for r in list(range(min(14, H))) + list(range(max(0, H - 18), H)):
                if fg[r].mean() > 0.8:
                    fg[r] = False
            perfil = fg.sum(axis=0)
            nominal = [pad + i * pw for i in range(5)]
            b = [pad, None, None, None, pad + (ix1 - ix0)]
            for kk in (1, 2, 3):
                c0 = int(round(nominal[kk]))
                cand = range(c0 - BUSCA2, c0 + BUSCA2 + 1)
                b[kk] = min(cand, key=lambda c: perfil[c] + 0.15 * abs(c - c0))
            informe["fronteras"].append((L.NAMES[k], [int(b[kk] - nominal[kk]) for kk in (1, 2, 3)], [int(perfil[b[kk]]) for kk in (1, 2, 3)]))
            for i in range(4):
                xs = int(round(ix0 + i * pw))
                wcell = int(round(pw))
                X0 = xs - L.MARG
                width = wcell + 2 * L.MARG
                # ventana ancha (coordenadas de la celda) tomada del panel
                win = np.zeros((H, width, 3), int) + bg
                msk = np.zeros((H, width), bool)
                for xr in range(width):
                    xp = (X0 + xr) - ix0 + pad            # columna en el panel con margen
                    if 0 <= xp < panel.shape[1]:
                        win[:, xr] = panel[:, xp]
                        msk[:, xr] = fg[:, xp] & (xp >= b[i]) & (xp < b[i + 1])
                off = (xs - L.MARG) - ix0 + pad            # columna del panel que corresponde a la columna 0 de la ventana
                cutL, cutR = int(b[i] - off), int(b[i + 1] - off)
                cutL = max(0, cutL)
                cutR = min(width, cutR)
                lab, n = L.label_components(msk)
                quitados = 0
                tocado = False
                for c in range(1, n + 1):
                    ys_, xs_ = np.where(lab == c)
                    area = len(ys_)
                    drop = False
                    if area < 12:
                        drop = True
                    if not drop:
                        d_ = np.abs(win[ys_, xs_] - bg).sum(axis=1).max()
                        if d_ < 70 and area < 250:
                            drop = True
                        elif (ys_.max() - ys_.min() + 1) <= 7 and (xs_.max() - xs_.min() + 1) >= 90:
                            drop = True
                    if drop:
                        msk[lab == c] = False
                        quitados += area
                        continue
                    toca_l = xs_.min() == cutL and i > 0
                    toca_r = xs_.max() == cutR - 1 and i < 3
                    if area > 1500 and (toca_l or toca_r):
                        tocado = True
                celdas[(L.NAMES[k], i)] = dict(
                    win=win, fg=msk, bg=bg, nom0=L.MARG, nom1=L.MARG + wcell, cutL=cutL, cutR=cutR,
                    contacto=(int(perfil[b[i]]) if i > 0 else 0, int(perfil[b[i + 1]]) if i < 3 else 0),
                    sliver=quitados, tocado=tocado, foraneo=0, xs=xs,
                )
            k += 1
    return celdas, informe


def verificar_particion(celdas):
    """Comprueba que ningún píxel de la hoja pertenece a dos fotogramas del mismo panel."""
    malos = []
    for n in L.NAMES:
        for i in range(3):
            a = celdas[(n, i)]
            b = celdas[(n, i + 1)]
            # columnas absolutas respecto a la ventana de a: la ventana de b empieza (xs_b - xs_a) más a la derecha
            delta = b["xs"] - a["xs"]
            solape = 0
            for xr in range(a["fg"].shape[1]):
                xb = xr - delta
                if 0 <= xb < b["fg"].shape[1]:
                    solape += int((a["fg"][:, xr] & b["fg"][:, xb]).sum())
            if solape:
                malos.append((n, i, solape))
    return malos
