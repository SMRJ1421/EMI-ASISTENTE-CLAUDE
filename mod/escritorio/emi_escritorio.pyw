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
DATOS = Path(os.environ.get('EMI_DATOS') or Path.home() / '.claude' / 'mascota')  # EMI_DATOS solo para pruebas
SESIONES = DATOS / 'sesiones'
CONFIG = DATOS / 'escritorio.json'
INTERRUPTOR = DATOS / 'escritorio.txt'  # «off» la cierra; el mod lo escribe con /emi escritorio | sin-escritorio
PUERTO = int(os.environ.get('EMI_PUERTO') or 47231)  # una sola Emi por equipo: si el puerto está ocupado, ya hay otra y esta se va
CLAVE = '#fe00fe'  # color que Windows deja transparente
SIN_SENAL = 35  # s sin señal de una conversación: se da por cerrada (igual que en el mod)
GRACIA = 8  # s sin ninguna conversación viva antes de irse
LENTOS = {'nueva', 'leyendo', 'duerme'}  # 2 fps; pensando va a 5 fps; el resto a 4 (igual que dibujo.ts)
PRIORIDAD = {'necesita': 6, 'falla': 5, 'para': 5, 'baile': 4, 'terminado': 4, 'pensando': 3, 'responde': 3, 'leyendo': 3, 'escribiendo': 3}


def cargar_frames() -> dict[str, list[tk.PhotoImage]]:
    """Los PNG de frames/ (Tk 8.6 los lee con su transparencia); hay que crear la ventana raíz antes."""
    por_estado: dict[str, list[tk.PhotoImage]] = {}
    for archivo in sorted(FRAMES.glob('*_*.png')):
        estado = archivo.stem.rsplit('_', 1)[0]
        por_estado.setdefault(estado, []).append(tk.PhotoImage(file=str(archivo)))
    return por_estado


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
    fps = 5 if estado == 'pensando' else 2 if estado in LENTOS else 4
    return int(max(0.0, time.time() - desde) * fps) % max(1, cuantos)


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
        self.cache: dict[tuple[str, int, int], tk.PhotoImage] = {}

        self.raiz.overrideredirect(True)
        self.raiz.attributes('-topmost', True)
        self.raiz.config(bg=CLAVE)
        self.raiz.attributes('-transparentcolor', CLAVE)
        self.etiqueta = tk.Label(self.raiz, bg=CLAVE, bd=0, highlightthickness=0)
        self.etiqueta.pack()
        self.etiqueta.bind('<ButtonPress-1>', self.empezar_arrastre)
        self.etiqueta.bind('<B1-Motion>', self.arrastrar)
        self.etiqueta.bind('<ButtonRelease-1>', lambda _e: self.guardar())
        self.etiqueta.bind('<Button-3>', self.menu)
        self.colocar()
        self.pintar()
        self.raiz.after(500, self.sondear)
        self.raiz.after(100, self.animar)
        self.raiz.after(2000, self.mantener_arriba)

    # ---- ventana ----
    def tam(self) -> tuple[int, int]:
        base = next(iter(self.frames.values()))[0]
        return base.width() * self.escala, base.height() * self.escala

    def colocar(self) -> None:
        w, h = self.tam()
        x = self.config.get('x', self.raiz.winfo_screenwidth() - w - 40)
        y = self.config.get('y', self.raiz.winfo_screenheight() - h - 80)
        x = min(max(0, x), self.raiz.winfo_screenwidth() - 40)
        y = min(max(0, y), self.raiz.winfo_screenheight() - 40)
        self.raiz.geometry(f'{w}x{h}+{x}+{y}')

    def guardar(self) -> None:
        self.config.update(x=self.raiz.winfo_x(), y=self.raiz.winfo_y(), escala=self.escala)
        try:
            DATOS.mkdir(parents=True, exist_ok=True)
            CONFIG.write_text(json.dumps(self.config), encoding='utf-8')
        except OSError:
            pass

    def empezar_arrastre(self, e: tk.Event) -> None:
        self.dx, self.dy = e.x, e.y

    def arrastrar(self, e: tk.Event) -> None:
        self.raiz.geometry(f'+{self.raiz.winfo_x() + e.x - self.dx}+{self.raiz.winfo_y() + e.y - self.dy}')

    def menu(self, e: tk.Event) -> None:
        m = tk.Menu(self.raiz, tearoff=0)
        for nombre, escala in (('Pequeña', 1), ('Mediana', 2), ('Grande', 3)):
            m.add_command(label=nombre, command=lambda s=escala: self.cambiar_escala(s))
        m.add_separator()
        m.add_command(label='Cerrar Emi', command=self.cerrar)
        m.tk_popup(e.x_root, e.y_root)

    def cambiar_escala(self, escala: int) -> None:
        self.escala = escala
        self.colocar()
        self.pintar()
        self.guardar()

    def cerrar(self) -> None:
        self.guardar()
        self.raiz.destroy()

    def mantener_arriba(self) -> None:
        self.raiz.attributes('-topmost', True)
        self.raiz.lift()
        self.raiz.after(2000, self.mantener_arriba)

    # ---- dibujo ----
    def pintar(self) -> None:
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
