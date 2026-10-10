"""Exporta los fotogramas de Emi a PNG transparentes para el programa de escritorio (emi_escritorio.pyw).

Uso:  python escritorio\\exportar_frames.py
Lee mod\\hooks\\sprites.ts (tamaño XL, 12 estados x 4 fotogramas) y mod\\hooks\\animaciones.ts («pensando», 5 fotogramas de 60x60).
Escribe escritorio\\frames\\<estado>_<n>.png, todos en un lienzo de 72x96 «píxeles de arte» con los pies abajo y centrados,
para que Emi no salte de sitio al cambiar de estado. Solo Pillow. Hay que repetirlo si cambia el arte del mod.
"""
import json
import re
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[2]  # mod\escritorio -> raíz del proyecto
SALIDA = Path(__file__).resolve().parent / 'frames'
ALFABETO = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!#$%&*+,-:;<=>?@^_~()[]{}|'
CUENTA = '0123456789abcdefghijklmnopqrstuvwxyz'
LIENZO = (72, 96)


def descomprimir(fila: str) -> str:
    sal, i = '', 0
    while i < len(fila):
        if fila[i] == '§':
            sal += fila[i + 2] * CUENTA.index(fila[i + 1])
            i += 3
        else:
            sal += fila[i]
            i += 1
    return sal


def a_imagen(fotograma: str, paleta: list[str]) -> Image.Image:
    filas = [descomprimir(f) for f in fotograma.split('/')]
    im = Image.new('RGBA', (len(filas[0]), len(filas)), (0, 0, 0, 0))
    px = im.load()
    for y, fila in enumerate(filas):
        for x, c in enumerate(fila):
            if c != '.':
                h = paleta[ALFABETO.index(c)]
                px[x, y] = (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), 255)
    return im


def en_lienzo(im: Image.Image) -> Image.Image:
    lienzo = Image.new('RGBA', LIENZO, (0, 0, 0, 0))
    lienzo.paste(im, ((LIENZO[0] - im.width) // 2, LIENZO[1] - im.height), im)
    return lienzo


texto = (RAIZ / 'mod' / 'hooks' / 'sprites.ts').read_text(encoding='utf-8')
bloque = texto[texto.index('  XL: {'):]
paleta = re.findall(r'"(#[0-9a-f]{6})"', re.search(r'paleta: \[(.*?)\]', bloque, re.S).group(1))
SALIDA.mkdir(exist_ok=True)
for viejo in SALIDA.glob('*.png'):
    viejo.unlink()
estados = re.findall(r'\n      (\w+): \[(.*?)\],?(?=\n)', bloque[bloque.index('estados:'):], re.S)
total = 0
for nombre, lista in estados:
    for i, f in enumerate(re.findall(r'"([^"]*)"', lista)):
        en_lienzo(a_imagen(f, paleta)).save(SALIDA / f'{nombre}_{i}.png')
        total += 1
    if nombre == 'duerme':
        break  # el siguiente bloque ya sería otro tamaño

# Estados con animación propia (pensando, hula...): hoja de 60x60; se recorta al cuerpo (misma caja en todos los fotogramas del estado),
# se amplía x2 si cabe en el lienzo (si no, x1) y se coloca igual que el resto.
ts = (RAIZ / 'mod' / 'hooks' / 'animaciones.ts').read_text(encoding='utf-8')
especial = json.loads(re.search(r'export const ESPECIAL[^=]*= (\{.*\})\s*\n', ts).group(1))
anim = json.loads(ts[ts.index('export const ANIM') :].split('= ', 1)[1])
for estado, e in especial.items():
    for viejo in SALIDA.glob(f'{estado}_*.png'):
        viejo.unlink()
    hoja = anim[e['tam']]
    ims = [a_imagen(f, hoja['paleta']) for f in hoja['estados'][estado]]
    cajas = [im.getbbox() for im in ims]
    caja = (min(c[0] for c in cajas), min(c[1] for c in cajas), max(c[2] for c in cajas), max(c[3] for c in cajas))
    w, h = caja[2] - caja[0], caja[3] - caja[1]
    escala = 2 if w * 2 <= LIENZO[0] and h * 2 <= LIENZO[1] else 1  # entera: el arte pixelado no admite escalas con decimales
    for i, im in enumerate(ims):
        recorte = im.crop(caja)
        recorte = recorte.resize((round(w * escala), round(h * escala)), Image.NEAREST)
        en_lienzo(recorte).save(SALIDA / f'{estado}_{i}.png')
        total += 1
    print(estado, 'recortado a', caja, 'ampliado x%.2f' % escala)
print('fotogramas escritos:', total)
