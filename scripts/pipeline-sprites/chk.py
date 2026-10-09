import json, pickle
import numpy as np
import emi_lib as L
d = json.load(open("diag/sprites_corregidos.json"))
celdas = pickle.load(open("diag/celdas.pkl", "rb"))
for n in ("pensando", "responde", "terminado", "baile"):
    nat, ori, top = [], [], []
    for i in range(4):
        rows = d["sprites"][n]["L"][i]
        al = np.array([[c != "." for c in r] for r in rows])
        cuerpo = [y for y in range(al.shape[0]) if al[y].sum() >= 8]
        nat.append((min(cuerpo), max(cuerpo)))
        fg = celdas[(n, i)]["fg"]
        lab, k = L.label_components(fg)
        ys = np.concatenate([np.where(lab == m)[0] for m in range(1, k + 1) if (lab == m).sum() > 1500])
        ori.append((round(ys.min() / 4.75, 1), round(ys.max() / 4.75, 1)))
    print(n, "nativo (arriba,suelo):", nat, "| original en px nativos:", ori)
