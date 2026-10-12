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
_e.cerrar = lambda: None  # sin sesiones se cerraría sola a los 8 s; aquí la prueba la cierra al final
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
_e.actividad = (time.time() - 20 * 60) * 1000
assert _m.texto_cache(_e.actividad) == '40m' and _m.texto_cache(None) == '' and _m.texto_cache(1) == '0m'
assert [_m.texto_trabajado(v) for v in (None, 500, 45000, 150000, 3900000)] == ['', '', '45s', '2m 30s', '1h 05m']
_e.usado = 20
_e.reinicio = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() + 2 * 3600 + 10 * 60 + 30))
_e.dibujar_uso()
_e.raiz.update()
assert _e.lienzo.find_withtag('cache') and _e.lienzo.bbox('cache')[0] < _e.lienzo.bbox('uso')[0], 'la barra del caché va a la izquierda de la de uso'
assert _e.l_reinicio.cget('text') == '2h10m' and _m.falta(None) == '' and _m.falta('2000-01-01T00:00:00Z') == ''
_e.raiz.update()
assert any(_e.lienzo.itemcget(i, 'text') == '20%' for i in _e.lienzo.find_withtag('uso') if _e.lienzo.type(i) == 'text')
# El marco de la barra del caché queda a 2 px de Emi en la fila más cercana (los lazos entran en sus huecos), y la de uso pegada a ella.
_f = _e.lienzo.itemcget(_e.emi, 'image')
_foto = next(v for v in _e.cache.values() if str(v) == _f)
_w, _h = _e.tam()
_ex, _ey, _by = _w // 2 - _foto.width() // 2, _h - _foto.height(), (_h - _m.ALTO_BARRA) // 2
_der, _izq = _e.perfil(_foto, True), _e.perfil(_e.marco, False)
_huecos = [_e.x_barras + m - (_ex + _der[_by + j - _ey]) - 1 for j, m in enumerate(_izq) if m is not None and 0 <= _by + j - _ey < len(_der) and _der[_by + j - _ey] is not None]
assert min(_huecos) >= 2, min(_huecos)  # el dibujo más ancho del estado queda a 2 px; este, a 2 o más
assert _e.lienzo.bbox('uso')[0] - _e.lienzo.bbox('cache')[0] == _e.paso_barras(), 'la de uso, pegada a la del caché'
_xs = set()
for _k in range(8):  # las barras no bailan con la animación del estado
    _e.desde = time.time() - _k * _m.PASO_S
    _e.pintar()
    _xs.add(_e.x_barras)
assert len(_xs) == 1, _xs
assert [_m.color_uso(u) for u in (20, 60, 90)] == ['#3fa66b', '#e59a2f', '#d9434b']
# Tuerca y panel: la tuerca no desaparece al apagar la barra ni al ocultar a Emi.
_e.abrir_panel()
for _k in _m.BARRAS:
    _e.alternar_barra(_k)
_e.raiz.update()
assert not _e.lienzo.find_withtag('uso') and not _e.lienzo.find_withtag('cache') and _e.l_trabajo.winfo_manager() == '' and _e.tuerca.winfo_manager() == 'place' and all(_e.filas_panel[k]['activa'] is False for k in _m.BARRAS)
_e.alternar_oculta()
_e.raiz.update()
assert _e.lienzo.itemcget(_e.emi, 'state') == 'hidden' and _e.tuerca.winfo_manager() == 'place' and _e.filas_panel['oculta']['activa'] is True
_e.alternar_cuadro()
assert _e.cuadro_abierto() and _e.filas_panel['cuadro']['activa'] is True
assert len(_e.filas_cuadro()) == 15 and _e.filas_cuadro()[1][2:] == (8, 200, 5, '1,6')
_e.alternar_oculta()
for _k in _m.BARRAS:
    _e.alternar_barra(_k)
assert _e.filas_panel['caida']['activa'] is True and _e.filas_panel['banda_app']['activa'] is False
_e.alternar_banda_app()
assert (_m.DATOS / 'banda_app.txt').read_text(encoding='utf-8') == 'on'
_e.alternar_banda_app()
# Caída: soltada arriba, baja hasta apoyarse en el suelo.
_e.raiz.geometry('+100+20')
if 'sujeta' in _e.hd:
    _e.sujeta = time.time()
    _e.pintar()
    assert str(_e.lienzo.itemcget(_e.emi, 'image')) == str(_e.foto_hd('sujeta', 0))
_e.raiz.update()
_e.soltar()
_fin = time.time() + 15
while time.time() < _fin and _e.raiz.winfo_y() < _e.suelo() - _e.tam()[1]:
    _e.raiz.update()
    time.sleep(0.01)
assert _e.raiz.winfo_y() == _e.suelo() - _e.tam()[1], ('no cayó al suelo', _e.raiz.winfo_y())
if 'caida' in _e.hd:
    for _ in range(20):
        if _e.caida_fase and _e.caida_fase[0] == 'aterriza':
            break
        _e.raiz.update(); time.sleep(0.02)
    assert _e.caida_fase is not None and _e.caida_fase[0] == 'aterriza' and 4 <= _e.fotograma_caida() <= 7
    _e.raiz.after(10, _e.fin_caida)
    _e.raiz.update(); time.sleep(0.05); _e.raiz.update()
    assert _e.caida_fase is None
# Sin caída: se queda donde la sueltas y ese pasa a ser su sitio.
_e.movimiento += 1  # corta la vuelta que dejó la caída de arriba
_e.caminando = None
_e.caida = False
_e.casa_x = 300
_e.raiz.geometry('+200+%d' % (_e.suelo() - _e.tam()[1]))
_e.raiz.update()
_e.soltar()
_e.raiz.update()
assert _e.caminando is None and _e.casa_x == _e.raiz.winfo_x() == 200, ('sin caída no debe moverse', _e.caminando, _e.casa_x, _e.raiz.winfo_x())
# Caminar: lejos de su sitio, vuelve caminando en horizontal.
_e.casa_x = 300
_e.volver()
_e.raiz.update()
assert _e.caminando is not None and _e.caminando[1] == 1
if 'caminando' in _e.hd:
    _e.pintar()
_fin = time.time() + 15
while time.time() < _fin and _e.caminando is not None:
    _e.raiz.update(); time.sleep(0.005)
assert _e.raiz.winfo_x() == 300 and _e.caminando is None, ('no volvió a su sitio', _e.raiz.winfo_x())
# Paseo: va a un punto cercano y, tras 3 s, vuelve a su sitio.
_e.pasear()
_e.raiz.update()
assert _e.caminando is not None, 'el paseo no arrancó'
_fin = time.time() + 15
while time.time() < _fin and _e.caminando is not None and abs(_e.raiz.winfo_x() - 300) < 100:
    _e.raiz.update(); time.sleep(0.005)
assert abs(_e.raiz.winfo_x() - 300) >= 100, ('el paseo no se alejó', _e.raiz.winfo_x())
_e.movimiento += 1  # corta la vuelta pendiente
_e.caida = True
_e.cerrar_panel()
assert _e.panel is None and _e.lienzo.itemcget(_e.emi, 'state') == 'normal'
_e.usado = None
_e.dibujar_uso()
assert not _e.lienzo.find_withtag('uso')
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
