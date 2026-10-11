"""Genera mod\\hooks\\animaciones.ts con los estados que tienen animación propia (60x60 para paneles y escritorio, 28x28 para la banda del terminal).

Uso:  python scripts\\pipeline-sprites\\animaciones_mod.py
Antes hay que haber corrido estado_animado.py <estado> de cada uno (genera laboratorio\\hooks\\<estado>.ts).
Para sumar un estado: añadirlo a ESTADOS, correr estado_animado.py, este script y escritorio\\exportar_frames.py.
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
# estado del mod -> (archivo del laboratorio, hoja grande, hoja chica, ¿sobre la tarjeta lila?). Todos los estados completan su ciclo a 5 fps (PASO_MS en dibujo.ts).
# «tarjeta»: el arte con contorno negro posa sobre la tarjeta lila (como los demás estados); el que no lo trae (pensando) deja ver el fondo.
# «nueva» (conversacion.ts, 8 fps) está lista en el laboratorio pero aún no se lleva al mod: añadirla aquí cuando se autorice.
ESTADOS = {
    'pensando': ('pensando.ts', 'A5', 'A5S', False),
    'hula': ('hula.ts', 'H5', 'H5S', False),
    'escribiendo': ('escribiendo.ts', 'E5', 'E5S', False),
    'terminado': ('terminado.ts', 'T5', 'T5S', False),
    'responde': ('responde.ts', 'R5', 'R5S', False),
    'leyendo': ('leyendo.ts', 'L5', 'L5S', False),
    'necesita': ('necesita.ts', 'N5', 'N5S', False),
    'duerme': ('duerme.ts', 'D5', 'D5S', False),
}


def variante(archivo: str, nombre: str) -> dict:
    texto = (RAIZ / 'laboratorio' / 'hooks' / archivo).read_text(encoding='utf-8')
    return json.loads(texto[texto.index('= {') + 2:])[nombre]


hojas = {}
especial = {}
for estado, (archivo, grande, chico, tarjeta) in ESTADOS.items():
    for tam, nombre in ((grande, 'nat60'), (chico, 'nat28')):
        v = variante(archivo, nombre)
        hojas[tam] = {'ancho': v['ancho'], 'alto': v['alto'], 'paleta': v['paleta'], 'estados': {estado: v['fotogramas']}}
    especial[estado] = {'tam': grande, 'chico': chico, 'tarjeta': tarjeta}

tipos = ' | '.join(f"'{t}'" for t in hojas)
lineas = [
    '// Generado por scripts\\pipeline-sprites\\animaciones_mod.py desde los PNG de arte\\ (variantes nat60 y nat28). No editar a mano.',
    '// Estados con animación propia: la hoja grande (60x60) va en los paneles y la banda de escritorio; la chica (28x28), en la banda del terminal.',
    "import type { Hoja } from './sprites'",
    '',
    f'export type TamAnim = {tipos}',
    '// Qué estado usa qué hoja (grande y chica) y si posa sobre la tarjeta lila (arte con contorno negro).',
    'export const ESPECIAL: Record<string, { tam: TamAnim; chico: TamAnim; tarjeta: boolean }> = ' + json.dumps(especial),
    'export const ANIM: Record<TamAnim, Hoja> = ' + json.dumps(hojas, ensure_ascii=False, indent=1),
]
(RAIZ / 'mod' / 'hooks' / 'animaciones.ts').write_text('\n'.join(lineas) + '\n', encoding='utf-8')
print('ok', {t: len(h['estados'][list(h['estados'])[0]]) for t, h in hojas.items()})
