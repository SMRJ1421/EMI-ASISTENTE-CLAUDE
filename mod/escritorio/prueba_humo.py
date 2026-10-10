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
