"""Estados cuyo arte ya viene a 60x60 reales (con copia de alta resolución que aquí no se usa): se toman tal cual, sin reducir ni alinear.

Uso:  python scripts\\pipeline-sprites\\animacion_nativa.py escribiendo
Entrada: arte\\<carpeta>\\*-frame-NN.png (60x60 RGBA; se ignoran los «alta-resolucion»). Solo lectura.
Salida:  laboratorio\\hooks\\<estado>.ts con las variantes nat60 (los 60x60 tal cual) y nat28 (media de cajas a 28x28 para la banda del terminal),
         con el mismo formato que estado_animado.py, de modo que animaciones_mod.py los recoge igual. Vistas previas en datos-laboratorio\\<estado>\\.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parents[2]
ESTADOS = {
    'escribiendo': dict(entrada='EMI-CLAUDE-ESCRIBIENDO-COMANDOS', patron='*.png', ts='escribiendo.ts', const='ESCR', titulo='Escribiendo / comandos', modo='ilustrada'),
    'hula': dict(entrada='EMI-CLAUDE-DE-GUARDIA', patron='*.png', ts='hula.ts', const='HULA', titulo='De guardia', modo='ilustrada'),
    'responde': dict(entrada='EMI-CALUDE-TE-RESPONDE', patron='*.png', ts='responde.ts', const='RESP', titulo='Te responde', modo='ilustrada'),
    'leyendo': dict(entrada='EMI-CLAUDE-LEYENDO', patron='*.png', ts='leyendo.ts', const='LEER', titulo='Leyendo', modo='ilustrada'),
    'terminado': dict(entrada='EMI_CLAUDE_TERMINADO', patron='*.png', ts='terminado.ts', const='TERM', titulo='Terminado', modo='ilustrada'),
    'duerme': dict(entrada='EMI-CLAUDE-DUERME', patron='*.png', ts='duerme.ts', const='DUER', titulo='Duerme', modo='ilustrada'),
    'necesita': dict(entrada='EMI-CLAUDE-NECESITA', patron='*.png', ts='necesita.ts', const='NECE', titulo='Necesita', modo='ilustrada'),
    'pensando': dict(entrada='EMI CLAUDE PENSANDO', patron='*.png', ts='pensando.ts', const='PENS', titulo='Pensando', modo='ilustrada'),
}
ESTADO = sys.argv[1] if len(sys.argv) > 1 else 'escribiendo'
CFG = ESTADOS[ESTADO]
ENTRADA = RAIZ / 'arte' / CFG['entrada']
SALIDA = RAIZ / 'datos-laboratorio' / ESTADO
SALIDA.mkdir(parents=True, exist_ok=True)
ALFABETO = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!#$%&*+,-:;<=>?@^_~()[]{}|'
CUENTA = '0123456789abcdefghijklmnopqrstuvwxyz'
TARJETA = (0xF5, 0xE6, 0xFD)

archivos = sorted(f for f in ENTRADA.glob(CFG['patron']) if 'alta-resolucion' not in f.name)
frames = [np.array(Image.open(f).convert('RGBA')) for f in archivos]
if CFG['modo'] == 'nativa':
    assert frames and all(f.shape == (60, 60, 4) for f in frames), 'se esperaban fotogramas de 60x60'


def reducir(f: np.ndarray, caja: tuple, alto_fig: int, lienzo: int) -> np.ndarray:
    """Recorta `caja` (la misma para todos los fotogramas), la reduce con Lanczos a `alto_fig` de alto y la deja abajo y centrada en `lienzo` x `lienzo`."""
    x0, y0, x1, y1 = caja
    escala = min(alto_fig / (y1 - y0), (lienzo - 2) / (x1 - x0))  # cabe en alto y en ancho (las escenas anchas, como escribiendo, mandan por el ancho)
    ancho_fig, alto_fig = round((x1 - x0) * escala), round((y1 - y0) * escala)
    a = f[y0:y1, x0:x1].astype(float)
    a[..., :3] *= a[..., 3:4] / 255  # color premultiplicado: el borde no sangra el color del fondo
    r = np.array(Image.fromarray(a.astype(np.uint8), 'RGBA').resize((ancho_fig, alto_fig), Image.LANCZOS)).astype(float)
    alfa = r[..., 3:4] / 255
    col = np.where(alfa > 0, r[..., :3] / np.maximum(alfa, 1e-6), 0)
    sal = np.zeros((lienzo, lienzo, 4), np.uint8)
    ox, oy = (lienzo - ancho_fig) // 2, lienzo - alto_fig - max(1, lienzo // 30)
    sal[oy:oy + alto_fig, ox:ox + ancho_fig, :3] = np.clip(col, 0, 255)
    sal[oy:oy + alto_fig, ox:ox + ancho_fig, 3] = np.where(alfa[..., 0] >= 0.5, 255, 0)
    sal[sal[..., 3] == 0] = 0
    return sal


if CFG['modo'] == 'ilustrada':
    cajas = []
    for f in frames:
        ys, xs = np.where(f[..., 3] >= 128)
        cajas.append((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    CAJA = (min(c[0] for c in cajas), min(c[1] for c in cajas), max(c[2] for c in cajas), max(c[3] for c in cajas))


def binario(f: np.ndarray) -> np.ndarray:
    g = f.copy()
    g[..., 3] = np.where(f[..., 3] >= 128, 255, 0)  # alfa >= 128 opaco; el resto transparente (como en estado_animado.py)
    g[g[..., 3] == 0] = 0
    return g


def a_28(f: np.ndarray) -> np.ndarray:
    """60 -> 28 por media de cajas (como `bloque` en estado_animado.py): opaco si lo es al menos la mitad del área, color medio de los opacos."""
    rgba = f.astype(float)
    peso = (rgba[..., 3] >= 128).astype(float)
    ancho = Image.fromarray((peso * 255).astype(np.uint8)).resize((28, 28), Image.BOX)
    cobertura = np.array(ancho).astype(float) / 255
    canales = [np.array(Image.fromarray((rgba[..., c] * peso).astype(np.uint8)).resize((28, 28), Image.BOX)).astype(float) for c in range(3)]
    sal = np.zeros((28, 28, 4), np.uint8)
    for c in range(3):
        sal[..., c] = np.clip(canales[c] / np.maximum(cobertura, 1e-6), 0, 255)
    sal[..., 3] = np.where(cobertura >= 0.5, 255, 0)
    sal[sal[..., 3] == 0] = 0
    return sal


def cuantizar(imgs: list[np.ndarray], maximo: int = 88, refuerzo: int = 0):
    opacos = np.concatenate([im[im[..., 3] > 0][:, :3] for im in imgs])
    unicos, cuentas = np.unique(opacos, axis=0, return_counts=True)
    if len(unicos) <= maximo:
        return [tuple(int(v) for v in c) for c in unicos], 0.0, len(unicos)
    q = Image.fromarray(unicos.astype(np.uint8)[None, :, :]).quantize(colors=maximo - refuerzo, method=Image.MEDIANCUT, dither=Image.NONE)
    pal = np.array(q.getpalette()[:(maximo - refuerzo) * 3]).reshape(-1, 3)
    # Colores raros pero visibles (el adorno rojo del pelo): `refuerzo` plazas para los más alejados de la paleta, pesados por la raíz de su uso.
    for _ in range(refuerzo):
        d = ((unicos[:, None, :].astype(int) - pal[None, :, :]) ** 2).sum(-1).min(1)
        pal = np.vstack([pal, unicos[int(np.argmax(np.sqrt(d) * np.sqrt(cuentas)))]])
    d = ((unicos[:, None, :].astype(int) - pal[None, :, :]) ** 2).sum(-1)
    return [tuple(int(v) for v in c) for c in pal], float(np.sqrt((d.min(1) * cuentas).sum() / cuentas.sum())), len(unicos)


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
    return [''.join('.' if a == 0 else ALFABETO[int(((arr - (r, g, b)) ** 2).sum(1).argmin())] for r, g, b, a in fila) for fila in im]


def a_rgb(im: np.ndarray, pal: list) -> np.ndarray:
    arr = np.array(pal, dtype=np.uint8)
    sal = np.zeros(im.shape[:2] + (3,), np.uint8)
    sal[:] = TARJETA
    for y, x in zip(*np.where(im[..., 3] > 0)):
        sal[y, x] = arr[int(((arr.astype(int) - im[y, x, :3]) ** 2).sum(1).argmin())]
    return sal


if CFG['modo'] == 'ilustrada':
    variantes = {'nat60': [reducir(f, CAJA, 58, 60) for f in frames], 'nat28': [reducir(f, CAJA, 26, 28) for f in frames]}
else:
    variantes = {'nat60': [binario(f) for f in frames], 'nat28': [a_28(f) for f in frames]}
datos, informe, vistas = {}, {'archivos': [a.name for a in archivos], 'fotogramas_identicos': sum(1 for i in range(len(frames)) for j in range(i) if (frames[i] == frames[j]).all())}, {}
for nombre, imgs in variantes.items():
    pal, err, exactos = cuantizar(imgs, refuerzo=10 if CFG['modo'] == 'ilustrada' else 0)
    datos[nombre] = {'ancho': imgs[0].shape[1], 'alto': imgs[0].shape[0], 'paleta': ['#%02x%02x%02x' % c for c in pal],
                     'fotogramas': ['/'.join(codificar_fila(f) for f in a_texto(im, pal)) for im in imgs]}
    informe[nombre] = {'colores_exactos': exactos, 'colores_en_paleta': len(pal), 'error_de_color_rgb': round(err, 2)}
    vistas[nombre] = [a_rgb(im, pal) for im in imgs]

lineas = [
    f"// Generado por scripts\\pipeline-sprites\\animacion_nativa.py {ESTADO} desde arte\\{CFG['entrada']} ({len(frames)} PNG, modo {CFG['modo']}). No editar a mano.",
    f"// Variantes del estado «{CFG['titulo']}» ({len(frames)} fotogramas). Filas separadas por «/», «.» transparente, «§»+largo+color = tramo repetido.",
    "import type { VarianteConv } from './convdibujo'",
    f"export const {CFG['const']}: Record<string, VarianteConv> = " + json.dumps(datos, ensure_ascii=False, indent=1),
]
(RAIZ / 'laboratorio' / 'hooks' / CFG['ts']).write_text('\n'.join(lineas) + '\n', encoding='utf-8')

ESC = 6
for nombre, lista in vistas.items():
    h = max(f.shape[0] for f in lista)
    w = sum(f.shape[1] for f in lista) + 4 * (len(lista) - 1)
    lienzo = np.full((h, w, 3), 255, np.uint8)
    x = 0
    for f in lista:
        lienzo[:f.shape[0], x:x + f.shape[1]] = f
        x += f.shape[1] + 4
    Image.fromarray(lienzo).resize((w * ESC, h * ESC), Image.NEAREST).save(SALIDA / f'{nombre}.png')
(SALIDA / 'informe.json').write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(informe, ensure_ascii=False, indent=2))
