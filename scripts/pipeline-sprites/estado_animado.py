"""Estado animado (nueva | pensando): PNG de 1254x1254 -> variantes de sprite para el laboratorio (no toca mod\\).

Uso:  python scripts\\pipeline-sprites\\estado_animado.py [nueva|pensando]
Entrada: arte\\<carpeta del estado>\\*.png (solo lectura; copia en respaldos\\).
Salida:  laboratorio\\hooks\\<estado>.ts (datos) y datos-laboratorio\\<estado>\\* (informe y vistas previas).
Solo Pillow + numpy. Muestreo siempre vecino más cercano (sin mezclar colores).
"""
import json
import re
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parents[2]
# estado -> carpeta de PNG, qué hay de fondo («alfa»: ya viene transparente; «negro»: fondo opaco casi negro que se quita desde el borde),
# archivo de datos, nombre de la constante y de qué estado del mod se toma la comparación.
ESTADOS = {
    'nueva': dict(entrada='Emi-Animacion-Conversacion_Nueva', patron='frame-0*.png', fondo='alfa', salida='conversacion-nueva', ts='conversacion.ts', const='CONV', titulo='Conversación nueva'),
    'pensando': dict(entrada='EMI CLAUDE PENSANDO', patron='*.png', fondo='alfa', salida='pensando', ts='pensando.ts', const='PENS', titulo='Pensando'),
    'hula': dict(entrada='Emi-Animacion-pensando-de-guardia-hula', patron='*.png', fondo='alfa', salida='hula', ts='hula.ts', const='HULA', titulo='De guardia: hula'),
}
ESTADO = sys.argv[1] if len(sys.argv) > 1 else 'nueva'
CFG = ESTADOS[ESTADO]
ENTRADA = RAIZ / 'arte' / CFG['entrada']
SALIDA = RAIZ / 'datos-laboratorio' / CFG['salida']
TS = RAIZ / 'laboratorio' / 'hooks' / CFG['ts']
LADO = 1254
ALFABETO = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!#$%&*+,-:;<=>?@^_~()[]{}|'
CUENTA = '0123456789abcdefghijklmnopqrstuvwxyz'
TARJETA = (0xF5, 0xE6, 0xFD)
SALIDA.mkdir(parents=True, exist_ok=True)

informe: dict = {}

# ---------- 1. Cargar y comprobar ----------
ARCHIVOS = sorted(ENTRADA.glob(CFG['patron']))


def quitar_fondo_negro(rgb: np.ndarray, tope: int = 45) -> np.ndarray:
    """RGBA: el negro casi puro (canal máximo <= tope) conectado con el borde pasa a transparente; el negro de dentro (ojos, bocas) se queda."""
    alto, ancho = rgb.shape[:2]
    oscuro = rgb.max(-1) <= tope
    fondo = np.zeros_like(oscuro)
    cola = deque([(y, x) for y in (0, alto - 1) for x in range(ancho)] + [(y, x) for x in (0, ancho - 1) for y in range(alto)])
    while cola:
        y, x = cola.popleft()
        if 0 <= y < alto and 0 <= x < ancho and oscuro[y, x] and not fondo[y, x]:
            fondo[y, x] = True
            cola.extend(((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)))
    return np.dstack([rgb, np.where(fondo, 0, 255).astype(np.uint8)])


def cargar(archivo: Path) -> np.ndarray:
    im = Image.open(archivo)
    return quitar_fondo_negro(np.array(im.convert('RGB'))) if CFG['fondo'] == 'negro' else np.array(im.convert('RGBA'))


frames = [cargar(a) for a in ARCHIVOS]
N = len(frames)
informe['estado'] = ESTADO
informe['archivos'] = [a.name for a in ARCHIVOS]
assert all(f.shape == (LADO, LADO, 4) for f in frames)
alfa_valores = sorted({int(v) for f in frames for v in np.unique(f[..., 3])})
informe['transparencia'] = {
    'alfa_distintos': len(alfa_valores),
    'alfa_min_max': [alfa_valores[0], alfa_valores[-1]],
    'pixeles_con_alfa_parcial': [int(((f[..., 3] > 0) & (f[..., 3] < 255)).sum()) for f in frames],
    'opaco_por_ciento': [round(float((f[..., 3] > 0).mean() * 100), 1) for f in frames],
    'esquinas_transparentes': all(int(f[0, 0, 3]) == 0 and int(f[-1, -1, 3]) == 0 for f in frames),
}
informe['diferencias_con_el_anterior'] = [int((frames[i][..., :4] != frames[i - 1][..., :4]).any(-1).sum()) for i in range(1, N)]
informe['fotogramas_identicos'] = sum(1 for i in range(N) for j in range(i) if (frames[i] == frames[j]).all())


def limpiar(f: np.ndarray, minimo: int = 250):
    """Alfa binario (>=128) y sin motas: quita las piezas sueltas de menos de `minimo` píxeles (el punto rojo mide ~1000)."""
    dentro = f[..., 3] >= 128
    alto, ancho = dentro.shape
    visto = np.zeros_like(dentro)
    sal = np.zeros_like(dentro)
    quitadas = 0
    for y0, x0 in zip(*np.where(dentro)):
        if visto[y0, x0]:
            continue
        visto[y0, x0] = True
        pieza = [(y0, x0)]
        cola = deque(pieza)
        while cola:
            y, x = cola.popleft()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < alto and 0 <= xx < ancho and dentro[yy, xx] and not visto[yy, xx]:
                    visto[yy, xx] = True
                    cola.append((yy, xx))
                    pieza.append((yy, xx))
        if len(pieza) >= minimo:
            ys, xs = zip(*pieza)
            sal[list(ys), list(xs)] = True
        else:
            quitadas += 1
    g = f.copy()
    g[..., 3] = np.where(sal, 255, 0)
    return g, quitadas


limpios = [limpiar(f) for f in frames]
frames = [g for g, _ in limpios]
informe['motas_eliminadas_por_fotograma'] = [q for _, q in limpios]


def componente_principal(alfa: np.ndarray, paso: int = 3) -> np.ndarray:
    """Máscara (a 1/paso) de la mayor pieza conexa: el cuerpo, sin chispas ni el punto rojo."""
    s = alfa[::paso, ::paso]
    alto, ancho = s.shape
    etiqueta = np.zeros((alto, ancho), np.int32)
    tallas = [0]
    n = 0
    for y0, x0 in zip(*np.where(s)):
        if etiqueta[y0, x0]:
            continue
        n += 1
        etiqueta[y0, x0] = n
        cola = deque([(y0, x0)])
        c = 0
        while cola:
            y, x = cola.popleft()
            c += 1
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < alto and 0 <= xx < ancho and s[yy, xx] and not etiqueta[yy, xx]:
                    etiqueta[yy, xx] = n
                    cola.append((yy, xx))
        tallas.append(c)
    return etiqueta == (int(np.argmax(tallas[1:])) + 1)


masks3 = [componente_principal(f[..., 3] > 0, 3) for f in frames]  # 418 x 418


def escalar(m: np.ndarray, s: float) -> np.ndarray:
    n = max(1, round(m.shape[0] * s))
    return np.array(Image.fromarray(m.astype(np.uint8) * 255).resize((n, n), Image.NEAREST)) > 0


def iou_con(ref: np.ndarray, m: np.ndarray, s: float, ox: int, oy: int) -> float:
    """IoU entre `ref` y `m` escalada por s (desde el origen) y desplazada (ox, oy)."""
    ms = escalar(m, s)
    lienzo = np.zeros_like(ref)
    h, w = ref.shape
    y0, x0 = max(oy, 0), max(ox, 0)
    y1, x1 = min(oy + ms.shape[0], h), min(ox + ms.shape[1], w)
    if y1 <= y0 or x1 <= x0:
        return 0.0
    lienzo[y0:y1, x0:x1] = ms[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    union = np.logical_or(ref, lienzo).sum()
    return float(np.logical_and(ref, lienzo).sum() / union) if union else 0.0


def correlacion_gruesa(ref: np.ndarray, m: np.ndarray, s: float):
    """Mejor desplazamiento por FFT a 1/6 de la resolución (los parámetros devueltos van en unidades de 1/3)."""
    r = ref[::2, ::2]
    ms = escalar(m[::2, ::2], s)
    n = 512
    a = np.zeros((n, n))
    b = np.zeros((n, n))
    a[128:128 + r.shape[0], 128:128 + r.shape[1]] = r
    b[:ms.shape[0], :ms.shape[1]] = ms
    corr = np.fft.irfft2(np.fft.rfft2(a) * np.conj(np.fft.rfft2(b)), s=(n, n))
    iy, ix = np.unravel_index(int(np.argmax(corr)), corr.shape)
    iy = iy - n if iy > n // 2 else iy
    ix = ix - n if ix > n // 2 else ix
    # el desplazamiento (ix, iy) es de `b` sobre `a` con a colocada en 128: restamos ese margen y pasamos a unidades de 1/3
    return (ix - 128) * 2, (iy - 128) * 2, float(corr.max() / (r.sum() + ms.sum() - corr.max()))


ref = masks3[0]
ajustes = [{'s': 1.0, 'ox': 0.0, 'oy': 0.0, 'iou': 1.0, 'iou_sin_ajustar': 1.0}]  # ox, oy en píxeles del PNG: ref = s*q + o
for i in range(1, N):
    m = masks3[i]
    mejor = max(((correlacion_gruesa(ref, m, s) + (s,)) for s in np.arange(0.85, 1.201, 0.01)), key=lambda t: t[2])
    ox0, oy0, _, s0 = mejor
    cand = []
    for s in np.arange(s0 - 0.015, s0 + 0.0151, 0.005):
        for oy in range(int(oy0) - 6, int(oy0) + 7):
            for ox in range(int(ox0) - 6, int(ox0) + 7):
                cand.append((iou_con(ref, m, float(s), ox, oy), float(s), ox, oy))
    iou, s, ox, oy = max(cand)
    ajustes.append({'s': round(s, 3), 'ox': ox * 3, 'oy': oy * 3, 'iou': round(iou, 4), 'iou_sin_ajustar': round(iou_con(ref, m, 1.0, 0, 0), 4)})
informe['alineacion_contra_fotograma_1'] = ajustes

# ---------- 2. Muestreo vecino más cercano con la transformación ----------


def muestrear(i: int, ancho: int, alto: int, x0: float, y0: float, px: float, py: float, bloque: int = 1) -> np.ndarray:
    """Fotograma i, alineado al 1, en una rejilla ancho x alto cuyo píxel (0,0) cubre desde (x0,y0) del PNG de referencia con paso (px,py).
    Un solo punto por píxel (el centro): vecino más cercano. Con `bloque` = k > 1 (solo la versión diminuta de la banda), k x k puntos por
    píxel, uno por celda nativa: opaco si lo es al menos la mitad, con la media de los colores opacos. Devuelve RGBA uint8."""
    if bloque > 1:
        sub = [muestrear(i, ancho * bloque, alto * bloque, x0, y0, px / bloque, py / bloque) for _ in (0,)][0]
        cuadros = sub.reshape(alto, bloque, ancho, bloque, 4).transpose(0, 2, 1, 3, 4).reshape(alto, ancho, bloque * bloque, 4).astype(int)
        opaco = cuadros[..., 3] > 0
        n = opaco.sum(-1)
        media = (cuadros[..., :3] * opaco[..., None]).sum(2) // np.maximum(n, 1)[..., None]
        sal = np.zeros((alto, ancho, 4), np.uint8)
        sal[..., :3] = media
        sal[..., 3] = np.where(n * 2 >= bloque * bloque, 255, 0)
        sal[sal[..., 3] == 0] = 0
        return sal
    a = ajustes[i]
    rx = x0 + (np.arange(ancho) + 0.5) * px
    ry = y0 + (np.arange(alto) + 0.5) * py
    qx = np.floor((rx - a['ox']) / a['s']).astype(int)
    qy = np.floor((ry - a['oy']) / a['s']).astype(int)
    fuera_x = (qx < 0) | (qx >= LADO)
    fuera_y = (qy < 0) | (qy >= LADO)
    sal = frames[i][np.clip(qy, 0, LADO - 1)[:, None], np.clip(qx, 0, LADO - 1)[None, :]].copy()
    sal[fuera_y[:, None] | fuera_x[None, :]] = 0
    return sal


# ---------- 3. Rejilla nativa del arte (para la variante «nat») ----------


def periodo_y_fase(e: np.ndarray, lo: float, hi: float):
    idx = np.arange(len(e))
    mejor = (0.0, 0.0, 0.0)
    for p in np.arange(lo, hi, 0.05):
        z = (e * np.exp(-2j * np.pi * idx / p)).sum()
        v = abs(z) / e.sum()
        if v > mejor[0]:
            mejor = (v, float(p), float((np.angle(z) / (2 * np.pi)) * p % p) + 1)  # +1: la arista i separa los píxeles i e i+1
    return mejor


f0 = frames[0].astype(int)
ex = np.abs(np.diff(f0, axis=1)).sum(axis=(0, 2)).astype(float)
ey = np.abs(np.diff(f0, axis=0)).sum(axis=(1, 2)).astype(float)
_, px_nat, fx = periodo_y_fase(ex, 18.0, 21.0)
_, py_nat, fy = periodo_y_fase(ey, 18.0, 21.0)
informe['rejilla_nativa_px_del_PNG'] = {'ancho_de_celda': round(px_nat, 2), 'alto_de_celda': round(py_nat, 2), 'celdas': [round(LADO / px_nat, 1), round(LADO / py_nat, 1)]}

# ---------- 4. Variantes ----------
# Cuerpo de Emi en el PNG (fotograma 1 + alineación): caja de todos los fotogramas.
cajas = []
for i in range(N):
    ys, xs = np.where(masks3[i])
    a = ajustes[i]
    cajas.append((xs.min() * 3 * a['s'] + a['ox'], xs.max() * 3 * a['s'] + a['ox'], ys.min() * 3 * a['s'] + a['oy'], ys.max() * 3 * a['s'] + a['oy']))
cx = (min(c[0] for c in cajas) + max(c[1] for c in cajas)) / 2
cy_pies = max(c[3] for c in cajas)
informe['caja_del_cuerpo_en_el_PNG'] = {'x': [round(min(c[0] for c in cajas)), round(max(c[1] for c in cajas))], 'y': [round(min(c[2] for c in cajas)), round(max(c[3] for c in cajas))]}

VARIANTES = {}
for n in (30, 40, 48, 60):
    VARIANTES[f'nn{n}'] = dict(ancho=n, alto=n, x0=0.0, y0=0.0, px=LADO / n, py=LADO / n, nota=f'PNG completo a {n}x{n}, vecino más cercano')
# «nat»: 60x60 celdas del arte original (un punto por celda, con el paso real de la rejilla), centrado en el cuerpo.
def en_rejilla(v: float, fase: float, paso: float) -> float:
    return fase + round((v - fase) / paso) * paso  # el borde de la ventana cae en una arista de celda: cada muestra es el centro de una celda


VARIANTES['nat60'] = dict(ancho=60, alto=60, x0=en_rejilla(cx - 30 * px_nat, fx, px_nat), y0=en_rejilla(cy_pies - 56 * py_nat, fy, py_nat), px=px_nat, py=py_nat, nota='ventana de 60x60 celdas nativas del arte, centrada en Emi, pies a 4 celdas del borde')
# «nat28»: para la banda del terminal (14 filas = 28 px). Ventana de 56x56 celdas nativas a 2 celdas por píxel; la muestra cae en el centro
# de cada celda nativa (2x2 por píxel).
VARIANTES['nat28'] = dict(ancho=28, alto=28, x0=en_rejilla(cx - 28 * px_nat, fx, px_nat), y0=en_rejilla(cy_pies - 52 * py_nat, fy, py_nat), px=2 * px_nat, py=2 * py_nat, bloque=2, nota='ventana de 56x56 celdas nativas reducida a 28x28 (media de 2x2 celdas), pies a 2 px del borde')


def cuantizar(imgs: list[np.ndarray], maximo: int = 88):
    """Paleta común de todos los fotogramas: los colores exactos si caben; si no, corte mediano de Pillow sin tramado."""
    opacos = np.concatenate([im[im[..., 3] > 0][:, :3] for im in imgs])
    unicos, cuentas = np.unique(opacos, axis=0, return_counts=True)
    if len(unicos) <= maximo:
        return [tuple(int(v) for v in c) for c in unicos], 0.0, len(unicos)
    muestra = Image.fromarray(unicos.astype(np.uint8)[None, :, :])
    q = muestra.quantize(colors=maximo, method=Image.MEDIANCUT, dither=Image.NONE)
    pal = np.array(q.getpalette()[:maximo * 3]).reshape(-1, 3)
    # cada color exacto -> el más cercano de la paleta (pesando por uso)
    d = ((unicos[:, None, :].astype(int) - pal[None, :, :]) ** 2).sum(-1)
    err = float(np.sqrt((d.min(1) * cuentas).sum() / cuentas.sum()))
    return [tuple(int(v) for v in c) for c in pal], err, len(unicos)


def codificar_fila(fila: str) -> str:
    sal, i = '', 0
    while i < len(fila):
        j = i
        while j < len(fila) and fila[j] == fila[i] and j - i < 35:
            j += 1
        sal += f'§{CUENTA[j - i]}{fila[i]}' if j - i >= 4 else fila[i:j]
        i = j
    return sal


def a_texto(im: np.ndarray, pal: list) -> list[str]:
    arr = np.array(pal, dtype=int)
    filas = []
    for fila in im:
        s = ''
        for r, g, b, a in fila:
            if a == 0:
                s += '.'
            else:
                s += ALFABETO[int(((arr - (r, g, b)) ** 2).sum(1).argmin())]
        filas.append(s)
    return filas


def a_rgb(im: np.ndarray, pal: list) -> np.ndarray:
    arr = np.array(pal, dtype=np.uint8)
    sal = np.zeros(im.shape[:2] + (3,), np.uint8)
    sal[:] = TARJETA
    for y in range(im.shape[0]):
        for x in range(im.shape[1]):
            if im[y, x, 3]:
                sal[y, x] = arr[int(((arr.astype(int) - im[y, x, :3]) ** 2).sum(1).argmin())]
    return sal


datos_ts = {}
resumen = {}
rgb_por_variante: dict[str, list[np.ndarray]] = {}
for nombre, v in VARIANTES.items():
    imgs = [muestrear(i, v['ancho'], v['alto'], v['x0'], v['y0'], v['px'], v['py'], v.get('bloque', 1)) for i in range(N)]
    pal, err, exactos = cuantizar(imgs)
    # estadísticas de calidad: contorno negro conservado y tamaño de Emi
    cuerpo = [im[..., 3] > 0 for im in imgs]
    ys, xs = np.where(np.logical_or.reduce(cuerpo))
    # silueta contra la referencia (fotograma 1 alineado a 1254, reducida al mismo muestreo con un punto por píxel)
    opacos_f1 = int(cuerpo[0].sum())
    resumen[nombre] = {
        'nota': v['nota'],
        'tam': f"{v['ancho']}x{v['alto']}",
        'colores_exactos': exactos,
        'colores_en_paleta': len(pal),
        'error_de_color_rgb': round(err, 2),
        'caja_de_emi_px': [int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)],
        'margen_px': {'izq': int(xs.min()), 'der': int(v['ancho'] - 1 - xs.max()), 'arriba': int(ys.min()), 'abajo': int(v['alto'] - 1 - ys.max())},
        'pixeles_opacos_fotograma1': opacos_f1,
        'pixeles_de_contorno_negro_f1': int(((imgs[0][..., :3] < 40).all(-1) & cuerpo[0]).sum()),
        'celdas_de_terminal': f"{v['ancho']} columnas x {v['alto'] // 2} filas",
    }
    datos_ts[nombre] = {
        'ancho': v['ancho'],
        'alto': v['alto'],
        'paleta': ['#%02x%02x%02x' % c for c in pal],
        'fotogramas': ['/'.join(codificar_fila(f) for f in a_texto(im, pal)) for im in imgs],
    }
    rgb_por_variante[nombre] = [a_rgb(im, pal) for im in imgs]

informe['variantes'] = resumen

# ---------- 5. Datos para el laboratorio ----------
lineas = [
    f"// Generado por scripts\\pipeline-sprites\\estado_animado.py {ESTADO} desde arte\\{CFG['entrada']} ({N} PNG de 1254x1254). No editar a mano.",
    f"// Variantes del estado «{CFG['titulo']}» ({N} fotogramas alineados). Filas separadas por «/», «.» transparente, «§»+largo+color = tramo repetido.",
    "import type { VarianteConv } from './convdibujo'",
    f"export const {CFG['const']}: Record<string, VarianteConv> = " + json.dumps(datos_ts, ensure_ascii=False, indent=1),
]
TS.write_text('\n'.join(lineas) + '\n', encoding='utf-8')

# ---------- 6. Vista previa y comparación con el estado actual ----------


def leer_actual(estado: str = ESTADO):
    """Los fotogramas del estado actual del mod a tamaño M (40x60), leídos de laboratorio\\hooks\\sprites.ts."""
    texto = (RAIZ / 'mod' / 'hooks' / 'sprites.ts').read_text(encoding='utf-8')
    bloque = texto[texto.index('  M: {'):]
    pal = re.search(r'paleta: \[(.*?)\]', bloque, re.S).group(1)
    pal = re.findall(r'"(#[0-9a-f]{6})"', pal)
    nueva = re.search(estado + r': \[(.*?)\],\n', bloque, re.S).group(1)  # un «]» puede ser un color de la paleta
    fots = re.findall(r'"([^"]*)"', nueva)
    sal = []
    for f in fots:
        filas = []
        for fila in f.split('/'):
            s, i = '', 0
            while i < len(fila):
                if fila[i] == '§':
                    s += fila[i + 2] * CUENTA.index(fila[i + 1])
                    i += 3
                else:
                    s += fila[i]
                    i += 1
            filas.append(s)
        arr = np.zeros((len(filas), len(filas[0]), 3), np.uint8)
        arr[:] = TARJETA
        for y, fila in enumerate(filas):
            for x, c in enumerate(fila):
                if c != '.':
                    arr[y, x] = tuple(int(pal[ALFABETO.index(c)][k:k + 2], 16) for k in (1, 3, 5))
        sal.append(arr)
    return sal


actual = leer_actual()
ESC = 6
anchura = max(v.shape[1] for v in actual) + 2
filas_img = []
etiquetas = []


def tira(frames_rgb: list[np.ndarray]) -> Image.Image:
    h = max(f.shape[0] for f in frames_rgb)
    w = sum(f.shape[1] for f in frames_rgb) + 4 * (len(frames_rgb) - 1)
    lienzo = np.full((h, w, 3), 255, np.uint8)
    x = 0
    for f in frames_rgb:
        lienzo[:f.shape[0], x:x + f.shape[1]] = f
        x += f.shape[1] + 4
    return Image.fromarray(lienzo).resize((w * ESC, h * ESC), Image.NEAREST)


tira(actual).save(SALIDA / f'actual_{ESTADO}_M_40x60.png')
for nombre, lista in rgb_por_variante.items():
    tira(lista).save(SALIDA / f'{nombre}.png')
# Hoja comparativa a la misma escala de pantalla: el actual (4 fotogramas) y la variante de 60 (8 fotogramas, 2 filas de 4)
for nombre in ('nn60', 'nat60'):
    lista = rgb_por_variante[nombre]
    a = tira(lista[:4])
    b = tira(lista[4:]) if N > 4 else Image.new('RGB', (1, 1), (255, 255, 255))
    c = tira(actual)
    h = a.height + b.height + c.height + 24
    w = max(a.width, b.width, c.width)
    hoja = Image.new('RGB', (w, h), (255, 255, 255))
    hoja.paste(c, (0, 0))
    hoja.paste(a, (0, c.height + 12))
    hoja.paste(b, (0, c.height + a.height + 24))
    hoja.save(SALIDA / f'comparacion_actual_vs_{nombre}.png')
# Movimiento: diferencia entre fotogramas consecutivos (alineados) en píxeles del sprite de 60
nat = [np.array(x) for x in rgb_por_variante['nat60']]
informe['movimiento_nat60_pixeles_distintos_entre_fotogramas'] = [int((nat[(i + 1) % N] != nat[i]).any(-1).sum()) for i in range(N)]
(SALIDA / 'informe.json').write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(informe, ensure_ascii=False, indent=2))
