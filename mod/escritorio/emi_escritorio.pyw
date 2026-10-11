"""Emi en el escritorio: una ventana transparente, siempre visible, que muestra el estado de Emi aunque Claude esté minimizado.

Lo lanza el mod (al abrir una sesión) y se cierra solo cuando ya no queda ninguna sesión de Claude abierta.
Lee el estado de ~/.claude/mascota/sesiones/*.json (lo escribe el mod) y los fotogramas de escritorio/frames/*.png
(los genera exportar_frames.py). Solo usa Python 3 con tkinter (sin Pillow); no abre red ni toca nada fuera de ~/.claude/mascota.
Arrastra a Emi para moverla; clic derecho: tamaño o cerrar. /emi sin-escritorio también la cierra.
"""
import json
import os
import socket
import sys
import time
import tkinter as tk
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
CLAVE = '#fe00fe'  # color que Windows deja transparente
SIN_SENAL = 35  # s sin señal de una conversación: se da por cerrada (igual que en el mod)
GRACIA = 8  # s sin ninguna conversación viva antes de irse
PASO_S = 0.2  # cada dibujo dura 200 ms (5 fps) en cualquier animación
ACTIVOS = {'pensando', 'responde', 'leyendo', 'escribiendo', 'necesita', 'falla', 'para', 'terminado', 'baile'}  # estados con globo de mensaje
# Frase por defecto del globo cuando el mod (una versión anterior) no la publica.
FRASE_BASE = {'pensando': 'pensando…', 'responde': 'respondiendo…', 'leyendo': 'leyendo…', 'escribiendo': 'escribiendo…', 'necesita': '¡te necesito!', 'falla': 'algo falló', 'para': 'me detuve', 'terminado': '¡listo!', 'baile': '¡terminé un encargo largo!'}
PRIORIDAD = {'necesita': 6, 'falla': 5, 'para': 5, 'baile': 4, 'terminado': 4, 'pensando': 3, 'responde': 3, 'leyendo': 3, 'escribiendo': 3}


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
        self.pendientes = [(e, i) for e, rs in self.hd.items() for i in range(len(rs))]

        self.raiz.overrideredirect(True)
        self.raiz.attributes('-topmost', True)
        self.raiz.config(bg=CLAVE)
        self.raiz.attributes('-transparentcolor', CLAVE)
        self.etiqueta = tk.Label(self.raiz, bg=CLAVE, bd=0, highlightthickness=0)
        self.etiqueta.place(relx=0.5, rely=1.0, anchor='s')  # abajo y centrada: todos los estados apoyan los pies en el mismo sitio
        self.etiqueta.bind('<ButtonPress-1>', self.empezar_arrastre)
        self.etiqueta.bind('<B1-Motion>', self.arrastrar)
        self.etiqueta.bind('<ButtonRelease-1>', lambda _e: self.guardar())
        self.etiqueta.bind('<Button-3>', self.menu)
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
        self.globo.withdraw()
        self.colocar()
        self.pintar()
        self.raiz.after(500, self.sondear)
        self.raiz.after(100, self.animar)
        self.raiz.after(1500, self.precargar)
        self.raiz.after(2000, self.mantener_arriba)

    # ---- ventana ----
    def tam(self) -> tuple[int, int]:
        base = next(iter(self.frames.values()))[0]
        ancho, alto = base.width() * self.escala, base.height() * self.escala
        if self.hd:
            lado = -(-HD_LADO // SUBMUESTREO.get(self.escala, 5))  # subsample redondea hacia arriba
            ancho, alto = max(ancho, lado), max(alto, lado)
        return ancho, alto

    def colocar(self) -> None:
        w, h = self.tam()
        x = self.config.get('x', self.raiz.winfo_screenwidth() - w - 40)
        y = self.config.get('y', self.raiz.winfo_screenheight() - h - 80)
        x = min(max(0, x), self.raiz.winfo_screenwidth() - 40)
        y = min(max(0, y), self.raiz.winfo_screenheight() - 40)
        self.raiz.geometry(f'{w}x{h}+{x}+{y}')
        self.raiz.after(50, self.colocar_globo)

    def guardar(self) -> None:
        self.config.update(x=self.raiz.winfo_x(), y=self.raiz.winfo_y(), escala=self.escala, mensaje=self.mensaje)
        try:
            DATOS.mkdir(parents=True, exist_ok=True)
            CONFIG.write_text(json.dumps(self.config), encoding='utf-8')
        except OSError:
            pass

    def empezar_arrastre(self, e: tk.Event) -> None:
        self.dx, self.dy = e.x, e.y

    def arrastrar(self, e: tk.Event) -> None:
        self.raiz.geometry(f'+{self.raiz.winfo_x() + e.x - self.dx}+{self.raiz.winfo_y() + e.y - self.dy}')
        self.colocar_globo()

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

    # ---- globo de mensaje ----
    def alternar_mensaje(self) -> None:
        self.mensaje = not self.mensaje
        self.guardar()
        self.actualizar_globo(*self.texto, self.color)

    def actualizar_globo(self, frase: str, detalle: str, color: str = '') -> None:
        self.texto = (frase, detalle)
        self.l_frase.config(fg=oscurecer(color))
        if not self.mensaje or self.estado not in ACTIVOS or not (frase or detalle):
            self.globo.withdraw()
            return
        self.l_frase.config(text=frase)
        self.l_detalle.config(text=detalle)
        (self.l_detalle.pack_forget() if not detalle else self.l_detalle.pack(padx=8, pady=(0, 5), anchor='w'))
        self.globo.deiconify()
        self.colocar_globo()

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

    def pintar(self) -> None:
        if self.estado in self.hd:
            i = fotograma_de(self.estado, self.desde, len(self.hd[self.estado]))
            foto = self.foto_hd(self.estado, i)
            if foto is not None:
                self.etiqueta.config(image=foto)
                return
        lista = self.frames.get(self.estado) or self.frames.get('hula') or next(iter(self.frames.values()))
        i = fotograma_de(self.estado, self.desde, len(lista))
        clave = (self.estado, i, self.escala)
        foto = self.cache.get(clave)
        if foto is None:
            foto = lista[i].zoom(self.escala)  # ampliación entera: píxeles cuadrados, sin suavizar
            self.cache[clave] = foto
        self.etiqueta.config(image=foto)

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
            nuevo = (str(mejor.get('frase') or FRASE_BASE.get(estado, '')), str(mejor.get('detalle') or ''))
            self.color = str(mejor.get('color') or '')
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
