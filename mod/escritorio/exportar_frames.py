"""Exporta los fotogramas de Emi a PNG transparentes para el programa de escritorio (emi_escritorio.pyw).

Uso:  python escritorio\\exportar_frames.py
Lee mod\\hooks\\sprites.ts (tamaño XL, 12 estados x 4 fotogramas) y mod\\hooks\\animaciones.ts («pensando», 5 fotogramas de 60x60).
Escribe escritorio\\frames\\<estado>_<n>.png, todos en un lienzo de 72x96 «píxeles de arte» con los pies abajo y centrados,
para que Emi no salte de sitio al cambiar de estado. Solo Pillow. Hay que repetirlo si cambia el arte del mod.
"""
import json
import re
from pathlib import Path

import numpy as np
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

# Originales de alta resolución (1254x1254, mismos colores; solo se limpia el alfa, ver abajo) para los estados que los tienen: Emi escritorio los muestra a casi su
# resolución. Si falta alguno, usa el fotograma pequeño de arriba. Se copian con el nombre <estado>_<n>.png (n desde 0, orden de nombre).
HD = {
    'pensando': RAIZ / 'arte' / 'EMI CLAUDE PENSANDO',
    'hula': RAIZ / 'arte' / 'EMI-CLAUDE-DE-GUARDIA',
    'terminado': RAIZ / 'arte' / 'EMI_CLAUDE_TERMINADO',
    'responde': RAIZ / 'arte' / 'EMI-CALUDE-TE-RESPONDE',
    'leyendo': RAIZ / 'arte' / 'EMI-CLAUDE-LEYENDO',
    'necesita': RAIZ / 'arte' / 'EMI-CLAUDE-NECESITA',
    'duerme': RAIZ / 'arte' / 'EMI-CLAUDE-DUERME',
    'guardando': RAIZ / 'arte' / 'EMI-CLAUDE-SAVE-OBSIDIAN',
    'caminando': RAIZ / 'arte' / 'EMI-CLAUDE-CAMINANDO',  # solo Emi escritorio: vuelve a su sitio
    'sujeta': RAIZ / 'arte' / 'EMI-CLAUDE-SUJETA',  # solo Emi escritorio: mientras la arrastras
    'caida': RAIZ / 'arte' / 'EMI-CLAUDE-CAIDA',  # solo Emi escritorio: al soltarla con «caída al soltar»
    'escribiendo': RAIZ / 'arte' / 'EMI-CLAUDE-ESCRIBIENDO-COMANDOS',
}
import shutil

DESTINO_HD = Path(__file__).resolve().parent / 'hd'
DESTINO_HD.mkdir(exist_ok=True)
for viejo in DESTINO_HD.glob('*.png'):
    viejo.unlink()
for estado, carpeta in HD.items():
    originales = sorted(carpeta.glob('*.png'))
    cuadros = []
    for origen in originales:
        # Mismos colores y tamaño, pero alfa de todo o nada (>=128 opaco): los píxeles casi transparentes (motas, bordes suaves y el 251-254 del
        # cuerpo) se mezclarían en pantalla con el color transparente de la ventana (magenta) y dejarían puntos morados alrededor de Emi.
        px = np.array(Image.open(origen).convert('RGBA'))
        px[..., 3] = np.where(px[..., 3] >= 128, 255, 0)
        px[px[..., 3] == 0] = 0
        cuadros.append(px)
    # Todos los estados apoyan los pies en la misma línea y quedan centrados en el mismo punto, para que Emi no «salte» al cambiar de estado
    # (los lienzos originales ponen los pies entre el 90 % y el 96 % de la altura). Se mueven todos los fotogramas del estado por igual:
    # el movimiento propio de la animación se conserva.
    cajas = [np.where(c[..., 3] > 0) for c in cuadros]
    x0, x1 = min(xs.min() for _, xs in cajas), max(xs.max() for _, xs in cajas) + 1
    y1 = max(ys.max() for ys, _ in cajas) + 1
    lado = cuadros[0].shape[0]
    dx, dy = lado // 2 - (x0 + x1) // 2, (lado - 8) - y1
    for i, px in enumerate(cuadros):
        nuevo = np.zeros_like(px)
        ys, xs = np.where(px[..., 3] > 0)
        ny, nx = ys + dy, xs + dx
        dentro = (ny >= 0) & (ny < lado) & (nx >= 0) & (nx < lado)
        nuevo[ny[dentro], nx[dentro]] = px[ys[dentro], xs[dentro]]
        Image.fromarray(nuevo, 'RGBA').save(DESTINO_HD / f'{estado}_{i}.png', optimize=True)
    print(estado, 'HD:', len(originales), 'fotogramas de', carpeta.name, f'(movido dx={dx}, dy={dy} px)')

# Marco de las barras de uso y caché (arte\barra-emi-claude\1.png): se vacía el hueco interior (Emi escritorio dibuja ahí el relleno),
# se recorta a lo visible y se reduce con vecino más cercano a 60 px de ancho, con alfa de todo o nada (mismo motivo que los HD).
MARCO_ORIGEN = RAIZ / 'arte' / 'barra-emi-claude' / '1.png'
HUECO = (361, 395, 527, 1462)  # x0, y0, x1, y1 del interior en el original (medido)
MARCO_ANCHO = 90
if MARCO_ORIGEN.exists():
    px = np.array(Image.open(MARCO_ORIGEN).convert('RGBA'))
    px[HUECO[1]:HUECO[3], HUECO[0]:HUECO[2]] = 0
    im = Image.fromarray(px, 'RGBA')
    caja = im.getbbox()
    im = im.crop(caja)
    alto = round(im.height * MARCO_ANCHO / im.width)
    escala = MARCO_ANCHO / im.width
    im = im.resize((MARCO_ANCHO, alto), Image.NEAREST)
    px = np.array(im)
    px[..., 3] = np.where(px[..., 3] >= 128, 255, 0)
    px[px[..., 3] == 0] = 0
    Image.fromarray(px, 'RGBA').save(Path(__file__).resolve().parent / 'marco_barra.png', optimize=True)
    hueco = [round((HUECO[0] - caja[0]) * escala), round((HUECO[1] - caja[1]) * escala), round((HUECO[2] - caja[0]) * escala), round((HUECO[3] - caja[1]) * escala)]
    print('marco_barra.png', MARCO_ANCHO, 'x', alto, 'hueco', hueco)  # copiar a MARCO_HUECO en emi_escritorio.pyw

# Panel de configuración (arte\interfaz): fondo de ventana, filas normal/encima, interruptores y cabecera con Emi, ya a su tamaño final.
# Se reducen con Lanczos (es ilustración grande, no píxel a píxel) y alfa de todo o nada, como el resto. Medidas en px del panel (ver emi_escritorio.pyw).
INTERFAZ = RAIZ / 'arte' / 'interfaz'
DESTINO_UI = Path(__file__).resolve().parent / 'interfaz'
PANEL_ANCHO, PANEL_ALTO, FILA_ANCHO, FILA_ALTO, INTER_ALTO = 380, 669, 330, 46, 30  # 9 filas


def alfa_binario(im: Image.Image) -> Image.Image:
    px = np.array(im.convert('RGBA'))
    px[..., 3] = np.where(px[..., 3] >= 128, 255, 0)
    px[px[..., 3] == 0] = 0
    return Image.fromarray(px, 'RGBA')


def recortada(n: int) -> Image.Image:
    im = alfa_binario(Image.open(INTERFAZ / f'{n}.png'))  # la caja, sin la sombra casi transparente
    return im.crop(im.getbbox())


def fila(n: int) -> Image.Image:
    # Altura fija; los extremos (con sus adornos) se conservan y el centro se estira a lo ancho.
    im = recortada(n)
    im = im.resize((round(im.width * FILA_ALTO / im.height), FILA_ALTO), Image.LANCZOS)
    cap = im.width // 6
    out = Image.new('RGBA', (FILA_ANCHO, FILA_ALTO))
    out.paste(im.crop((0, 0, cap, FILA_ALTO)), (0, 0))
    out.paste(im.crop((cap, 0, im.width - cap, FILA_ALTO)).resize((FILA_ANCHO - 2 * cap, FILA_ALTO), Image.LANCZOS), (cap, 0))
    out.paste(im.crop((im.width - cap, 0, im.width, FILA_ALTO)), (FILA_ANCHO - cap, 0))
    return alfa_binario(out)


if INTERFAZ.exists():
    DESTINO_UI.mkdir(exist_ok=True)
    v = np.array(recortada(1))  # 890x1300: se vacía el interior (traía 6 casillas dibujadas) y se alarga por el centro
    v[157:1242, 53:853] = v[700, 450]
    s = PANEL_ANCHO / v.shape[1]
    alto = round(PANEL_ALTO / s)
    if alto >= len(v):
        v = np.concatenate([v[:650], np.repeat(v[650:651], alto - len(v), axis=0), v[650:]])
    else:
        v = np.concatenate([v[:650 - (len(v) - alto)], v[650:]])
    alfa_binario(Image.fromarray(v, 'RGBA').resize((PANEL_ANCHO, PANEL_ALTO), Image.LANCZOS)).save(DESTINO_UI / 'fondo.png', optimize=True)
    fila(3).save(DESTINO_UI / 'fila.png', optimize=True)
    fila(4).save(DESTINO_UI / 'fila_encima.png', optimize=True)
    for n, nombre in ((6, 'si'), (7, 'no')):
        im = recortada(n)
        alfa_binario(im.resize((round(im.width * INTER_ALTO / im.height), INTER_ALTO), Image.LANCZOS)).save(DESTINO_UI / f'interruptor_{nombre}.png', optimize=True)
    # Cabecera: Emi asomada sobre una barra (arte\interfaz\emi-para-interfaz.png), recortada hasta la barra.
    im = Image.open(INTERFAZ / 'emi-para-interfaz.png').convert('RGBA').crop((120, 0, 1140, 518))
    alfa_binario(im.resize((round(im.width * 112 / im.height), 112), Image.LANCZOS)).save(DESTINO_UI / 'cabecera.png', optimize=True)
    print('interfaz:', sorted(p.name for p in DESTINO_UI.glob('*.png')))

# Iconos de las filas del panel (arte\interfaz\ICONO-INTERFAZ\1..7.png, en el orden de FILAS_PANEL), a 34 px de alto.
ICONOS = ['uso', 'cache', 'tiempo', 'cuadro', 'oculta', 'caida', 'banda_app', 'atenuar', 'mensaje']
if (INTERFAZ / 'ICONO-INTERFAZ').exists():
    for n, k in enumerate(ICONOS, 1):
        origen = INTERFAZ / 'ICONO-INTERFAZ' / f'{n}.png'
        im = alfa_binario(Image.open(origen if origen.exists() else INTERFAZ / 'ICONO-INTERFAZ' / '5.png'))  # sin icono propio (8: atenuar, 9: frase de estado), el del ojo
        im = im.crop(im.getbbox())
        lado = 34
        alfa_binario(im.resize((round(im.width * lado / max(im.size)), round(im.height * lado / max(im.size))), Image.LANCZOS)).save(DESTINO_UI / f'icono_{k}.png', optimize=True)
    print('iconos:', len(ICONOS))
