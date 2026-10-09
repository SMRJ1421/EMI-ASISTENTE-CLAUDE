import pickle
import numpy as np
import emi_lib as L

celdas = L.cargar_celdas()
pickle.dump(celdas, open("diag/celdas.pkl", "wb"))
ks = [3.8, 4.0, 4.2, 4.4, 4.6, 4.75, 4.9, 5.1, 5.3, 5.6, 5.9, 6.2]
muestra = [(n, i) for n in L.NAMES for i in (0, 2)]
for eje in ("x", "y"):
    tot = np.zeros(len(ks))
    for key in muestra:
        c = celdas[key]
        tot += np.array([L.contraste(c["win"], c["fg"], kk, eje) for kk in ks])
    tot /= len(muestra)
    print("eje", eje, " ".join(f"{k}:{v * 100:.1f}" for k, v in zip(ks, tot)))
