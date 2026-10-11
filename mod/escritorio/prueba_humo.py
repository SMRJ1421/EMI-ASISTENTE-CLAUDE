"""Prueba de humo del programa de escritorio, sin tocar tu ~/.claude: sesión falsa, una sola instancia y cierre al quedarse sin sesiones.
Uso: python escritorio/prueba_humo.py (abre una ventana de Emi unos segundos)."""
import json, os, subprocess, sys, tempfile, time
from pathlib import Path
PROGRAMA = str(Path(__file__).resolve().parent / 'emi_escritorio.pyw')
d = Path(tempfile.mkdtemp()); (d/'sesiones').mkdir()
def sesion(estado):
    (d/'sesiones'/'a.json').write_text(json.dumps({'id':'a','trabajando':True,'vivo':int(time.time()*1000),'cerrada':False,'estado':estado,'desde':int(time.time()*1000)}))
sesion('pensando')
env = dict(os.environ, EMI_DATOS=str(d), EMI_PUERTO='47999')
p = subprocess.Popen([sys.executable, PROGRAMA], env=env, stderr=subprocess.PIPE)
time.sleep(3); sesion('escribiendo'); time.sleep(2)
assert p.poll() is None, 'se cerró con una sesión viva'
# una segunda instancia debe irse sola (una sola Emi)
q = subprocess.run([sys.executable, PROGRAMA], env=env, timeout=10)
assert q.returncode == 0, 'la segunda instancia debía irse sola'
(d/'sesiones'/'a.json').write_text(json.dumps({'id':'a','vivo':int(time.time()*1000),'cerrada':True}))
t0=time.time()
while p.poll() is None and time.time()-t0<20: time.sleep(0.5)
assert p.poll() == 0, 'no se cerró al quedarse sin sesiones: ' + p.stderr.read().decode()[:300]
print('ok: una sola instancia, y se cerró sola', round(time.time()-t0,1), 's después de la última sesión')
assert (d/'escritorio.json').exists(), 'no guardó su posición'

# Fotogramas grandes: se cargan, se reducen por saltos (251 px en tamaño Mediana) y la ventana los abarca.
import importlib.util
import tempfile as _tf

os.environ['EMI_DATOS'] = _tf.mkdtemp()
_spec = importlib.util.spec_from_file_location('emi_escritorio', PROGRAMA)
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)
_e = _m.Emi()
assert _e.hd.get('pensando') and len(_e.hd['pensando']) == 8 and len(_e.hd['hula']) == 8, 'faltan los PNG grandes'
_t0 = time.time()
_f = _e.foto_hd('pensando', 0)
assert _f.width() == 251 and _f.height() == 251, (_f.width(), _f.height())  # 1254 / 5 redondeado hacia arriba
_primera = time.time() - _t0
assert _e.tam()[0] >= 251 and _e.tam()[1] >= 251
_e.cambiar_escala(3)
assert _e.foto_hd('hula', 2).width() == 418
# Globo de mensaje: sale con el estado activo y el detalle; se esconde en reposo y con la opción apagada.
_e.estado = 'escribiendo'
_e.actualizar_globo('escribiendo...', 'Edit register.tsx')
_e.raiz.update()
assert _e.globo.state() == 'normal' and _e.l_detalle.cget('text') == 'Edit register.tsx' and _e.l_frase.cget('text') == 'escribiendo...'
assert _e.globo.winfo_x() >= 0 and _e.globo.winfo_y() >= 0
_e.actualizar_globo('picando código…', 'Edit x', '#f2c94c')
assert _e.l_frase.cget('fg') == '#a98c35', _e.l_frase.cget('fg')  # amarillo del estado, oscurecido
_e.alternar_mensaje()
assert _e.globo.state() == 'withdrawn'
_e.alternar_mensaje()
assert _e.globo.state() == 'normal'
_e.estado = 'hula'
_e.actualizar_globo('vigilando', '')
assert _e.globo.state() == 'withdrawn'
print('ok: globo de mensaje')
_e.raiz.destroy()
print('ok: fotogramas grandes (primer PNG de 1254x1254 cargado y reducido en %.2f s)' % _primera)

# 5 fps: cada dibujo dura 200 ms (ciclo de 1,6 s con 8 fotogramas y de 0,8 s con 4).
_t = time.time()
assert [_m.fotograma_de('x', _t - s, 8) for s in (0.0, 0.199, 0.201, 1.05, 1.59, 1.61)] == [0, 0, 1, 5, 7, 0]
assert [_m.fotograma_de('x', _t - s, 4) for s in (0.0, 0.199, 0.201, 0.79, 0.81)] == [0, 0, 1, 3, 0]
print('ok: 5 fps')
