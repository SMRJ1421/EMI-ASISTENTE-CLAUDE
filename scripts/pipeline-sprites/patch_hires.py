lines = open("hires.py", encoding="utf-8").read().split("\n")

# --- paleta con semillas por tono (líneas 121-132) ---
pal_nuevo = '''    cols = []
    for n in L.NAMES:
        for i in range(4):
            rgb, al = datos[(nombre, n, i)]
            cols.append(rgb[al])
    allc = np.concatenate(cols).astype(np.uint8)
    pal = hacer_paleta(allc, NC)
    paletas[nombre] = pal'''.split("\n")
lines[120:132] = pal_nuevo   # índices 120..131 = líneas 121..132

# --- detalle nuevo vectorizado (líneas 86-108) ---
det_nuevo = '''            # cuánto detalle nuevo hay frente al sprite actual: muestras cuyo color no coincide con el píxel nativo que las contiene
            nj, ni = int(Hh / K0) + 2, int(Ww / K0) + 2
            nat_rgb, nat_al = L.muestrear(c["win"], c["fg"], K0, K0, px, py, 0, nj, 0, ni, "centro")
            ys_, xs_ = np.where(al)
            if len(ys_):
                gj = np.floor((Y0 + (ys_ + 0.5) * k - py) / K0).astype(int)
                gi = np.floor((x0 + (xs_ + 0.5) * k - px) / K0).astype(int)
                ok = (gj >= 0) & (gj < nj) & (gi >= 0) & (gi < ni)
                ok[ok] = nat_al[gj[ok], gi[ok]]
                if ok.any():
                    d = np.abs(rgb[ys_[ok], xs_[ok]].astype(int) - nat_rgb[gj[ok], gi[ok]].astype(int)).sum(axis=1) / 3
                    dif[nombre].append(float((d > 30).mean()))'''.split("\n")
lines[85:108] = det_nuevo    # líneas 86..108

texto = "\n".join(lines)
funcion = '''
import colorsys


def hacer_paleta(px, nc):
    """Paleta con colores reales del dibujo: 3 semillas por cada tono vivo (para que ojos y confeti no se fundan con otros verdes
    o azules) y el resto por corte de medianas sobre el resto de píxeles."""
    p = px.astype(int)
    sat = (p.max(axis=1) - p.min(axis=1)) > 110
    semillas = []
    vivos = px[sat]
    if len(vivos):
        hsv = np.array([colorsys.rgb_to_hsv(*(c / 255.0)) for c in vivos[:: max(1, len(vivos) // 20000)]])
        mues = vivos[:: max(1, len(vivos) // 20000)]
        h = hsv[:, 0] * 360
        for lo, hi in ((0, 20), (340, 361), (20, 45), (45, 70), (70, 170), (170, 200), (200, 260), (260, 340)):
            sel = mues[(h >= lo) & (h < hi)]
            if len(sel) >= 15:
                qq = Image.fromarray(sel.reshape(1, -1, 3).astype(np.uint8), "RGB").quantize(colors=3, method=Image.MEDIANCUT, dither=Image.NONE)
                semillas.extend(np.array(qq.getpalette()[:9]).reshape(-1, 3).tolist())
    resto = px[~sat]
    n_resto = max(8, nc - len(semillas))
    qq = Image.fromarray(resto.reshape(1, -1, 3).astype(np.uint8), "RGB").quantize(colors=n_resto, method=Image.MEDIANCUT, dither=Image.NONE)
    base = np.array(qq.getpalette()[:n_resto * 3]).reshape(-1, 3)
    return np.vstack([np.array(semillas).reshape(-1, 3), base])[:nc]

'''
texto = texto.replace("# ---- paletas y límite de pares de colores del Raster ----", funcion + "# ---- paletas y límite de pares de colores del Raster ----", 1)
open("hires.py", "w", encoding="utf-8").write(texto)
print("parcheado")
