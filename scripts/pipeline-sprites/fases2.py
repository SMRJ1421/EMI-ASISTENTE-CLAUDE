import pickle
import numpy as np
import emi_lib as L
celdas = pickle.load(open("diag/celdas.pkl", "rb"))
par = pickle.load(open("diag/params5.pkl", "rb"))
kx = ky = 4.75
fases = {}
for n in L.NAMES:
    best = None
    for px in np.arange(0, kx, 0.25):
        for py in np.arange(0, ky, 0.25):
            e = sum(L.grid_error(celdas[(n, i)]["win"], celdas[(n, i)]["fg"], kx, ky, px, py) for i in range(4))
            if best is None or e < best[0]:
                best = (e, px, py)
    fases[n] = (best[1], best[2])
    print(n, "fase", best[1], best[2], "error", round(best[0] / 4, 1))
pickle.dump(dict(kx=kx, ky=ky, fases=fases), open("diag/params5.pkl", "wb"))
