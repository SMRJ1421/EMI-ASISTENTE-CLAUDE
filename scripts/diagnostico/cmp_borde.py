# ¿El contorno conserva mejor el original si el bloque con mucho trazo oscuro toma su color oscuro real?
import pickle
import numpy as np
import emi_lib as L

celdas = pickle.load(open("diag/celdas.pkl", "rb"))
par = pickle.load(open("diag/params5.pkl", "rb"))
kx = ky = par["kx"]
res = {"centro": [], "borde": []}
cont = {"centro": [], "borde": []}   # continuidad del contorno: píxeles oscuros con vecino oscuro (arriba/abajo/izq/der)
for n in L.NAMES:
    px, py = par["fases"][n]
    fgs = [celdas[(n, i)]["fg"] for i in range(4)]
    y0, y1, x0, x1 = L.bbox_union(fgs)
    j0, j1 = int(np.floor((y0 - py) / ky)), int(np.ceil((y1 - py) / ky))
    i0, i1 = int(np.floor((x0 - px) / kx)), int(np.ceil((x1 - px) / kx))
    for i in range(4):
        c = celdas[(n, i)]
        for modo in res:
            rgb, al = L.muestrear(c["win"], c["fg"], kx, ky, px, py, j0, j1, i0, i1, modo)
            e, _ = L.error_reconstruccion(c["win"], c["fg"], rgb, al, kx, ky, px, py, j0, i0)
            res[modo].append(e)
            osc = (rgb.astype(int).sum(axis=2) < 150) & al
            pad = np.pad(osc, 1)
            vec = pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
            aisl = (osc & ~vec).sum()
            cont[modo].append(aisl / max(1, osc.sum()))
for m in res:
    print(f"{m}: error medio {np.mean(res[m]):.1f}/255 | píxeles de contorno aislados (sin vecino oscuro) {np.mean(cont[m]) * 100:.1f}%")
