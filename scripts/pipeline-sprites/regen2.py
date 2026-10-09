import pickle
import emi_lib as L
import emi_lib2 as L2
c, inf = L2.cargar_celdas_v2()
pickle.dump(c, open("diag/celdas.pkl", "wb"))
malos = L2.verificar_particion(c)
print("pares de fotogramas vecinos con píxeles compartidos:", malos if malos else "ninguno")
for n, desp, perf in inf["fronteras"]:
    print(f"  {n:12s} frontera vs nominal (px) {desp} | contacto en la frontera (px) {perf}")
print("restos eliminados:", sum(v["sliver"] for v in c.values()), "px | figuras solapadas:", [(k) for k, v in c.items() if v["tocado"]])
