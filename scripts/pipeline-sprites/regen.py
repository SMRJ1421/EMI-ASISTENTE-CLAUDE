import pickle
import emi_lib as L
c = L.cargar_celdas()
pickle.dump(c, open("diag/celdas.pkl", "wb"))
print("foraneos:", [(k, v["foraneo"]) for k, v in c.items() if v["foraneo"] > 0])
print("restos eliminados (px):", sum(v["sliver"] for v in c.values()))
