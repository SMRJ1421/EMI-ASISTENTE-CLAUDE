"""Emi en el escritorio: una ventana transparente, siempre visible, que muestra el estado de Emi aunque Claude esté minimizado.

Lo lanza el mod (al abrir una sesión) y se cierra solo cuando ya no queda ninguna sesión de Claude abierta.
Lee el estado de ~/.claude/mascota/sesiones/*.json (lo escribe el mod) y los fotogramas de escritorio/frames/*.png
(los genera exportar_frames.py). Solo usa Python 3 con tkinter (sin Pillow); no abre red ni toca nada fuera de ~/.claude/mascota.
Arrastra a Emi para moverla; clic derecho: tamaño o cerrar. /emi sin-escritorio también la cierra.
"""
import json
import os
import random
import socket
import sys
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
FRAMES = AQUI / 'frames'
HD = AQUI / 'hd'  # originales de 1254x1254 (los copia exportar_frames.py); los estados que los tienen se ven casi a su resolución
HD_LADO = 1254
SUBMUESTREO = {1: 7, 2: 5, 3: 3}  # tamaño Pequeña/Mediana/Grande -> 1254/7=179 px, 1254/5=250 px, 1254/3=418 px. El arte tiene celdas de ~18 px: saltar de a 3-7 px conserva los bloques
DATOS = Path(os.environ.get('EMI_DATOS') or Path.home() / '.claude' / 'mascota')  # EMI_DATOS solo para pruebas
SESIONES = DATOS / 'sesiones'
CONFIG = DATOS / 'escritorio.json'
INTERRUPTOR = DATOS / 'escritorio.txt'  # «off» la cierra; el mod lo escribe con /emi escritorio | sin-escritorio
PUERTO = int(os.environ.get('EMI_PUERTO') or 47231)  # una sola Emi por equipo: si el puerto está ocupado, ya hay otra y esta se va
FONDO_GLOBO, BORDE_GLOBO = '#fffdf5', '#b79ae0'
ALFA_GLOBO = 0.45  # opacidad del globo con el ratón encima
CLAVE = '#fe00fe'  # color que Windows deja transparente
SIN_SENAL = 35  # s sin señal de una conversación: se da por cerrada (igual que en el mod)
GRACIA = 8  # s sin ninguna conversación viva antes de irse
PASO_S = 0.2  # cada dibujo dura 200 ms (5 fps) en cualquier animación
ACTIVOS = {'guardando', 'pensando', 'responde', 'leyendo', 'escribiendo', 'necesita', 'falla', 'para', 'terminado', 'baile'}  # estados con globo de mensaje
# Frase por defecto del globo cuando el mod (una versión anterior) no la publica.
FRASE_BASE = {'guardando': 'guardando en mi segundo cerebro…', 'pensando': 'pensando…', 'responde': 'respondiendo…', 'leyendo': 'leyendo…', 'escribiendo': 'escribiendo…', 'necesita': '¡te necesito!', 'falla': 'algo falló', 'para': 'me detuve', 'terminado': '¡listo!', 'baile': '¡terminé un encargo largo!'}
PRIORIDAD = {'guardando': 3, 'necesita': 6, 'falla': 5, 'para': 5, 'baile': 4, 'terminado': 4, 'pensando': 3, 'responde': 3, 'leyendo': 3, 'escribiendo': 3}


def cargar_frames() -> dict[str, list[tk.PhotoImage]]:
    """Los PNG de frames/ (Tk 8.6 los lee con su transparencia); hay que crear la ventana raíz antes."""
    por_estado: dict[str, list[tk.PhotoImage]] = {}
    for archivo in sorted(FRAMES.glob('*_*.png')):
        estado = archivo.stem.rsplit('_', 1)[0]
        por_estado.setdefault(estado, []).append(tk.PhotoImage(file=str(archivo)))
    return por_estado


def rutas_hd() -> dict[str, list[Path]]:
    """estado -> PNG grandes en orden (pensando_0, pensando_1...). Se cargan por demanda: 1254x1254 son ~6 MB de memoria cada uno."""
    por_estado: dict[str, list[Path]] = {}
    for archivo in sorted(HD.glob('*_*.png'), key=lambda a: (a.stem.rsplit('_', 1)[0], int(a.stem.rsplit('_', 1)[1]))):
        por_estado.setdefault(archivo.stem.rsplit('_', 1)[0], []).append(archivo)
    return por_estado


def oscurecer(color: str, factor: float = 0.7) -> str:
    """El color del estado (el mismo de la frase en Claude) un 30 % más oscuro, para que se lea sobre el fondo crema del globo."""
    try:
        r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
        return '#%02x%02x%02x' % (int(r * factor), int(g * factor), int(b * factor))
    except (ValueError, IndexError):
        return '#6a4fb5'


ALFA_LEJOS = 0.4  # opacidad de Emi cuando no estás en Claude ni en el escritorio
APPS_CLAUDE = {'claude.exe', 'windowsterminal.exe'}  # la app de Claude y la terminal donde corre Claude Code


def ventana_delante() -> str:
    """Qué hay en primer plano: 'claude', 'escritorio', 'emi' u 'otra'. Solo Windows; en otro sistema, 'claude' (no atenúa)."""
    if sys.platform != 'win32':
        return 'claude'
    import ctypes
    from ctypes import wintypes
    u, k = ctypes.windll.user32, ctypes.windll.kernel32
    h = u.GetForegroundWindow()
    if not h:
        return 'escritorio'
    clase = ctypes.create_unicode_buffer(64)
    u.GetClassNameW(h, clase, 64)
    if clase.value in ('Progman', 'WorkerW', 'Shell_TrayWnd', 'Shell_SecondaryTrayWnd'):
        return 'escritorio'  # el fondo de pantalla o la barra de tareas
    pid = wintypes.DWORD()
    u.GetWindowThreadProcessId(h, ctypes.byref(pid))
    if pid.value == os.getpid():
        return 'emi'
    proc = k.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not proc:
        return 'otra'
    try:
        ruta = ctypes.create_unicode_buffer(260)
        n = wintypes.DWORD(260)
        k.QueryFullProcessImageNameW(proc, 0, ruta, ctypes.byref(n))
    finally:
        k.CloseHandle(proc)
    return 'claude' if Path(ruta.value).name.lower() in APPS_CLAUDE else 'otra'


def leer_config() -> dict:
    try:
        return json.loads(CONFIG.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def sesiones_vivas() -> list[dict]:
    vivas = []
    try:
        for archivo in SESIONES.glob('*.json'):
            try:
                d = json.loads(archivo.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                continue  # un archivo a medio escribir: se lee en la siguiente pasada
            if not d.get('cerrada') and time.time() - d.get('vivo', 0) / 1000 < SIN_SENAL:
                vivas.append(d)
    except OSError:
        pass
    return vivas


ESTADOS_USO = ('nueva', 'pensando', 'responde', 'leyendo', 'escribiendo', 'necesita', 'falla', 'para', 'terminado', 'hula', 'duerme', 'guardando', 'caida', 'sujeta', 'caminando')  # los 12 en uso, y caída y sujeta (solo Emi escritorio), para el cuadro
ANCHO_BARRA, ALTO_BARRA = 90, 196  # barras verticales (uso y caché) con el marco de arte/barra-emi-claude
SEP_BARRAS = 2  # px vacíos entre Emi y la primera barra, y entre las dos barras
MARCO = AQUI / 'marco_barra.png'  # lo genera exportar_frames.py
MARCO_HUECO = (36, 39, 55, 160)  # x0, y0, x1, y1 del interior del marco, donde va el relleno (lo imprime exportar_frames.py)


def falta(reinicio) -> str:
    # Tiempo hasta que se renueva la sesión actual, corto para caber sobre la barra: «2h10m», «35m»; vacío si no hay dato.
    if not isinstance(reinicio, str):
        return ''
    try:
        seg = datetime.fromisoformat(reinicio.replace('Z', '+00:00')).timestamp() - time.time()
    except ValueError:
        return ''
    if seg <= 0:
        return ''
    h, m = divmod(int(seg // 60), 60)
    return f'{h}h{m:02d}m' if h else f'{max(1, m)}m'


BARRAS = {'uso': 'Barra de uso de la sesión', 'cache': 'Barra del caché', 'tiempo': 'Tiempo trabajado'}  # interruptores de la tuerca
UI = AQUI / 'interfaz'  # piezas del panel de configuración (las genera exportar_frames.py desde arte\\interfaz)
TINTA_PANEL, ROJO_PANEL = '#5b1a2c', '#e0344f'
PANEL_Y0 = 178  # y de la primera fila, bajo la cabecera
NOMBRES_PANEL = {**BARRAS, 'cuadro': 'Ver cuadro de estados', 'oculta': 'Ocultar a Emi', 'caida': 'Caída al soltar', 'banda_app': 'Emi en la app de Claude', 'atenuar': 'Atenuar fuera de Claude'}
# (clave, acción): en ese orden van las filas del panel; el icono es interfaz\\icono_<clave>.png. Todas llevan interruptor.
FILAS_PANEL = [
    ('uso', lambda e: e.alternar_barra('uso')),
    ('cache', lambda e: e.alternar_barra('cache')),
    ('tiempo', lambda e: e.alternar_barra('tiempo')),
    ('cuadro', lambda e: e.alternar_cuadro()),
    ('oculta', lambda e: e.alternar_oculta()),
    ('caida', lambda e: e.alternar_caida()),
    ('banda_app', lambda e: e.alternar_banda_app()),
    ('atenuar', lambda e: e.alternar_atenuar()),
]
PASEO_S = 60  # tras 1 min sin nada que hacer, Emi pasea
CACHE_S = 3600  # el caché de la conversación dura 1 h desde la última petición (5 min si la cuenta pasa a sobreconsumo)


def cache_queda(actividad) -> float | None:
    # Segundos que le quedan al caché; None si no hay dato.
    if not isinstance(actividad, (int, float)) or actividad <= 0:
        return None
    return max(0.0, CACHE_S - (time.time() - actividad / 1000))


def texto_cache(actividad) -> str:
    queda = cache_queda(actividad)
    return '' if queda is None else f'{int(queda // 60)}m' if queda >= 60 else ('0m' if queda <= 0 else '<1m')


def color_cache(queda: float) -> str:
    return '#3fa66b' if queda > 1800 else '#e59a2f' if queda > 600 else '#d9434b'


def texto_trabajado(ms) -> str:
    # Tiempo que Claude lleva trabajando en la conversación: «45s», «2m 30s», «1h 05m».
    if not isinstance(ms, (int, float)) or ms < 1000:
        return ''
    s = int(ms // 1000)
    if s < 60:
        return f'{s}s'
    if s < 3600:
        return f'{s // 60}m {s % 60:02d}s'
    return f'{s // 3600}h {s % 3600 // 60:02d}m'


def color_uso(usado: float) -> str:
    # Verde hasta la mitad, ámbar hasta el 80 % y rojo después.
    return '#3fa66b' if usado < 50 else '#e59a2f' if usado < 80 else '#d9434b'


def fotograma_de(estado: str, desde: float, cuantos: int) -> int:
    # Todos los estados van a 5 fps: lo mismo que PASO_MS en el mod.
    return int(max(0.0, time.time() - desde) / PASO_S) % max(1, cuantos)


class Emi:
    def __init__(self) -> None:
        self.raiz = tk.Tk()
        self.frames = cargar_frames()
        if not self.frames:
            sys.exit(0)
        self.config = leer_config()
        self.escala = int(self.config.get('escala', 2))
        self.estado = 'hula'
        self.desde = time.time()
        self.sin_sesiones_desde: float | None = None
        self.cache: dict[tuple, tk.PhotoImage] = {}
        self.hd = rutas_hd()
        self.mensaje = bool(self.config.get('mensaje', True))
        self.color = ''
        self.texto = ('', '')  # (frase, detalle) que muestra el globo
        self.x_barras = 0  # lo fija mostrar() con el primer dibujo
        self.pendientes = [(e, i) for e, rs in self.hd.items() for i in range(len(rs))]

        self.raiz.overrideredirect(True)
        self.raiz.attributes('-topmost', True)
        self.raiz.config(bg=CLAVE)
        self.raiz.attributes('-transparentcolor', CLAVE)
        # Un solo lienzo para Emi y las barras: así los huecos transparentes de uno no tapan al otro y las barras pueden ir pegadas a ella.
        self.lienzo = tk.Canvas(self.raiz, bg=CLAVE, bd=0, highlightthickness=0)
        self.lienzo.place(x=0, y=0, relwidth=1, relheight=1)
        self.emi = self.lienzo.create_image(0, 0, anchor='s')  # la coloca poner_emi() desde colocar()
        self.lienzo.tag_bind(self.emi, '<ButtonPress-1>', self.empezar_arrastre)
        self.lienzo.tag_bind(self.emi, '<B1-Motion>', self.arrastrar)
        self.lienzo.tag_bind(self.emi, '<ButtonRelease-1>', lambda _e: self.soltar())
        self.lienzo.tag_bind(self.emi, '<Button-3>', self.menu)
        # Globo de mensaje: una ventanita aparte, opaca (el texto suavizado no se mezcla bien con el color transparente), junto a Emi.
        self.globo = tk.Toplevel(self.raiz)
        self.globo.overrideredirect(True)
        self.globo.attributes('-topmost', True)
        self.globo.config(bg=BORDE_GLOBO)
        cuerpo = tk.Frame(self.globo, bg=FONDO_GLOBO)
        cuerpo.pack(padx=2, pady=2)
        self.l_frase = tk.Label(cuerpo, bg=FONDO_GLOBO, fg='#6a4fb5', font=('Segoe UI', 10, 'bold'), wraplength=230, justify='left', anchor='w')
        self.l_detalle = tk.Label(cuerpo, bg=FONDO_GLOBO, fg='#555555', font=('Segoe UI', 9), wraplength=230, justify='left', anchor='w')
        self.l_frase.pack(padx=8, pady=(5, 0), anchor='w')
        self.l_detalle.pack(padx=8, pady=(0, 5), anchor='w')
        # Con el ratón encima, el globo se vuelve semitransparente para ver lo que hay detrás.
        self.globo.bind('<Enter>', lambda _e: self.globo.attributes('-alpha', ALFA_GLOBO))
        self.globo.bind('<Leave>', lambda _e: self.raiz.after(30, self.globo_opaco))
        # Uso del límite de la sesión actual: barra vertical opaca a la derecha de Emi, que se llena desde abajo, con el % dentro.
        self.usado = None
        # Encima de la barra: cuánto falta para que se renueve la sesión actual.
        self.reinicio = None
        self.l_reinicio = tk.Label(self.raiz, bg='#ece6f5', fg='#2b2b2b', font=('Segoe UI', 7, 'bold'), bd=0, padx=2)
        # Segunda barra, a la izquierda de la de uso: tiempo que le queda al caché de la conversación (1 h) antes de «perder el contexto».
        self.actividad = None
        self.texto_cache_visto = ''
        self.marco = tk.PhotoImage(file=str(MARCO))
        self.l_cache = tk.Label(self.raiz, text='caché', bg='#ece6f5', fg='#2b2b2b', font=('Segoe UI', 6, 'bold'), bd=0, padx=1)
        # Tuerca de configuración: siempre visible bajo la barra, aunque la barra esté apagada o Emi oculta.
        # Cada barra se enciende y apaga por separado desde la tuerca (antes un solo interruptor «barra» para todas).
        todas = bool(self.config.get('barra', True))
        self.barras = {k: bool(self.config.get(f'barra_{k}', todas)) for k in BARRAS}
        self.oculta = bool(self.config.get('oculta', False))
        self.movimiento = 0  # sube cada vez que la agarras: corta caídas y paseos en curso
        self.quieta_desde = time.time()  # desde cuándo Emi no tiene nada que hacer (para el paseo)
        self.caminando: tuple[float, int] | None = None  # (desde, sentido) mientras vuelve a su sitio
        self.casa_x = int(self.config.get('casa_x', self.config.get('x', self.raiz.winfo_screenwidth() - 300)))  # su sitio: adonde vuelve caminando
        self.sujeta: float | None = None  # desde cuándo la sujeta el cursor (solo Emi escritorio)
        self.caida_fase: tuple[str, float] | None = None  # ('cae' | 'aterriza', desde): la animación de caída, solo en Emi escritorio
        self.banda_app = (DATOS / 'banda_app.txt').exists() and (DATOS / 'banda_app.txt').read_text(encoding='utf-8').strip() == 'on'  # la banda de Emi en la app de Claude: apagada por defecto
        self.caida = bool(self.config.get('caida', True))  # al soltarla, cae hasta el suelo (encima de la barra de tareas)
        self.atenuar = bool(self.config.get('atenuar', True))  # fuera de Claude y del escritorio, Emi baja al 40 %
        self.alfa = 1.0  # opacidad actual de Emi y su globo
        self.panel: tk.Toplevel | None = None
        self.agarre_panel = None  # (x, y) donde agarraste la barra de título del panel
        self.tuerca = tk.Label(self.raiz, text='⚙', bg='#ece6f5', fg='#6a4fb5', font=('Segoe UI Symbol', 11), bd=0, padx=3, cursor='hand2')
        self.tuerca.bind('<Button-1>', lambda _e: self.abrir_panel())
        # A la izquierda de la tuerca: cuánto tiempo ha trabajado Claude en la conversación (suma los turnos; el que está en marcha cuenta en vivo).
        self.l_trabajo = tk.Label(self.raiz, bg='#ece6f5', fg='#2b2b2b', font=('Segoe UI', 8, 'bold'), bd=0, padx=4, pady=1)
        if self.oculta:
            self.lienzo.itemconfig(self.emi, state='hidden')
        self.globo.withdraw()
        self.colocar()
        self.pintar()
        self.raiz.after(500, self.sondear)
        self.raiz.after(100, self.animar)
        self.raiz.after(1500, self.precargar)
        self.raiz.after(700, self.vigilar_foco)
        self.raiz.after(2000, self.mantener_arriba)

    # ---- ventana ----
    def tam(self) -> tuple[int, int]:
        base = next(iter(self.frames.values()))[0]
        ancho, alto = base.width() * self.escala, base.height() * self.escala
        if self.hd:
            lado = -(-HD_LADO // SUBMUESTREO.get(self.escala, 5))  # subsample redondea hacia arriba
            ancho, alto = max(ancho, lado), max(alto, lado)
        return ancho, alto

    def margen(self) -> int:
        # Franja de las barras a la derecha de la zona de Emi; las barras se acercan a ella según su dibujo (ver mostrar()).
        return ANCHO_BARRA + self.paso_barras() + 4

    def perfil(self, foto: tk.PhotoImage, derecha: bool) -> list[int | None]:
        # Por fila: la última (derecha) o la primera columna pintada; None si la fila está vacía. Una vez por imagen.
        clave = ('perfil', str(foto), derecha)
        if clave not in self.cache:
            ancho = foto.width()
            cols = range(ancho - 1, -1, -1) if derecha else range(ancho)
            self.cache[clave] = [next((c for c in cols if not foto.transparency_get(c, y)), None) for y in range(foto.height())]
        return self.cache[clave]

    def x_de(self, foto: tk.PhotoImage) -> int:
        # Dónde empieza la primera barra para que su marco quede a 2 px de este dibujo, fila por fila (los lazos entran en sus huecos).
        w, h = self.tam()
        ex, ey = w // 2 - foto.width() // 2, h - foto.height()
        by = (h - ALTO_BARRA) // 2
        emi, marco = self.perfil(foto, True), self.perfil(self.marco, False)
        lim = [ex + emi[by + j - ey] + 1 + SEP_BARRAS - m for j, m in enumerate(marco)
               if m is not None and 0 <= by + j - ey < len(emi) and emi[by + j - ey] is not None]
        return max(lim) if lim else ex + foto.width()

    def paso_barras(self) -> int:
        # De una barra a la siguiente: los dos marcos a 2 px en su fila más cercana (los lazos).
        der, izq = self.perfil(self.marco, True), self.perfil(self.marco, False)
        return max(d + 1 + SEP_BARRAS - i for d, i in zip(der, izq) if d is not None)

    def mostrar(self, foto: tk.PhotoImage, grupo, todas) -> None:
        # Pone el dibujo. Las barras se calculan para todos los dibujos del estado a la vez (el más ancho manda):
        # así no bailan con la animación, pero sí se acercan o se alejan cuando Emi cambia de estado.
        self.lienzo.itemconfig(self.emi, image=foto)
        clave = ('xb', grupo, self.escala)
        if clave not in self.cache:
            self.cache[clave] = max(self.x_de(f) for f in [*todas(), foto] if f is not None)
        x = self.cache[clave]
        if x != self.x_barras:
            self.x_barras = x
            self.dibujar_uso()
            tope = self.raiz.winfo_screenwidth() - x - self.paso_barras() - ANCHO_BARRA  # que la barra de uso no se salga por la derecha
            if self.raiz.winfo_x() > tope:
                self.raiz.geometry(f'+{tope}+{self.raiz.winfo_y()}')

    def poner_emi(self) -> None:
        # Abajo y centrada en su zona (la ventana es más ancha por las barras): todos los estados apoyan los pies en el mismo sitio.
        if not self.oculta:
            w, h = self.tam()
            self.lienzo.coords(self.emi, w // 2, h)
            self.lienzo.itemconfig(self.emi, state='normal')

    def colocar(self) -> None:
        w, h = self.tam()
        x = self.config.get('x', self.raiz.winfo_screenwidth() - w - 40)
        y = self.config.get('y', self.raiz.winfo_screenheight() - h - 80)
        x = min(max(0, x), self.raiz.winfo_screenwidth() - (self.x_barras or w // 2) - self.paso_barras() - ANCHO_BARRA)  # que la barra de uso no se salga; lo transparente de la derecha sí puede
        y = min(max(0, y), self.raiz.winfo_screenheight() - 40)
        self.raiz.geometry(f'{w + self.margen()}x{h}+{x}+{y}')
        self.poner_emi()
        self.raiz.after(50, self.colocar_globo)
        self.dibujar_uso()

    def dibujar_uso(self) -> None:
        alto = ALTO_BARRA
        by = (self.tam()[1] - alto) // 2  # borde de arriba de las barras
        self.lienzo.delete('barra')
        xb = self.x_barras  # borde izquierdo de la primera barra (la de caché)
        fin = xb + self.paso_barras() + ANCHO_BARRA
        self.tuerca.place(x=fin, rely=0.5, y=alto / 2 + 3, anchor='ne')
        texto = self.l_trabajo.cget('text')
        (self.l_trabajo.place(x=fin - 28, rely=0.5, y=alto / 2 + 5, anchor='ne') if self.barras['tiempo'] and texto else self.l_trabajo.place_forget())
        queda = cache_queda(self.actividad)
        if self.barras['cache'] and queda is not None:
            self.pintar_barra('cache', xb, by, queda / CACHE_S, color_cache(queda), texto_cache(self.actividad))
            self.l_cache.place(x=xb + ANCHO_BARRA / 2, rely=0.5, y=-alto / 2 - 3, anchor='s')
        else:
            self.l_cache.place_forget()
        if not self.barras['uso'] or not isinstance(self.usado, (int, float)):
            self.l_reinicio.place_forget()
            return
        u = max(0.0, min(100.0, float(self.usado)))
        self.pintar_barra('uso', xb + self.paso_barras(), by, u / 100, color_uso(u), f'{u:.0f}%')
        texto = falta(self.reinicio)
        self.l_reinicio.config(text=texto)
        (self.l_reinicio.place(x=xb + self.paso_barras() + ANCHO_BARRA / 2, rely=0.5, y=-alto / 2 - 3, anchor='s') if texto else self.l_reinicio.place_forget())

    def pintar_barra(self, nombre: str, bx: int, by: int, fraccion: float, color: str, texto: str) -> None:
        # Fondo claro y relleno desde abajo en el hueco, el marco encima y el texto en horizontal arriba (en el medio lo tapan las gemas del marco).
        x0, y0, x1, y1 = MARCO_HUECO
        x0, y0, x1, y1 = x0 + bx, y0 + by, x1 + bx, y1 + by
        c, et = self.lienzo, ('barra', nombre)
        c.create_rectangle(x0, y0, x1, y1, fill='#f0e9f4', width=0, tags=et)
        c.create_rectangle(x0, y1 - round((y1 - y0) * max(0.0, min(1.0, fraccion))), x1, y1, fill=color, width=0, tags=et)
        c.create_image(bx, by, image=self.marco, anchor='nw', tags=et)
        if texto:  # pastilla clara: el número es más ancho que el hueco y pisa el borde del marco
            t = c.create_text((x0 + x1) / 2, y0 + 12, text=texto, font=('Segoe UI', 7, 'bold'), fill='#2b2b2b', tags=et)
            a0, b0, a1, b1 = c.bbox(t)
            c.tag_lower(c.create_rectangle(a0 - 2, b0, a1 + 2, b1, fill='#f0e9f4', outline=BORDE_GLOBO, tags=et), t)

    def guardar(self) -> None:
        self.config.update(x=self.raiz.winfo_x(), y=self.raiz.winfo_y(), escala=self.escala, mensaje=self.mensaje, **{f'barra_{k}': v for k, v in self.barras.items()}, oculta=self.oculta, caida=self.caida, atenuar=self.atenuar, casa_x=self.casa_x)
        try:
            DATOS.mkdir(parents=True, exist_ok=True)
            CONFIG.write_text(json.dumps(self.config), encoding='utf-8')
        except OSError:
            pass

    def empezar_arrastre(self, e: tk.Event) -> None:
        self.dx, self.dy = e.x, e.y
        self.sujeta = time.time()  # mientras el botón siga pulsado, Emi pone la animación «sujeta»
        self.movimiento += 1  # cancela una caída o un paseo en curso
        self.quieta_desde = time.time()
        self.caida_fase = self.caminando = None

    def arrastrar(self, e: tk.Event) -> None:
        self.raiz.geometry(f'+{self.raiz.winfo_x() + e.x - self.dx}+{self.raiz.winfo_y() + e.y - self.dy}')
        self.colocar_globo()

    def suelo(self) -> int:
        """La y del borde inferior del área útil de Windows (encima de la barra de tareas)."""
        try:
            import ctypes
            import ctypes.wintypes
            r = ctypes.wintypes.RECT()
            if ctypes.windll.user32.SystemParametersInfoW(0x30, 0, ctypes.byref(r), 0):  # SPI_GETWORKAREA
                return r.bottom
        except (AttributeError, OSError):
            pass
        return self.raiz.winfo_screenheight() - 40

    def soltar(self) -> None:
        self.sujeta = None
        if self.caida:
            self.caer()
        else:  # sin caída, se queda justo donde la soltaste: ese pasa a ser su sitio
            self.casa_x = self.raiz.winfo_x()
            self.guardar()

    def caer(self, v: float = 0.0, mov: int | None = None) -> None:
        """Baja acelerando (un paso cada 16 ms) hasta apoyar el borde inferior de Emi en el suelo; si ya está abajo, no sube."""
        mov = self.movimiento if mov is None else mov
        if mov != self.movimiento:
            return  # la volvieron a agarrar
        x, y = self.raiz.winfo_x(), self.raiz.winfo_y()
        destino = self.suelo() - self.tam()[1]
        if y >= destino:
            if self.caida_fase is not None:
                # Toca el suelo: aterriza y se levanta (fotogramas 5 a 8) y vuelve a su estado.
                self.caida_fase = ('aterriza', time.time())
                self.raiz.after(round(4 * PASO_S * 1000), self.fin_caida)
            else:
                self.volver()
            return self.guardar()
        if v == 0.0 and 'caida' in self.hd:
            self.caida_fase = ('cae', time.time())
        v += 1.5
        self.raiz.geometry(f'+{x}+{min(destino, round(y + v))}')
        self.colocar_globo()
        self.raiz.after(16, self.caer, v, mov)

    def volver(self) -> None:
        self.caminar_a(self.casa_x)

    def caminar_a(self, destino: int, despues=None, mov: int | None = None) -> None:
        """Camina en horizontal (2 px cada 16 ms) hasta `destino`, con la animación «caminando» mirando hacia donde va."""
        if mov is None:
            self.movimiento += 1  # un paseo nuevo cancela el que estuviera en marcha
            mov = self.movimiento
        if mov != self.movimiento:
            return
        x, y = self.raiz.winfo_x(), self.raiz.winfo_y()
        falta_x = destino - x
        if abs(falta_x) <= 2:
            if self.caminando is not None:
                self.raiz.geometry(f'+{destino}+{y}')
                self.caminando = None
                self.quieta_desde = time.time()
                self.colocar_globo()
                self.guardar()
            if despues:
                despues()
            return
        if self.caminando is None:
            self.caminando = (time.time(), 1 if falta_x > 0 else -1)
        self.raiz.geometry(f'+{x + (2 if falta_x > 0 else -2)}+{y}')
        self.colocar_globo()
        self.raiz.after(16, self.caminar_a, destino, despues, mov)

    def pasear(self) -> None:
        """Tras 1 min sin nada que hacer: da un paseo a un punto cercano, se queda 3 s y vuelve a su sitio."""
        w = self.raiz.winfo_width()
        destino = self.casa_x + random.choice((-1, 1)) * random.randint(120, 300)
        destino = min(max(0, destino), self.raiz.winfo_screenwidth() - w)

        def al_llegar() -> None:
            mov = self.movimiento  # si en esos 3 s la agarras o empieza otro paseo, no vuelve
            self.raiz.after(3000, lambda: mov == self.movimiento and self.volver())

        self.caminar_a(destino, al_llegar)

    def menu(self, e: tk.Event) -> None:
        m = tk.Menu(self.raiz, tearoff=0)
        for nombre, escala in (('Pequeña', 1), ('Mediana', 2), ('Grande', 3)):
            m.add_command(label=nombre, command=lambda s=escala: self.cambiar_escala(s))
        m.add_separator()
        m.add_command(label=('✓ ' if self.mensaje else '    ') + 'Mensaje junto a Emi', command=self.alternar_mensaje)
        m.add_command(label='Cerrar Emi', command=self.cerrar)
        m.tk_popup(e.x_root, e.y_root)

    def cambiar_escala(self, escala: int) -> None:
        self.escala = escala
        self.pendientes = [(e, i) for e, rs in self.hd.items() for i in range(len(rs))]
        self.raiz.after(200, self.precargar)
        self.colocar()
        self.pintar()
        self.guardar()

    # ---- panel de configuración (la tuerca) ----
    def abrir_panel(self) -> None:
        """Panel de configuración con el arte de arte\\interfaz: ventana propia (sin el marco de Windows) que se arrastra por su barra de título."""
        if self.panel is not None:
            self.panel.deiconify()
            self.panel.lift()
            return
        p = self.panel = tk.Toplevel(self.raiz)
        p.title('Emi — configuración')
        p.overrideredirect(True)
        p.attributes('-topmost', True)
        p.config(bg=CLAVE)
        p.attributes('-transparentcolor', CLAVE)
        self.ui = {n: tk.PhotoImage(file=str(UI / f'{n}.png')) for n in ('fondo', 'fila', 'fila_encima', 'interruptor_si', 'interruptor_no', 'cabecera', *(f'icono_{k}' for k, _ in FILAS_PANEL))}
        c = self.c_panel = tk.Canvas(p, width=self.ui['fondo'].width(), height=self.ui['fondo'].height(), bg=CLAVE, highlightthickness=0, bd=0)
        c.pack()
        c.create_image(0, 0, image=self.ui['fondo'], anchor='nw')
        titulo = c.create_text(110, 41, text='Emi…', anchor='w', font=('Segoe UI', 12, 'bold'), fill=TINTA_PANEL)
        a0, b0, a1, b1 = c.bbox(titulo)
        c.tag_lower(c.create_rectangle(a0 - 4, b0, a1 + 4, b1, fill='#fcf3e6', outline=''), titulo)  # tapa la línea de la barra de título
        c.tag_raise(titulo)
        # Cabecera: Emi asomando y su nombre.
        c.create_image(26, 182, image=self.ui['cabecera'], anchor='sw')  # la barra en la que se apoya queda sobre la primera fila
        c.create_text(298, 118, text='Emi ♥', font=('Segoe Script', 24, 'bold'), fill=ROJO_PANEL)
        for x, y in ((205, 92), (240, 140), (348, 88), (32, 100)):
            c.create_text(x, y, text='✦', font=('Segoe UI Symbol', 10), fill='#f08a4b')
        self.filas_panel: dict[str, dict] = {}
        for i, (k, accion) in enumerate(FILAS_PANEL):
            y = PANEL_Y0 + i * (self.ui['fila'].height() + 6)
            etq = f'fila_{k}'
            fondo = c.create_image(25, y, image=self.ui['fila'], anchor='nw', tags=etq)
            c.create_image(54, y + 23, image=self.ui[f'icono_{k}'], tags=etq)
            texto = c.create_text(80, y + 23, anchor='w', font=('Segoe UI', 9, 'bold'), fill=TINTA_PANEL, tags=etq)
            interruptor = c.create_image(334, y + 23, anchor='e', tags=etq)
            self.filas_panel[k] = {'texto': texto, 'interruptor': interruptor, 'activa': None}
            c.tag_bind(etq, '<Enter>', lambda _e, f=fondo: (c.itemconfig(f, image=self.ui['fila_encima']), c.config(cursor='hand2')))
            c.tag_bind(etq, '<Leave>', lambda _e, f=fondo: (c.itemconfig(f, image=self.ui['fila']), c.config(cursor='')))
            c.tag_bind(etq, '<Button-1>', lambda _e, a=accion: a(self))
        # Barra de título: se arrastra; botones de minimizar (se esconde, la tuerca lo vuelve a mostrar) y cerrar.
        c.tag_bind(c.create_rectangle(262, 27, 290, 55, outline='', fill=''), '<Button-1>', lambda _e: p.withdraw())
        c.tag_bind(c.create_rectangle(326, 27, 355, 55, outline='', fill=''), '<Button-1>', lambda _e: self.cerrar_panel())
        c.bind('<ButtonPress-1>', lambda e: setattr(self, 'agarre_panel', (e.x, e.y) if e.y < 62 and e.x < 258 else None))
        c.bind('<B1-Motion>', lambda e: self.agarre_panel and p.geometry(f'+{p.winfo_x() + e.x - self.agarre_panel[0]}+{p.winfo_y() + e.y - self.agarre_panel[1]}'))
        self.textos_panel()
        p.geometry(f'+{(p.winfo_screenwidth() - self.ui["fondo"].width()) // 2}+{(p.winfo_screenheight() - self.ui["fondo"].height()) // 2}')  # en el centro de la pantalla

    def cerrar_panel(self) -> None:
        if self.panel is not None:
            self.panel.destroy()
            self.panel = None

    def textos_panel(self) -> None:
        if self.panel is None:
            return
        estado = {**self.barras, 'caida': self.caida, 'banda_app': self.banda_app, 'oculta': self.oculta, 'cuadro': self.cuadro_abierto(), 'atenuar': self.atenuar}
        for k, f in self.filas_panel.items():
            self.c_panel.itemconfig(f['texto'], text=NOMBRES_PANEL[k])
            f['activa'] = estado.get(k)
            img = '' if f['activa'] is None else self.ui['interruptor_si' if f['activa'] else 'interruptor_no']
            self.c_panel.itemconfig(f['interruptor'], image=img)

    def alternar_banda_app(self) -> None:
        # El mod la lee de banda_app.txt cada 2 s y muestra u oculta la banda en la app de escritorio de Claude.
        self.banda_app = not self.banda_app
        try:
            DATOS.mkdir(parents=True, exist_ok=True)
            (DATOS / 'banda_app.txt').write_text('on' if self.banda_app else 'off', encoding='utf-8')
        except OSError:
            pass
        self.textos_panel()

    def alternar_atenuar(self) -> None:
        self.atenuar = not self.atenuar
        self.textos_panel()
        self.guardar()

    def alternar_caida(self) -> None:
        self.caida = not self.caida
        self.textos_panel()
        self.guardar()

    def alternar_barra(self, k: str) -> None:
        self.barras[k] = not self.barras[k]
        self.dibujar_uso()
        self.textos_panel()
        self.guardar()

    def alternar_oculta(self) -> None:
        self.oculta = not self.oculta
        if self.oculta:
            self.lienzo.itemconfig(self.emi, state='hidden')
            self.globo.withdraw()
        else:
            self.poner_emi()
            self.actualizar_globo(*self.texto, self.color)
        self.textos_panel()
        self.guardar()

    def filas_cuadro(self) -> list[tuple]:
        """El cuadro de estados con sus columnas fijas, sacado de los fotogramas que Emi tiene cargados."""
        ms = round(PASO_S * 1000)
        filas = []
        for e in ESTADOS_USO:
            n = len(self.hd.get(e) or self.frames.get(e) or [])
            ciclo = f'{n * PASO_S:.1f}'.replace('.', ',')
            filas.append((e, 'Nuevo naranja' if e in self.hd else 'Lila original', n, ms, round(1 / PASO_S), ciclo))
        return filas

    def cuadro_abierto(self) -> bool:
        v = getattr(self, 'cuadro', None)
        return v is not None and bool(v.winfo_exists())

    def alternar_cuadro(self) -> None:
        if self.cuadro_abierto():
            self.cuadro.destroy()
        else:
            self.ver_cuadro()
        self.textos_panel()

    def ver_cuadro(self) -> None:
        v = tk.Toplevel(self.panel or self.raiz)
        v.title('Cuadro de estados')
        v.protocol('WM_DELETE_WINDOW', lambda: (v.destroy(), self.textos_panel()))  # al cerrarlo, su interruptor se apaga
        v.resizable(False, False)
        v.attributes('-topmost', True)
        v.config(bg=FONDO_GLOBO, padx=10, pady=8)
        cab = ('Estado', 'Arte', 'Fotogramas', 'ms por dibujo', 'fps', 'Segundos por ciclo')
        for f, fila in enumerate([cab] + self.filas_cuadro()):
            for c, valor in enumerate(fila):
                tk.Label(v, text=str(valor), bg='#ece6f5' if f == 0 else FONDO_GLOBO, font=('Segoe UI', 9, 'bold' if f == 0 else 'normal'),
                         padx=6, pady=2, anchor='w').grid(row=f, column=c, sticky='we')
        self.cuadro = v

    # ---- globo de mensaje ----
    def alternar_mensaje(self) -> None:
        self.mensaje = not self.mensaje
        self.guardar()
        self.actualizar_globo(*self.texto, self.color)

    def actualizar_globo(self, frase: str, detalle: str, color: str = '') -> None:
        self.texto = (frase, detalle)
        self.l_frase.config(fg=oscurecer(color))
        if self.oculta or not self.mensaje or self.estado not in ACTIVOS or not (frase or detalle):
            self.globo.withdraw()
            return
        self.l_frase.config(text=frase)
        self.l_detalle.config(text=detalle)
        (self.l_detalle.pack_forget() if not detalle else self.l_detalle.pack(padx=8, pady=(0, 5), anchor='w'))
        self.globo.deiconify()
        self.colocar_globo()

    def globo_opaco(self) -> None:
        # <Leave> también salta al pasar entre sus etiquetas: solo vuelve a opaco si el ratón salió del globo de verdad.
        x, y = self.globo.winfo_pointerxy()
        gx, gy = self.globo.winfo_rootx(), self.globo.winfo_rooty()
        if not (gx <= x < gx + self.globo.winfo_width() and gy <= y < gy + self.globo.winfo_height()):
            self.globo.attributes('-alpha', self.alfa)

    def colocar_globo(self) -> None:
        """A la izquierda de la ventana de Emi (a la derecha si no hay sitio), a un tercio de su altura."""
        if self.globo.state() == 'withdrawn':
            return
        self.globo.update_idletasks()
        gw, gh = self.globo.winfo_reqwidth(), self.globo.winfo_reqheight()
        x, y = self.raiz.winfo_x(), self.raiz.winfo_y()
        w, h = self.raiz.winfo_width(), self.raiz.winfo_height()
        gx = x - gw - 6 if x - gw - 6 >= 0 else x + w + 6
        gy = min(max(0, y + h // 3), self.raiz.winfo_screenheight() - gh - 40)
        self.globo.geometry(f'+{gx}+{gy}')

    def cerrar(self) -> None:
        self.guardar()
        self.raiz.destroy()

    def vigilar_foco(self) -> None:
        # Cada 0,5 s mira qué ventana tienes delante: fuera de Claude y del escritorio, Emi se vuelve semitransparente.
        try:
            lejos = self.atenuar and ventana_delante() == 'otra'
        except (OSError, AttributeError, ValueError):
            lejos = False
        alfa = ALFA_LEJOS if lejos else 1.0
        if alfa != self.alfa:
            self.alfa = alfa
            self.raiz.attributes('-alpha', alfa)
            self.globo.attributes('-alpha', alfa)
        self.raiz.after(500, self.vigilar_foco)

    def mantener_arriba(self) -> None:
        self.raiz.attributes('-topmost', True)
        self.raiz.lift()
        if self.globo.state() != 'withdrawn':
            self.globo.attributes('-topmost', True)
            self.globo.lift()
        self.raiz.after(2000, self.mantener_arriba)

    # ---- dibujo ----
    def foto_hd(self, estado: str, i: int) -> tk.PhotoImage | None:
        clave = ('hd', estado, i, self.escala)
        foto = self.cache.get(clave)
        if foto is None:
            n = SUBMUESTREO.get(self.escala, 5)
            origen = self.hd[estado][i]
            # Caché de la versión reducida (la lectura de un PNG de 1254x1254 tarda ~0,6 s; la reducida, milisegundos). La clave lleva el
            # tamaño del archivo: si cambias el arte, se rehace sola.
            guardada = DATOS / 'cache_hd' / f'{origen.stem}_{n}_{origen.stat().st_size}.png'
            try:
                if guardada.exists():
                    foto = tk.PhotoImage(file=str(guardada))
                else:
                    grande = tk.PhotoImage(file=str(origen))
                    foto = grande.subsample(n)
                    del grande  # la de 1254x1254 ya no hace falta
                    try:
                        guardada.parent.mkdir(parents=True, exist_ok=True)
                        foto.write(str(guardada), format='png')
                    except (tk.TclError, OSError):
                        pass  # sin caché solo se pierde tiempo en el próximo arranque
            except (tk.TclError, OSError):
                self.hd.pop(estado, None)  # un PNG ilegible: ese estado vuelve a su dibujo pequeño
                return None
            self.cache[clave] = foto
        return foto

    def precargar(self) -> None:
        """Carga un PNG grande cada 200 ms para que el primer ciclo de cada estado no se entrecorte."""
        while self.pendientes:
            estado, i = self.pendientes.pop(0)
            if estado in self.hd and i < len(self.hd[estado]):
                self.foto_hd(estado, i)
                break
        if self.pendientes:
            self.raiz.after(200, self.precargar)

    def fin_caida(self) -> None:
        if self.caida_fase is not None and self.caida_fase[0] == 'aterriza':
            self.caida_fase = None
            self.volver()  # ya en el suelo, camina de vuelta a su sitio

    def fotograma_caida(self) -> int:
        """Mientras cae, repite los fotogramas 1 a 4; al aterrizar, pasa una vez por el 5 al 8."""
        fase, desde = self.caida_fase
        paso = int((time.time() - desde) / PASO_S)
        return paso % 4 if fase == 'cae' else min(7, 4 + paso)

    def pintar(self) -> None:
        if self.sujeta is not None and 'sujeta' in self.hd:
            foto = self.foto_hd('sujeta', fotograma_de('sujeta', self.sujeta, len(self.hd['sujeta'])))
            if foto is not None:
                self.mostrar(foto, 'sujeta', lambda: self.todas_hd('sujeta'))
                return
        if self.caida_fase is not None and 'caida' in self.hd:
            foto = self.foto_hd('caida', self.fotograma_caida())
            if foto is not None:
                self.mostrar(foto, 'caida', lambda: self.todas_hd('caida'))
                return
        if self.caminando is not None and 'caminando' in self.hd:
            desde, sentido = self.caminando
            i = fotograma_de('caminando', desde, len(self.hd['caminando']))
            foto = self.foto_hd('caminando', i)
            if foto is not None:
                if sentido < 0:  # el dibujo mira a la derecha: hacia la izquierda va reflejado
                    foto = self.espejo(i, foto)
                    self.mostrar(foto, 'caminando-izq', lambda: [self.espejo(k, f) for k, f in enumerate(self.todas_hd('caminando')) if f is not None])
                else:
                    self.mostrar(foto, 'caminando', lambda: self.todas_hd('caminando'))
                return
        if self.estado in self.hd:
            i = fotograma_de(self.estado, self.desde, len(self.hd[self.estado]))
            foto = self.foto_hd(self.estado, i)
            if foto is not None:
                self.mostrar(foto, self.estado, lambda: self.todas_hd(self.estado))
                return
        lista = self.frames.get(self.estado) or self.frames.get('hula') or next(iter(self.frames.values()))
        i = fotograma_de(self.estado, self.desde, len(lista))
        clave = (self.estado, i, self.escala)
        foto = self.cache.get(clave)
        if foto is None:
            foto = lista[i].zoom(self.escala)  # ampliación entera: píxeles cuadrados, sin suavizar
            self.cache[clave] = foto
        self.mostrar(foto, ('chico', self.estado), lambda: [f.zoom(self.escala) for f in lista])

    def todas_hd(self, estado: str) -> list:
        return [self.foto_hd(estado, k) for k in range(len(self.hd.get(estado, [])))]

    def espejo(self, i: int, foto: tk.PhotoImage) -> tk.PhotoImage:
        clave = ('espejo', i, self.escala)
        if clave not in self.cache:
            self.cache[clave] = foto.subsample(-1, 1)
        return self.cache[clave]

    def animar(self) -> None:
        self.pintar()
        self.raiz.after(100, self.animar)

    # ---- estado de Claude ----
    def sondear(self) -> None:
        try:
            if INTERRUPTOR.read_text(encoding='utf-8').strip() == 'off':
                return self.cerrar()
        except OSError:
            pass
        vivas = sesiones_vivas()
        if vivas:
            self.sin_sesiones_desde = None
            mejor = max(vivas, key=lambda d: (PRIORIDAD.get(d.get('estado') or ('pensando' if d.get('trabajando') else ''), 1), d.get('desde', 0), d.get('vivo', 0)))
            # Un mod anterior no publica el estado: se deduce de si Claude está trabajando.
            estado = mejor.get('estado') or ('pensando' if mejor.get('trabajando') else 'hula')
            if estado != self.estado:
                self.estado = estado
                self.desde = (mejor.get('desde') or time.time() * 1000) / 1000
            # Sin nada que hacer (de guardia o dormida) y quieta 1 min: sale a pasear (solo con la caída activada; sin ella no se mueve de donde la dejaste).
            libre = estado in ('hula', 'duerme') and self.sujeta is None and self.caida_fase is None and self.caminando is None
            if estado not in ('hula', 'duerme'):
                self.quieta_desde = time.time()  # Claude trabaja: el minuto vuelve a empezar
            elif libre and self.caida and not self.oculta and time.time() - self.quieta_desde >= PASEO_S:
                self.quieta_desde = time.time()
                self.pasear()
            # Debajo del detalle, el modelo que trabaja ahora (la sesión o el ayudante al que delegó).
            nuevo = (str(mejor.get('frase') or FRASE_BASE.get(estado, '')), '\n'.join(filter(None, (str(mejor.get('detalle') or ''), str(mejor.get('modelo') or '')))))
            # Las barras toman el dato de la sesión más reciente que lo tenga (otra sesión con un mod viejo no lo publica).
            con_uso = max((d for d in vivas if isinstance(d.get('usado'), (int, float))), key=lambda d: d.get('vivo', 0), default={})
            usado = con_uso.get('usado')
            self.color = str(mejor.get('color') or '')
            reinicio = con_uso.get('reinicio')
            # La cuenta atrás cambia sola con el tiempo: se redibuja cuando cambia el texto, no solo el dato.
            # Tiempo trabajado: el de la conversación que muestra Emi (o la más reciente que lo tenga), más el turno en marcha.
            con_tiempo = mejor if isinstance(mejor.get('trabajado'), (int, float)) else max((d for d in vivas if isinstance(d.get('trabajado'), (int, float))), key=lambda d: d.get('vivo', 0), default={})
            en_marcha = con_tiempo.get('inicioTurno') or 0
            texto = texto_trabajado((con_tiempo.get('trabajado') or 0) + (time.time() * 1000 - en_marcha if en_marcha else 0))
            texto = ('⏱ ' + texto) if texto else ''
            if texto != self.l_trabajo.cget('text'):
                self.l_trabajo.config(text=texto)
                self.dibujar_uso()  # la coloca (o la quita) junto a la tuerca
            actividad = max((d['actividad'] for d in vivas if isinstance(d.get('actividad'), (int, float)) and d['actividad'] > 0), default=None)
            if usado != self.usado or reinicio != self.reinicio or falta(reinicio) != self.l_reinicio.cget('text') or actividad != self.actividad or texto_cache(actividad) != self.texto_cache_visto:
                self.usado, self.reinicio, self.actividad, self.texto_cache_visto = usado, reinicio, actividad, texto_cache(actividad)
                self.dibujar_uso()
            if nuevo != self.texto or (self.estado in ACTIVOS) == (self.globo.state() == 'withdrawn'):
                self.actualizar_globo(*nuevo, self.color)
        else:
            self.sin_sesiones_desde = self.sin_sesiones_desde or time.time()
            if time.time() - self.sin_sesiones_desde > GRACIA:
                return self.cerrar()  # ya no queda ninguna conversación: Emi se despide
        self.raiz.after(500, self.sondear)


def main() -> None:
    cerrojo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        cerrojo.bind(('127.0.0.1', PUERTO))
    except OSError:
        return  # ya hay una Emi en el escritorio
    emi = Emi()
    emi.raiz.mainloop()
    cerrojo.close()


if __name__ == '__main__':
    main()
