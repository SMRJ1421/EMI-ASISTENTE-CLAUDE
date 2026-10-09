# Etapa 5: alineación entre fotogramas (¿se mueve la figura de un fotograma a otro más de lo que se mueve en el original?)
import numpy as np
from PIL import Image

FL = np.load("frames_L.npy", allow_pickle=True).item()
names = ["nueva", "pensando", "responde", "leyendo", "escribiendo", "necesita", "falla", "para", "terminado", "baile", "hula", "duerme"]
out = open("diag/informe_etapa_5.txt", "w", encoding="utf-8")


def P(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out.write(s + "\n")


P("== ETAPA 5: alineación en el lienzo común (28 x 48) ==")
P("estado: fila del suelo (último píxel opaco del cuerpo) y columna central por fotograma; salto = diferencia máxima entre fotogramas")
peor = []
for n in names:
    filas, centros = [], []
    for rgb, al in FL[n]:
        ys, xs = np.where(al > 0)
        # el cuerpo: ignoramos los efectos sueltos tomando las filas donde hay al menos 8 píxeles opacos
        cuerpo = [y for y in range(al.shape[0]) if (al[y] > 0).sum() >= 8]
        filas.append(max(cuerpo))
        cols_cuerpo = np.where((al[min(cuerpo):max(cuerpo) + 1] > 0).sum(axis=0) >= 6)[0]
        centros.append(round(float((cols_cuerpo.min() + cols_cuerpo.max()) / 2), 1))
    sy = max(filas) - min(filas)
    sx = max(centros) - min(centros)
    peor.append((sy, sx, n))
    P(f"  {n:12s} suelo={filas} (salto {sy}) | centro x={centros} (salto {sx})")
P("saltos verticales >=2 px:", [(n, sy) for sy, sx, n in peor if sy >= 2])
P("saltos horizontales >=2 px:", [(n, sx) for sy, sx, n in peor if sx >= 2])
out.close()
