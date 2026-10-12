# Chat de actualización de animación (2026-10-08)

Resumen de la sesión en la que se incorporaron animaciones nuevas a Emi. Sirve para que otra sesión sepa **qué se hizo, por qué, dónde está cada cosa y qué falta**. Complementa a `CLAUDE.md` (reglas y cronología general) y a `INFORME_TECNICO_EMILIA.md`.

## 1. Resumen en tres líneas
- «De guardia: hula» (5 imágenes, 4 fps) también está actualizada en los mismos lugares (§12).
- «Pensando» ya usa las 5 imágenes nuevas (60x60, 5 fps) en **4 de los 5 lugares** donde se muestra Emi, con **fondo transparente**. Está en `mod\`.
- «Conversación nueva» (8 imágenes, 8 fps) está lista y probada **solo en el laboratorio**; **no** se ha llevado al mod principal.
- **Emi en el escritorio** (nuevo, ver §11): un programa aparte la muestra flotando sobre cualquier ventana mientras haya una sesión de Claude abierta.
- Nada está commiteado ni subido a GitHub. Hay copias de seguridad en `respaldos\`.

## 2. Qué se pidió, en orden
1. Revisar la carpeta y entender el estado del proyecto (4 fps actual, tamaños S/N/M/L/XL, el panel Dock admite hasta M).
2. Mejorar **solo el estado «Conversación nueva»** con 8 PNG de 1254x1254: comprobar transparencia y movimiento, pasarlos a 60x60 con vecino más cercano, mantener posición/escala/alineación, integrarlos **en el laboratorio**, probar a 8 fps, comparar con el actual y decir qué resolución rinde mejor en el Dock.
3. Hacer lo mismo con **«pensando»** (5 PNG) a **5 fps**.
4. Llevar «pensando» al **mod principal** (hubo que cambiar el modo de permisos, ver §7).
5. Hacer el fondo **transparente**.
6. Corregir los lugares donde seguía el sprite viejo (escritorio y banda).
7. Regla del usuario: **cuando diga «actualiza», hacerlo en todos los lugares** (ver §6).

## 3. Resultados de «Conversación nueva» (8 fotogramas, laboratorio)
- Los PNG tienen transparencia real: ~80 % del lienzo es transparente; alfa con bordes suaves y motas sueltas (se limpian con umbral 128).
- Los 8 fotogramas son distintos (cada uno difiere del anterior en ~300 000 píxeles): ojos, boca, pelo y punto rojo.
- El fotograma 6 estaba ~7 % más grande; los 2, 4 y 5 desplazados entre 12 y 18 px. Se alinearon contra el fotograma 1 (escala y desplazamiento) en una sola pasada de muestreo.
- La rejilla nativa del arte es de ~19,5 x 19,1 px (≈64 celdas por lado).
- **Mejor resolución para el Dock: `nat60`** (ventana de 60x60 celdas nativas, un punto por celda, vecino más cercano). Emi mide ~29x40 px, como el sprite M actual. `nn60` (reducir el PNG entero) rompe líneas de 1 celda y el punto rojo. 64x64 no cabe en el Dock (36 filas > 35).
- Error de color con paleta de 88: nat60 ~10,5 frente a nn60 ~12,2.
- En el laboratorio se ve con `/emiconv` (por defecto nat60 a 8 fps).

## 4. «Pensando» (5 fotogramas, 5 fps)
- Los PNG venían **sin transparencia**: fondo negro opaco (RGB). Se quita el negro (canal máximo ≤ 45) conectado con el borde; el negro de dentro (ojos, boca) se conserva.
- El arte **no tiene contorno negro**: sobre la tarjeta lila el pelo se ve más suave. Por eso en el mod se dibuja sobre el fondo del terminal/app.
- Rejilla ~20,2 x 19,5 px. Mismo método que arriba; nat60 vuelve a ser la mejor.
- Para la banda del terminal (14 filas) se generó `nat28`: ventana de 56x56 celdas reducida a 28x28 **promediando 2x2 celdas** (el vecino más cercano rompía el globo). Es más suave que nat60.

## 5. Dónde se muestra Emi y qué se hizo en cada lugar
| Lugar | «pensando» nuevo |
|---|---|
| Panel acoplado del terminal | Sí: 60x60 si caben 60 columnas y 34 filas con el texto debajo; si no, sprite viejo. |
| Banda del terminal | Sí: 60x60 si la banda es alta; si no, **28x28** (cabe en 14 filas). |
| Banda de la app de escritorio (SVG) | Sí: 60x60 transparente. |
| Panel de la app de escritorio (SVG) | Sí: 60x60 transparente. |
| Banda compacta (`/emi compacta`) | No: es una línea de texto sin imagen. |

Solo con tamaño `normal` o `grande`. `mini` y `compacta` siguen con sus sprites. El editor y el móvil comparten el SVG del escritorio.

**Detalles técnicos que importan**
- Fondo transparente: celdas Raster con el color `0x01000000` (terminal por defecto). Si arriba es transparente y abajo tiene color se usa `▄`; si arriba tiene color y abajo no, `▀` con fondo por defecto. En SVG, no se pinta el rectángulo de la tarjeta.
- Fotograma por **tiempo** (`ms * fps / 1000`), no contando redibujos. El latido normal es de 250 ms, así que mientras dure el estado «pensando» corre un reloj extra de 100 ms (`ajustarRapido` en `register.tsx`); se cancela al salir del estado. Los demás estados no cambian de coste.
- El panel acoplado se abre con ~62 columnas (antes ~42) cuando el terminal da sitio, para que quepan los 60 px. Eso lo ensancha en todos los estados.
- La captura que mandó el usuario con el panel viejo era la **app de escritorio** (SVG), no el terminal: mi primer cambio solo cubría el terminal. De ahí la regla del §6.

## 6. Regla del usuario (guardada también en la memoria de Claude)
Cuando diga «actualiza» un estado, hacerlo en **todos** los lugares donde Emi se muestra (los 5 de arriba), y si alguno no se puede, avisar antes y buscar una versión que quepa, no omitirlo en silencio.

## 7. Archivos tocados o creados
**En `mod\` (el mod principal)**
- `hooks\animaciones.ts` (nuevo, generado): hojas `A5` (60x60) y `A5S` (28x28) con los 5 fotogramas; tabla `ESPECIAL` (estado → hoja grande, hoja chica, fps).
- `hooks\dibujo.ts`: `TamX`, `hoja()`, `fotogramaEn`, `especialQueCabe`, `especialEnBanda`; `celdas` y `dibujoSvg` aceptan las hojas nuevas y dejan el fondo transparente.
- `hooks\register.tsx`: panel y banda del terminal, panel y banda de escritorio, apertura del panel más ancho, reloj rápido.
- `tests\mascota.test.ts`: pruebas nuevas (hoja, tiempo, cabe/no cabe, transparencia, escritorio, banda).

**En `laboratorio\`**
- `hooks\conversacion.ts` y `hooks\pensando.ts` (datos generados, varias resoluciones), `hooks\convdibujo.ts`, comando `/emiconv [nueva|pensando] nat60|nn60|nn48|nn40|nn30|actual [fps] | off` en `register.tsx`, `tests\conv.test.ts`, `types\index.d.ts` (`ticConv`).

**Scripts (`scripts\pipeline-sprites\`)**
- `estado_animado.py nueva|pensando`: PNG → datos del laboratorio, vistas previas e informe (Pillow + numpy; sin instalar nada).
- `animaciones_mod.py`: del laboratorio a `mod\hooks\animaciones.ts`.
- Si cambian las imágenes: correr `estado_animado.py pensando` y luego `animaciones_mod.py`.

**Datos y comparaciones:** `datos-laboratorio\conversacion-nueva\` y `datos-laboratorio\pensando\` (PNG, GIF a 8 y 5 fps, `informe.json`).

**Originales y copias:** `arte\Emi-Animacion-Conversacion_Nueva\`, `arte\Emi-Animacion-pensando\`; copias con SHA-256 en `respaldos\conversacion-nueva-originales\` y `respaldos\pensando-originales\`; mod anterior en `respaldos\mascota-2026-10-08-antes-de-nueva-y-pensando\`; laboratorio anterior en `respaldos\mascota-lab-2026-10-08-antes-de-conversacion\`.

## 8. Verificación
- `claude plugin test mod`: 44 de 44. `claude plugin test laboratorio`: 21 de 21. `claude plugin validate`: pasa. tsc de `mod` y `laboratorio`: sin errores.
- **Verificado por el usuario con capturas:** panel de escritorio con «pensando» nuevo y fondo transparente («bien ahora sí»).
- **Sin ver en pantalla real:** la banda del terminal (28x28), el panel del terminal, la banda de escritorio tras el último cambio y la fluidez a 5 fps.

## 9. Incidencia de permisos (para no repetirla)
Con el modo automático, las ediciones de `mod\hooks\dibujo.ts` y `register.tsx` devolvieron «sin veredicto» del clasificador, un fallo duro que no se reintenta. Se intentó «Aceptar ediciones» y no bastó para `register.tsx`; el usuario cambió a «Omitir permisos» y las ediciones pasaron. No se rodeó el bloqueo con otra vía. Conviene volver a un modo más estricto al terminar.

## 10. Pendiente
1. Que el usuario mire, tras recargar el mod, la banda del terminal y la fluidez de «pensando».
2. **«Conversación nueva»** al mod principal (8 fotogramas, 8 fps): añadirla a `FUENTES` en `animaciones_mod.py`, a `ESPECIAL` y repetir los 5 lugares. Para la banda del terminal haría falta su versión 28x28.
3. Decisión de fondo: ¿los otros 11 estados también transparentes? Llevan contorno negro que se vería mal sobre un terminal oscuro; hoy siguen sobre la tarjeta lila.
4. Decidir si el contorno negro falta en «pensando» (se podría añadir; no se hizo sin pedirlo).
5. Commit de Git (no se hizo; la regla del proyecto es no hacer `git push` sin que lo pida).
6. Las 20 animaciones de `arte\animacion.png` y el resto de mejoras de `CLAUDE.md §6` siguen igual.

## 11. Emi flotando en el escritorio (programa aparte)
**Nombre acordado: «Emi escritorio»** (la que flota fuera de Claude). «Emi» a secas es la que vive dentro de Claude, en la banda y el panel.

**Pedido:** que Emi aparezca siempre, aunque se minimice Claude o se vaya a otro programa, y que desaparezca cuando ya no haya ninguna sesión de Claude abierta (el usuario eligió «siempre visible» y «desaparecer al cerrar Claude»).

**Por qué es un programa aparte:** el mod vive dentro de Claude Code y solo dibuja en sus paneles; no puede dibujar fuera. Se hizo `escritorio\emi_escritorio.pyw` (Python 3.12 + tkinter + Pillow, ya instalados; nada de terceros, sin red).

**Cómo funciona**
- El mod escribe el estado de cada sesión (`estado`, `desde`, `vivo`, `cerrada`) en `~\.claude\mascota\sesiones\<id>.json`, en cada cambio de estado y cada 10 s.
- El programa lee esos archivos cada 0,5 s, elige la sesión más importante (necesita > falla/para > terminado/baile > trabajando > guardia) y anima ese estado: 5 fps «pensando», 2 fps los lentos, 4 fps el resto (igual que el mod).
- Ventana sin bordes, siempre encima, fondo transparente (color clave de Windows). Se arrastra; clic derecho: tamaño pequeño/mediano/grande o cerrar. Guarda posición y tamaño en `~\.claude\mascota\escritorio.json`.
- **Una sola Emi:** si el puerto local 47231 ya está ocupado, la segunda instancia se va sola. Se cierra sola ~8 s después de que no quede ninguna sesión viva (sin señal en 35 s = cerrada). `escritorio.txt` con «off» también la cierra.
- El mod la lanza al abrir cada sesión con PowerShell `Start-Process pythonw` (solo en Windows y si el ajuste `escritorio` está activo).
- Fotogramas: `escritorio\exportar_frames.py` los saca del mod (`sprites.ts` tamaño XL + «pensando» 60x60) a `escritoriorames\*.png` (53 PNG, lienzo de 72x96). **Repetirlo si cambia el arte del mod.**

**Comandos nuevos:** `/emi escritorio` y `/emi sin-escritorio` (se guarda por equipo; `/emi` sin argumentos muestra el estado).

**Archivos:** `escritorio\emi_escritorio.pyw`, `escritorio\exportar_frames.py`, `escritorio\prueba_humo.py`, `escritorio\frames\`; en el mod: `types\index.d.ts` (ajuste `escritorio`), `hooks\register.tsx` (`publicar` con estado, `lanzarEscritorio`, comandos), `tests\mascota.test.ts` (prueba nueva).
egister.tsx` (`publicar` con estado, `lanzarEscritorio`, comandos), `tests\mascota.test.ts` (prueba nueva).

**Verificación:** `claude plugin test mod` 45/45, tsc limpio, validate OK. `python escritorio\prueba_humo.py` (sesión falsa en una carpeta temporal): una sola instancia, no se cierra con sesión viva, se cierra ~9 s después de la última, guarda su posición. Se lanzó una vez con el mismo comando que usa el mod y quedó corriendo.
**No verificado:** cómo se ve en la pantalla del usuario (posición, tamaño, transparencia, «siempre encima» sobre otras ventanas a pantalla completa), y el lanzamiento automático desde una sesión nueva.

**Limitaciones conocidas**
- La ruta del programa está fija en el mod: `~\Proyectos\mods-claude\emilia-mascota\escritorio\emi_escritorio.pyw`. Si se mueve el proyecto, hay que cambiarla en `register.tsx` (`rutaEscritorio`).
- Usa `pythonw` del PATH (hoy Python 3.12, que tiene Pillow). Si ese Python cambia, hay que reinstalar Pillow.
- Sobre aplicaciones a pantalla completa exclusiva (juegos, vídeo) Windows puede taparla.
- «Pensando» en el escritorio usa la animación nueva; «Conversación nueva» sigue con el sprite viejo (aún no está en el mod).
- Pendiente de decidir: aviso/globo de texto junto a Emi, o que se oculte sola si el usuario no quiere verla con Claude al frente.

## 12. «De guardia: hula» (5 fotogramas, 4 fps)
**Pedido:** actualizar el estado «hula» con las 5 imágenes de `arte\Emi-Animacion-pensando-de-guardia-hula` (el nombre de la carpeta dice «pensando» pero son de hula). No se indicaron fps: se dejaron en **4 fps**, la velocidad que ya tenía «hula» (cambiarlo es un solo valor: `ESTADOS` en `animaciones_mod.py`, luego regenerar).

**Lo que traían los PNG:** 1254x1254 con transparencia real (~75 %) y **contorno negro**; 5 fotogramas distintos (ojos abiertos, guiño, ojos cerrados, brazos). Alineación contra el fotograma 1: ajustes de 0 a 9 px y escala 0,985 a 1.

**Decisión de diseño:** como el arte lleva contorno negro, en el terminal y en los SVG posa sobre la **tarjeta lila** (como los otros estados con contorno); «pensando» (sin contorno) sigue sobre el fondo del terminal. Se controla con el campo `tarjeta` de cada estado en `ESPECIAL` (`animaciones.ts`). En Emi escritorio el fondo es transparente en los dos.

**Dónde se actualizó:** los mismos lugares que «pensando»: panel del terminal (60x60 si caben 60 columnas y 34 filas), banda del terminal (60x60 si es alta, si no 28x28), banda y panel de escritorio (SVG 60x60) y **Emi escritorio** (frames regenerados). La banda compacta sigue siendo solo texto.

**Cambios técnicos**
- El mod ya no está atado a «pensando»: `animaciones.ts` define cualquier estado con animación propia (`ESPECIAL`: hoja grande, hoja chica, fps, tarjeta). Hojas actuales: `A5/A5S` (pensando), `H5/H5S` (hula).
- Para sumar otro estado: añadirlo a `ESTADOS` en `scripts\pipeline-sprites\estado_animado.py` (carpeta de PNG) y en `animaciones_mod.py`; correr `estado_animado.py <estado>`, `animaciones_mod.py` y `escritorio\exportar_frames.py`; reiniciar Emi escritorio.
- El reloj rápido (`ajustarRapido`) solo corre si el estado va a más de 4 fps (pensando); «hula» usa el latido normal de 250 ms.
- `exportar_frames.py` recorta y amplía (hasta x2) todos los estados de `ESPECIAL`.
- Laboratorio: `/emiconv hula ...` y `laboratorio\hooks\hula.ts`.
- Copias de seguridad: `respaldos\hula-originales\` (PNG con SHA-256), `respaldos\mascota-2026-10-08-antes-de-hula\`, `respaldos\escritorio-2026-10-08-antes-de-hula\`.

**Verificación:** `claude plugin test mod` 47/47, laboratorio 21/21, tsc de ambos y `validate` limpios. Conversión revisada a ojo en `datos-laboratorio\hula\comparacion_actual_vs_nat60.png`. **No visto por el usuario todavía** en pantalla real; la versión de 28x28 tiene más error de color (~23) por tener muchos colores (flores, falda).

**Efecto colateral:** «hula» es el estado en reposo, el más visto, así que el panel del terminal ahora se abre siempre más ancho (~62 columnas).

## 13. Sonido al terminar: cada vez
**Antes:** el pitido de «listo» solo sonaba si el encargo duraba 30 s o más (`AVISO_DESDE`), y llevaba el globo de Windows.
**Ahora (pedido del usuario):** suena **cada vez que Claude termina** (`turn.complete` con `reason: 'answer'`), aunque sea corto. El **globo de Windows** sigue solo en encargos de 30 s o más. El pitido es el mismo: tres notas ascendentes (784, 988 y 1175 Hz, ~0,45 s) con `[console]::Beep` desde PowerShell. «Te necesita» sigue con sus dos pitidos de 988 Hz (máx. uno cada 60 s).
- Cambio: `avisar($, tipo, globo)` en `mod\hooks\register.tsx`; `ultimoAviso` solo se marca en los encargos largos (para no tapar un «te necesita» tras un turno corto).
- `/emi silencio` y `/emi sonido` siguen apagando y encendiendo el sonido; `/emi sin-avisos` / `/emi avisos`, el globo. Emi escritorio no emite sonido.
- Prueba nueva en `mascota.test.ts` («sonido al terminar»): un turno corto suena una vez y sin globo; con `/emi silencio` no suena. Total: `claude plugin test mod` 48/48, tsc limpio.
- **No oído todavía** en el equipo del usuario.

## 14. «Escribiendo / comandos» (5 fotogramas, 5 fps) — arte nativo 60x60
**Pedido:** actualizar «escribiendo» con `arte\animacion-emi-escribiendo-comandos` (el usuario dijo «si encuentras»: estaba ahí).
**Lo que traía la carpeta (formato nuevo):** 5 PNG **ya de 60x60 reales** con transparencia y contorno negro, más 5 copias `-alta-resolucion` de 500x500 (no se usan: 500/60 no es entero) y `vista-previa-5fps.gif` (5 fotogramas de 200 ms → **5 fps**, la velocidad usada).
**Cómo se convirtió:** no hace falta reducir ni alinear, así que se hizo un script aparte, `scripts\pipeline-sprites\animacion_nativa.py escribiendo`: toma los 60x60 tal cual (alfa ≥128), cuantiza a 88 colores (error medio por píxel ~10; 6,5 % de píxeles con error >40) y genera `laboratorio\hooks\escribiendo.ts` con `nat60` (60x60) y `nat28` (media de cajas para la banda del terminal, error de paleta mayor). Después `animaciones_mod.py` (hojas `E5`/`E5S`, fps 5, sobre la tarjeta lila por el contorno) y `escritorio\exportar_frames.py`.
**Dónde:** los mismos 5 lugares que «pensando» y «hula» (panel y banda del terminal, banda y panel de escritorio, Emi escritorio). Como va a 5 fps, corre el reloj rápido mientras dura el estado.
**Cambio en Emi escritorio:** `exportar_frames.py` ahora amplía solo con escala **entera** (x2 si cabe en 72x96, si no x1). «Escribiendo» queda a x1 (ocupa ~50x48 px de arte); «pensando» y «hula», a x2.
**Verificación:** `claude plugin test mod` 49/49, laboratorio 21/21, tsc y validate limpios. Laboratorio: `/emiconv escribiendo nat60|nat28`. **No visto aún en pantalla real.**
**Copias:** `respaldos\escribiendo-originales\` (PNG y GIF con SHA-256), `respaldos\mascota-2026-10-09-antes-de-escribiendo\`, `respaldos\escritorio-2026-10-09-antes-de-escribiendo\`.
**Pendiente a la vista:** hay otra carpeta nueva, `arte\te-responde\` (estado «responde»), sin procesar.

## 15. Instalación en una línea (marketplace)
**Pedido:** que otra persona instale el mod con solo llamar a Claude con la URL del repositorio, y que quede todo listo.
**Cómo se hizo**
- `.claude-plugin\marketplace.json` en la raíz del repositorio: lo convierte en un marketplace con un plugin, `mascota`, cuyo `source` es `./mod`. Con eso la instalación es una línea en una sesión de terminal: `/plugin install mascota --marketplace SMRJ1421/emilia-mascota` (responder `y` y elegir el ámbito). Actualizar: `claude plugin update mascota`. La app de escritorio carga los mods instalados desde la terminal, pero el comando `/plugin` solo existe en la terminal.
- **Emi escritorio viaja dentro del mod**: `escritorio\` se movió a `mod\escritorio\` (con `git mv`) porque el marketplace solo copia `mod\`. El mod calcula la ruta con `$.plugin.root` en vez de una ruta fija, así que funciona igual instalado, con `--plugin-dir` o con `CLAUDE_CODE_PLUGIN_DIRS`. `exportar_frames.py` y `prueba_humo.py` se adaptaron; ahora se corre `python mod\escritorio\exportar_frames.py`.
- **Sin Pillow:** `emi_escritorio.pyw` ya no usa Pillow; lee los PNG con `tk.PhotoImage` (Tk 8.6) y amplía con `zoom` (escala entera). Solo hace falta **Python 3 con tkinter** (`pythonw` en el PATH). Si no hay Python, el mod avisa una vez con un aviso y sigue sin Emi escritorio (`/emi sin-escritorio` quita el aviso).
- README reescrito con la línea de instalación, los requisitos y los pasos.
**Verificación:** `claude plugin validate .` pasa. Instalación probada de punta a punta en una carpeta de configuración temporal (`CLAUDE_CONFIG_DIR`, sin tocar la del usuario): `marketplace add` + `install mascota@emilia-mascota` copiaron `escritorio\emi_escritorio.pyw` y `escritorio\frames\`. `claude plugin test mod` 49/49, tsc limpio, `prueba_humo.py` pasa con tkinter solo.
**No probado:** instalar desde GitHub de verdad (hace falta que el repositorio esté subido y sea público o accesible) ni en un equipo ajeno; cómo se ve Emi escritorio con `PhotoImage` en la pantalla del usuario (cambió el dibujo respecto a Pillow).
**Pendiente de decisión del usuario:** la visibilidad del repositorio (hoy es **público**; contiene arte propio y su correo en los commits) y qué publicar antes de compartirlo. Ver el resumen de datos personales en la conversación (correo en los commits, usuario de Windows en rutas de `docs\` y `scripts\`).

### 15b. Subido a GitHub y probado desde allí (2026-10-10)
- `git push origin main`: `68d7580..d017de2` (5 commits). El repositorio sigue **público** (verificado sin sesión con la API de GitHub).
- Instalación real desde GitHub en una configuración temporal (`CLAUDE_CONFIG_DIR`, sin tocar la del usuario): `claude plugin marketplace add SMRJ1421/emilia-mascota` (clonó y validó) + `claude plugin install mascota@emilia-mascota` → instalado, habilitado, con `escritorio\emi_escritorio.pyw` y 51 fotogramas. En la copia instalada: `claude plugin validate` pasa y `claude plugin test` da 49/49.
- Todavía **no probado en el equipo de otra persona** ni la apertura automática de Emi escritorio tras una instalación limpia (hace falta una sesión nueva con Python 3 y tkinter).
- Datos personales visibles en el repositorio público: correo `smrj.1421@gmail.com` en los commits y el usuario de Windows en rutas de algunos documentos; el arte original de `arte\` también es público.

## 16. «Pensando» con ilustración nueva (8 fotogramas, 5 fps) — carpeta `arte\EMI-PENSANDO`
**Pedido:** usar `arte\EMI-PENSANDO` para el estado «pensando» (reemplaza a la versión de 5 fotogramas pixelados de §4).
**Lo que traía (y es distinto a todo lo anterior):** 8 PNG de 1254x1254 con transparencia (~46 %), pero **no son pixel art**: son ilustraciones suaves de alta resolución (≈165 000 colores por fotograma) con **otro diseño** (cuerpo completo, pelo largo y ondulado, vestido morado, dedo en la barbilla). Sin contorno negro.
**Decisión técnica:** no hay cuadrícula de píxeles que respetar, así que el vecino más cercano sale ruidoso. Se usó una caja de recorte común para los 8 fotogramas (no se alinean uno a uno: se conserva el movimiento original), reducción **Lanczos con color premultiplicado por el alfa** (el borde no sangra color) y cuantización a 88 colores con **10 plazas reservadas** a los colores más alejados de la paleta (sin ellas el adorno rojo del pelo salía morado). Error medio de color ~12. La figura mide ~55x58 px en el lienzo de 60x60 (26 px de alto en el de 28x28 para la banda del terminal).
**Fps:** no se indicó; se mantuvo **5 fps** (lo pedido para «pensando» antes). Con 8 fotogramas el ciclo dura 1,6 s.
**Cambios:** `animacion_nativa.py` ganó el modo `ilustrada` (campo `modo` por estado; «escribiendo» sigue en `nativa`); `laboratorio\hooks\pensando.ts` ahora solo tiene las variantes `nat60` y `nat28` (se perdieron nn30…nn60 del arte viejo; el arte viejo sigue en `arte\Emi-Animacion-pensando\` y en `respaldos\`); `animaciones_mod.py` toma los 8 fotogramas; pruebas del mod y del laboratorio pasadas de 5 a 8 fotogramas; Emi escritorio regenerada (`pensando` a x1: la figura ocupa 55x58 de arte).
**Dónde:** los mismos lugares que antes (panel y banda del terminal, banda y panel de escritorio, Emi escritorio). Fondo transparente en todos.
**Verificación:** mod 49/49, laboratorio 21/21, tsc y validate limpios. **No visto aún en pantalla real.** Riesgo de estilo: es la única animación que no es pixel art, junto a las demás se verá distinta (más suave y de otro diseño).
**Copias:** `respaldos\EMI-PENSANDO-originales\` (SHA-256), `respaldos\mascota-2026-10-09-antes-de-pensando-ilustrado\`, `respaldos\pensando-lab-antes-ilustrado.ts`.
**GitHub:** este cambio está solo en commit local; no se ha subido (el usuario no lo pidió).

## 17. «Pensando» con `arte\EMI CLAUDE PENSANDO` (8 fotogramas, 5 fps) — reemplaza §16
**Pedido:** usar `arte\EMI CLAUDE PENSANDO` (1.png a 8.png) para «pensando».
**Lo que traía:** 8 PNG de 1254x1254 con transparencia, **pixel art de verdad** (cuadrícula ~18 x 19,6 px, unas 64 celdas) pero con un **personaje distinto**: pelo naranja con coletas, ojos rojos, vestido rojo y un globo de pensamiento «...». Parece «Emi en los colores de Claude» (naranja); no es la Emi lila. El personaje ocupa casi todo el lienzo (~64 celdas de ancho): un recorte de 60 celdas lo cortaría.
**Cómo se convirtió:** modo `ilustrada` de `animacion_nativa.py` (caja común, reducción Lanczos con color premultiplicado, 88 colores con 10 plazas de refuerzo). Se probó contra el vecino más cercano y éste salía ruidoso (se perdían la cara y el globo); Lanczos conserva cara, globo y pelo. Error de color ~15; nat28 para la banda del terminal ~14.
**Fps:** no se indicó; **5 fps** (como antes). Con 8 fotogramas el ciclo dura 1,6 s. **Fondo transparente** (el usuario lo pidió así para «pensando»); el arte lleva contorno rojo oscuro, no negro: sobre un terminal muy oscuro el contorno se nota menos.
**Dónde:** panel y banda del terminal (28x28 en las 14 filas), banda y panel de escritorio, Emi escritorio (regenerada; «pensando» a x1: ocupa 59x58 de arte). Pruebas: mod 49/49, laboratorio 21/21, tsc y validate limpios.
**Riesgo de estilo:** mezcla en la misma Emi un «pensando» naranja con los demás estados lilas. Si no es intencional, conviene que el resto de estados también tenga la versión Claude.
**Copias:** `respaldos\EMI-CLAUDE-PENSANDO-originales\` (SHA-256), `respaldos\mascota-2026-10-09-antes-de-emi-claude-pensando\`, `respaldos\pensando-lab-antes-emi-claude.ts`. Sin cambios en Git (el usuario pidió no tocarlo por ahora).

## 18. Emi escritorio con las imágenes originales de 1254x1254
**Pedido:** que el mod use las imágenes de 1254 px en vez de las de 60 px. **Alcance acordado (con el usuario):** solo **Emi escritorio**, con los originales sin reducir guardados en el mod. El terminal (celdas, tope 60x60 en el panel, 28x28 en la banda) no puede mostrar 1254 px; la app de escritorio de Claude (SVG, máx. 131 072 caracteres) no se tocó.
**Qué estados:** los que tienen original grande: **pensando** (`EMI CLAUDE PENSANDO`, 8) y **hula** (`Emi-Animacion-pensando-de-guardia-hula`, 5). Los demás siguen con su dibujo pequeño de `frames\` (más adelante, al llegar sus originales, se añaden en `HD` de `exportar_frames.py`).
**Cómo:** `exportar_frames.py` copia los PNG originales **tal cual** a `mod\escritorio\hd\<estado>_<n>.png` (12 MB en total). `emi_escritorio.pyw` los lee con Tk y los reduce por saltos (`subsample`: tamaño Pequeña 1/7 = 179 px, Mediana 1/5 = 251 px, Grande 1/3 = 418 px); como el arte tiene celdas de ~18 px, los bloques quedan íntegros y no hace falta Pillow. La ventana se adapta al tamaño mayor y Emi apoya los pies abajo y centrada. Los estados sin original usan el zoom entero de antes.
**Rendimiento:** cada PNG grande tarda ~0,5 s en leerse; se precargan uno cada 200 ms al arrancar (un tramo con tirones al inicio) y la versión reducida se guarda en `~\.claude\mascota\cache_hd\` (clave: estado, fotograma, tamaño y peso del archivo), así que el siguiente arranque casi no tarda. Un PNG ilegible hace que ese estado vuelva a su dibujo pequeño.
**Efecto en el tamaño:** «hula» y «pensando» ahora miden ~250 px de ventana en Mediana (antes 144x192 px); «pensando» deja de verse chica.
**Verificación:** `prueba_humo.py` ampliado (carga el PNG de 1254, comprueba 251 px en Mediana y 418 en Grande, caché); `claude plugin test mod` 49/49; validate limpio. **No visto aún en pantalla real.**
**Peso:** el mod pasa a pesar ~12 MB más (afecta a la instalación desde GitHub). Sin cambios en Git (el usuario pidió no tocarlo por ahora).

### 18b. Partículas moradas alrededor de Emi escritorio (corregido)
**Síntoma:** puntos moradas alrededor de la Emi naranja de «pensando» en Emi escritorio.
**Causa:** los PNG originales traen alfa parcial en casi todos los píxeles (251-254 en el cuerpo, y ~30 000 píxeles por fotograma con alfa <128 alrededor: motas y bordes suaves). Tk los mezcla con el color transparente de la ventana (`#fe00fe`, magenta) y esos píxeles ya no son exactamente la clave, así que se ven como puntos morados.
**Arreglo:** `exportar_frames.py` ahora guarda las copias de `hd\` con **alfa de todo o nada** (>=128 opaco), mismos colores y tamaño (1254x1254); los fotogramas pasaron de 12 MB a ~9,7 MB. Se borró la caché `~\.claude\mascota\cache_hd` (se rehace sola) y se reinició Emi escritorio.
**Nota:** el arte original de `arte\` no se tocó; la limpieza es solo en la copia del mod. Si llega un estado nuevo con originales grandes, `exportar_frames.py` aplica la misma limpieza.

## 19. «Terminado» con `arte\EMI_CLAUDE_TERMINADO` (8 fotogramas, 5 fps)
**Pedido:** usar `arte\EMI_CLAUDE_TERMINADO` para el estado «terminado» (el que sale cuando Claude acaba una respuesta; «baile» es el de los encargos largos y no se tocó).
**Lo que traía:** 8 PNG de 1254x1254 con transparencia (~52 %), pixel art del **mismo personaje naranja de «pensando»** (Emi en colores de Claude) con confeti de colores, cara feliz de ojos cerrados y brazos arriba. Todos distintos.
**Cómo:** igual que «pensando» (§17): modo `ilustrada` de `animacion_nativa.py` (caja común, Lanczos, 88 colores con 10 plazas de refuerzo: los verdes, azules y amarillos del confeti se conservan). Error de color ~17,5 (el más alto, por la variedad de colores del confeti). Hojas `T5` (60x60) y `T5S` (28x28 para la banda del terminal), 5 fps, **fondo transparente** (como «pensando»); se pueden cambiar en `animaciones_mod.py`.
**Dónde:** panel y banda del terminal, banda y panel de escritorio, y **Emi escritorio con los originales de 1254x1254** (copiados y con alfa limpio en `mod\escritorio\hd\terminado_N.png`; 5 fps). Laboratorio: `/emiconv terminado nat60|nat28`.
**Peso:** `hd\` pasa de 9,7 MB a ~19 MB; el mod pesa más al instalarlo desde GitHub.
**Verificación:** mod 50/50 (prueba nueva), laboratorio 21/21, tsc y validate limpios, `prueba_humo.py` pasa. **No visto aún en pantalla real.**
**Riesgo de estilo:** «pensando» y «terminado» son naranjas; «hula», «escribiendo» y el resto, lilas.
**Copias:** `respaldos\EMI_CLAUDE_TERMINADO-originales\` (SHA-256), `respaldos\mascota-2026-10-10-antes-de-terminado\`. Sin cambios en Git (el usuario pidió no tocarlo por ahora).

## 20. Globo de mensaje junto a Emi escritorio
**Pedido:** un cuadro de mensaje al lado de Emi escritorio con lo que se está haciendo.
**Qué muestra:** la frase del estado (p. ej. «cavilando…») en negrita y debajo el detalle de la herramienta que Claude usa (p. ej. `Edit register.tsx`, `Bash «git status»`; el mod ya recorta el texto). Solo en estados activos (pensando, responde, leyendo, escribiendo, te necesita, falla, para, terminado, baile); en reposo (hula, duerme) no aparece.
**Cómo:** el mod publica `frase` y `detalle` en el archivo de sesión (`publicar` en `register.tsx`, en cada cambio de estado). `emi_escritorio.pyw` abre un `Toplevel` aparte, opaco y siempre encima, que se coloca a la izquierda de Emi (a la derecha si no hay sitio) a un tercio de su altura y la sigue al arrastrarla. Es opaco para que el texto suavizado no se mezcle con el color transparente de la ventana. Con un mod anterior (sin `frase`) usa una frase corta por estado.
**Control:** clic derecho en Emi escritorio → «Mensaje junto a Emi» (se guarda en `escritorio.json`).
**Privacidad:** el detalle puede mostrar nombres de archivos y comandos en pantalla; si compartes pantalla, desactiva el mensaje.
**Verificación:** `prueba_humo.py` (globo aparece con el detalle, se esconde en reposo y con la opción apagada); mod 50/50, tsc y validate limpios. **No visto aún en pantalla real**; el mod cargado en sesiones ya abiertas publica el texto completo solo tras recargarlo. Sin cambios en Git.

## 21. «Escribiendo / comandos» con `arte\EMI-CLAUDE-ESCRIBIENDO-COMANDOS` (8 fotogramas, 5 fps) — reemplaza §14
**Pedido:** actualizar «escribiendo comandos» con la carpeta nueva. **Lo que traía:** 8 PNG de 1254x1254, pixel art con transparencia, la **Emi naranja** (Claude) sentada escribiendo en una terminal verde con `>_`; parpadeo, guiño, chispas. Reemplaza la versión lila de 5 fotogramas (§14, 60x60 nativos), que sigue en `arte\animacion-emi-escribiendo-comandos\` y en `respaldos\`.
**Cómo:** modo `ilustrada` (Lanczos, caja común, 88 colores con refuerzo); error de color ~16. Hojas `E5`/`E5S`, 5 fps, **sin tarjeta** (transparente, igual que pensando y terminado; antes estaba sobre la tarjeta lila). Emi escritorio con los originales de 1254x1254 (alfa limpio) en `hd\escribiendo_N.png`.
**Arreglo de paso en `animacion_nativa.py`:** `reducir()` solo respetaba el alto y las escenas anchas (esta mide ~1100x930) se salían del lienzo de 60; ahora cabe en alto **y** ancho. Se regeneraron «pensando» y «terminado» con esa corrección (el «pensando» era un poco más ancho que el lienzo y se recortaba).
**Peso:** `hd\` pasa a ~26 MB (pensando, hula, terminado, escribiendo).
**Verificación:** mod 50/50 (prueba de escribiendo actualizada a 8 fotogramas y sin tarjeta), laboratorio 21/21, tsc, validate y `prueba_humo.py` limpios. **No visto aún en pantalla real.** Sin cambios en Git.
**Copias:** `respaldos\EMI-CLAUDE-ESCRIBIENDO-COMANDOS-originales\` (SHA-256), `respaldos\mascota-2026-10-10-antes-de-escribiendo-claude\`, `respaldos\escribiendo-lab-antes-claude.ts`.
**Estado de estilo:** naranja (Claude): pensando, escribiendo, terminado. Lila: hula, el resto.

### 20b. El globo usa la frase y el color del estado
La **frase de estado** (p. ej. «picando código…», de `FRASES` en `estados.ts`) es la primera línea del globo de Emi escritorio, igual que en Claude, y el **detalle** (herramienta, archivo o comando) la segunda. Ahora el mod publica también `color` (el de `COLORES[estado]`) y el globo pinta la frase con ese color un 30 % más oscuro para leerse sobre el fondo crema (el amarillo de «escribiendo» pasa a `#a98c35`). Con un mod anterior sin `frase`/`color`, el globo usa una frase corta genérica y el lila. Prueba en `prueba_humo.py`; mod 50/50.

## 22. Estado de guardia («hula») con `arte\EMI-CLAUDE-DE-GUARDIA` (8 fotogramas, 4 fps) — reemplaza §12
**Pedido:** actualizar el estado de guardia con la carpeta nueva. En el mod ese estado se llama `hula` («De guardia: hula» en la hoja original); `duerme` es el otro estado de guardia (a los 5 min sin actividad) y no se tocó.
**Lo que traía:** 8 PNG de 1254x1254, pixel art con transparencia: la **Emi naranja** de pie, con las manos en el pecho, esperando y con un globo «algo más para hacer» (el texto del globo no se lee a 60x60; sí en los originales de Emi escritorio). Reemplaza la «hula» lila bailando con corona de flores (§12), que sigue en `arte\Emi-Animacion-pensando-de-guardia-hula\` y en `respaldos\`.
**Cómo:** modo `ilustrada` (Lanczos, caja común, 88 colores con refuerzo; error ~15). Hojas `H5`/`H5S`, **4 fps** (la velocidad que ya tenía el estado; con 8 fotogramas el ciclo dura 2 s), **sin tarjeta** (transparente, como el resto de la serie naranja). Emi escritorio con los originales (alfa limpio) en `hd\hula_N.png`.
**Peso:** `hd\` ~32 MB en total (pensando, hula, terminado, escribiendo).
**Verificación:** mod 50/50 (pruebas de hula actualizadas: 8 fotogramas, sin tarjeta, ciclo de 2 s), laboratorio 21/21, tsc, validate y `prueba_humo.py` limpios. **No visto aún en pantalla real.** Sin cambios en Git.
**Serie naranja (Claude):** pensando, escribiendo, terminado, hula. **Lila (original):** nueva, responde, leyendo, necesita, falla, para, baile, duerme.
**Copias:** `respaldos\EMI-CLAUDE-DE-GUARDIA-originales\` (SHA-256), `respaldos\mascota-2026-10-10-antes-de-guardia-claude\`, `respaldos\hula-lab-antes-guardia-claude.ts`.

## 23. Emi escritorio ya no «salta» al cambiar de estado
**Síntoma (usuario):** dejaba a Emi escritorio en un punto (unos 6 px a la derecha, 20 px arriba de otro) y al cambiar de estado se movía.
**Causa:** el programa no mueve la ventana; lo que cambiaba era dónde apoyaba los pies cada dibujo dentro del mismo lienzo de 1254x1254: los pies quedaban entre el 90 % (escribiendo) y el 96 % (pensando, terminado) de la altura, y el centro entre el 51 % y el 52 %. En la ventana Mediana (251 px) eso son hasta ~17 px de alto (~21 px con Windows al 125 %) y unos pocos de ancho.
**Arreglo:** `exportar_frames.py` re-ancla cada estado al copiar los originales a `hd\`: la caja que envuelve todos los fotogramas del estado queda **centrada en x (627 px) y con los pies a 8 px del borde de abajo**. Se mueven todos los fotogramas del estado por igual: el movimiento propio de la animación se conserva. Medido tras el arreglo: centro x = 627-628 y pies y = 1246 en los 4 estados. Los estados sin original grande (dibujo pequeño) ya apoyaban los pies abajo y centrados. Se borró la caché `cache_hd` y se reinició Emi escritorio.
**Lo que no cambia:** el **tamaño** de cada figura sigue siendo el del arte (pensando y terminado ocupan casi todo el lienzo; hula y escribiendo, menos), así que unos estados se ven más grandes que otros; es una decisión aparte (escala por estado).
**Verificación:** `prueba_humo.py` limpio; no visto aún en pantalla real. Sin cambios en Git.

## 24. «Te responde» (`responde`) con `arte\EMI-CALUDE-TE-RESPONDE` (8 fotogramas, 5 fps)
**Pedido:** actualizar el estado «te responde» con la carpeta nueva (el nombre de la carpeta trae la errata «CALUDE»).
**Lo que traía:** 8 PNG de 1254x1254, pixel art con transparencia: la **Emi naranja** hablando y saludando, con marcas de exclamación rojas, destellos, un guiño y gestos con las manos. No confundir con la carpeta antigua `arte\te-responde\` (sin procesar y sin usar).
**Cómo:** igual que el resto de la serie naranja: modo `ilustrada` (error de color ~15), hojas `R5`/`R5S`, **5 fps**, sin tarjeta (transparente). Emi escritorio con los originales re-anclados (`hd\responde_N.png`: centro y pies a la misma línea que los demás estados). Laboratorio: `/emiconv responde nat60|nat28`.
**Arreglo menor:** en Emi escritorio «escribiendo» iba a 4 fps (el mod a 5); ahora los estados `pensando`, `terminado`, `responde` y `escribiendo` van a 5 fps en los dos.
**Verificación:** mod 51/51 (prueba nueva de responde; las pruebas de «no tiene hoja especial» pasaron de `responde` a `leyendo`), laboratorio 21/21, tsc, validate y `prueba_humo.py` limpios. **No visto aún en pantalla real.** Sin cambios en Git.
**Serie naranja:** pensando, responde, escribiendo, terminado, hula. **Lila (original):** nueva, leyendo, necesita, falla, para, baile, duerme.
**Copias:** `respaldos\EMI-CALUDE-TE-RESPONDE-originales\` (SHA-256), `respaldos\mascota-2026-10-10-antes-de-responde-claude\`.

## 25. Se quita el «baile de fiesta» (`baile`)
**Pedido:** que Emi ya no haga el estado de bailar con música.
**Cambio (solo en `mod\hooks\register.tsx`):** al terminar una respuesta, Emi **siempre** pasa a «terminado» (antes pasaba a «baile» si el encargo duraba 2 minutos o más, o usaba 25 o más herramientas). Se quitó la constante `LARGO`. `/emi probar` enseña ahora 11 estados (sin «baile»).
**Lo que no cambia:** el sonido de «listo» (cada vez) y el globo de Windows (solo en encargos de 30 s o más). El estado `baile` y su arte lila siguen existiendo en los datos (`estados.ts`, `sprites.ts`) por si se quiere recuperar: bastaría volver a la condición `largo ? 'baile' : 'terminado'`.
**Verificación:** mod 51/51, tsc y validate limpios. Sin prueba específica del turno largo (necesita simular 2 minutos). **No visto aún en pantalla real.** Sin cambios en Git.

## 26. Los 5 estados de 8 fotogramas a 8 fps
**Pedido:** «¿puedes hacerlo de 8 fps?». **Alcance elegido:** los cinco estados con 8 fotogramas (pensando, responde, escribiendo, terminado, hula) pasan a **8 fps** (cada dibujo 125 ms; el ciclo dura 1 s). Los de 4 fotogramas (nueva, leyendo, duerme: 2 fps; necesita, falla, para: 4 fps) **no se tocaron**: a 8 fps un ciclo de 4 dibujos duraría 0,5 s.
**Dónde:** `ESTADOS` de `animaciones_mod.py` (campo fps → `ESPECIAL` en `animaciones.ts`) para el mod, y `OCHO_FPS` en `emi_escritorio.pyw` para Emi escritorio. El reloj rápido del mod (`ajustarRapido`) corre ahora también durante «hula» (antes bastaba el latido de 250 ms): dos tics por fotograma (~63 ms), así que en reposo la Emi de Claude se redibuja unas 16 veces por segundo en lugar de 4.
**Pruebas actualizadas:** fps y tiempos (125 ms por fotograma, ciclo de 1 s). Mod 51/51, tsc y validate limpios; `prueba_humo.py` limpio. **No visto aún en pantalla real.** Sin cambios en Git.
**Si se nota pesado:** bajar «hula» a 5 fps en `ESTADOS` (la pasa de nuevo al latido normal si se pone ≤ 4).

## 27. «Leyendo» con `arte\EMI-CLAUDE-LEYENDO` (8 fotogramas, 8 fps)
**Pedido:** actualizar el estado «leyendo» con la carpeta nueva. **Lo que traía:** 8 PNG de 1254x1254, pixel art con transparencia: la **Emi naranja** leyendo tras una laptop gris, con destellos, un globo/etiqueta pequeña y un parpadeo. Reemplaza el «leyendo» lila original de 4 fotogramas.
**Cómo:** como el resto de la serie naranja: modo `ilustrada` (error de color ~15; ~13 en la versión de la banda), hojas `L5`/`L5S`, **8 fps** (el valor vigente de la serie; antes «leyendo» iba a 2 fps), sin tarjeta, y en Emi escritorio los originales re-anclados (`hd\leyendo_N.png`) con `leyendo` añadido a `OCHO_FPS`. Laboratorio: `/emiconv leyendo nat60|nat28`.
**Cuándo sale:** cuando Claude lee o busca (`Read`, `Grep`, `Glob`, `WebFetch`, `WebSearch`, `ToolSearch`…).
**Verificación:** mod 52/52 (prueba nueva; las pruebas de «sin hoja especial» ahora usan `necesita`), laboratorio 21/21, tsc, validate y `prueba_humo.py` limpios. **No visto aún en pantalla real.** Sin cambios en Git.
**Serie naranja (8 fotogramas, 8 fps):** pensando, responde, escribiendo, leyendo, terminado, hula. **Lila (original, 4 fotogramas):** nueva, necesita, falla, para, duerme; «baile» ya no se usa.
**Copias:** `respaldos\EMI-CLAUDE-LEYENDO-originales\` (SHA-256), `respaldos\mascota-2026-10-10-antes-de-leyendo-claude\`.

## 28. Los 6 estados de 8 fotogramas vuelven a **5 fps**
**Pedido:** a 8 fps se veía muy rápido (§26). **Cambio:** pensando, responde, escribiendo, leyendo, terminado y hula van a **5 fps**: cada dibujo 200 ms, ciclo de 1,6 s. En `ESTADOS` de `animaciones_mod.py` (→ `ESPECIAL`) y `CINCO_FPS` de `emi_escritorio.pyw`. Con 5 fps «hula» (antes 4) vuelve a usar el reloj rápido de 150 ms de `ajustarRapido` (fps > 4). Pruebas actualizadas (mod 52/52), tsc y validate limpios; Emi escritorio reiniciada. **No visto aún en pantalla real.** Los de 4 fotogramas (nueva y duerme: 2 fps; necesita, falla y para: 4 fps) sin cambios. Sin cambios en Git.

## 29. Todos los estados a **4 fps**
**Pedido:** que todos los estados vayan a 4 fps (antes: los 6 estados de 8 fotogramas a 5 fps; nueva y duerme a 2 fps; necesita, falla y para a 4).
**Cambio:** `ESTADOS` de `animaciones_mod.py` (→ `ESPECIAL`) a 4 para los 6 estados nuevos; `LENTOS` desaparece de `dibujo.ts` (`indice` avanza un fotograma por tic en todos, así nueva y duerme pasan de 2 a 4 fps); en `emi_escritorio.pyw` una sola constante `FPS = 4`. Como 4 fps coincide con el latido de 250 ms, ya no hace falta el reloj rápido (`ajustarRapido` no arranca con fps ≤ 4): menos redibujados que a 5 u 8 fps. Ciclo de 8 fotogramas: 2 s; de 4 fotogramas: 1 s.
**Verificación:** mod 52/52 (pruebas de tiempos y de `indice` actualizadas), laboratorio 21/21, tsc y validate limpios, `prueba_humo.py` limpio; Emi escritorio reiniciada. **No visto aún en pantalla real.** Sin cambios en Git.

## 30. Ciclo de **3 segundos** en todos los estados (reemplaza §29)
**Pedido:** que todos los estados tengan 3 segundos de duración de un ciclo.
**Resultado:** los estados de **8 fotogramas** cambian de dibujo cada **375 ms** (2,67 fps) y los de **4 fotogramas** cada **750 ms** (1,33 fps); el ciclo completo de cualquiera dura 3 s. Ya no hay un número de fps: es `CICLO_MS = 3000` en `mod\hooks\dibujo.ts`.
**Cómo:** `fotogramaEn(estado, tam, ms)` (ahora válido para cualquier tamaño, no solo las hojas nuevas) calcula el fotograma desde el tiempo transcurrido; el panel, la banda del terminal y el SVG de escritorio lo usan para **todos** los estados (antes los de 4 fotogramas usaban el contador de tics). `animaciones_mod.py` y el tipo `ESPECIAL` perdieron el campo `fps`. En `emi_escritorio.pyw` la constante `CICLO_S = 3.0` sustituye a `FPS`.
**Reloj extra:** 750 ms es múltiplo del latido de 250 ms, así que los de 4 fotogramas no necesitan nada más; 375 ms no lo es, así que mientras dura un estado de 8 fotogramas corre un reloj de **125 ms** (`ajustarRapido`; fijo, ya sin depender de fps). Como «hula» (de guardia) es de 8 fotogramas, en reposo la Emi de Claude se redibuja ~8 veces por segundo.
**Verificación:** mod 53/53 (prueba nueva de ciclo para 8 y 4 fotogramas; las de tiempos actualizadas), laboratorio 21/21, tsc y validate limpios, `prueba_humo.py` (ciclo en Emi escritorio) limpio. **No visto aún en pantalla real.** Sin cambios en Git.
**Tabla final:** pensando, responde, escribiendo, leyendo, terminado, hula: 8 fotogramas, 375 ms, ciclo 3 s. nueva, necesita, falla, para, duerme (y baile, sin uso): 4 fotogramas, 750 ms, ciclo 3 s.

## 31. Ciclo de 2 s en todos los estados (2026-10-10)
**Pedido:** que todos los estados completen su ciclo en 2 s (antes 3 s, §30). Con 8 fotogramas cada dibujo dura 250 ms (≈4 fps) y con 4 fotogramas 500 ms (2 fps); ambos múltiplos del latido de 250 ms.
**Cambios:** `CICLO_MS = 2000` en `mod\hooks\dibujo.ts`; `CICLO_S = 2.0` en `mod\escritorio\emi_escritorio.pyw`; comentarios en `register.tsx` y `animaciones_mod.py`; pruebas (`mascota.test.ts`, `prueba_humo.py`) ajustadas a 250/500 ms y 2 s.
**Copia previa:** `respaldos\ciclo-3s-antes-de-2s-2026-10-10\`.
**Verificación:** mod 53/53, laboratorio 21/21, `prueba_humo.py` OK, validate pasa con avisos. No visto en pantalla. El reloj rápido de 125 ms (`ajustarRapido`) sigue activo en los estados de 8 fotogramas aunque ya no hace falta (250 ms = latido); quitarlo ahorraría redibujos, no se hizo sin pedirlo.

## 32. 5 fps en todos los estados (2026-10-10)
**Pedido:** que todos los estados vayan a 5 fps. Esto sustituye al ciclo fijo de 2 s (§31): ahora cada dibujo dura 200 ms, así que el ciclo es de **1,6 s con 8 fotogramas y 0,8 s con 4**.
**Cambios:** `CICLO_MS` → `PASO_MS = 200` en `mod\hooks\dibujo.ts`; `CICLO_S` → `PASO_S = 0.2` en `emi_escritorio.pyw`; `ajustarRapido` en `register.tsx` ahora corre siempre un reloj de 100 ms (antes solo en estados con 8 fotogramas), porque 200 ms no coincide con el latido de 250 ms; pruebas ajustadas.
**Copia previa:** `respaldos\ciclo-2s-antes-de-5fps-2026-10-10\`.
**Verificación:** mod 53/53, laboratorio 21/21, `prueba_humo.py` OK. No visto en pantalla. Coste: ~10 redibujos/s en todos los estados (antes 4/s en los de 4 fotogramas).

## 33. «Necesita» con arte nuevo (8 fotogramas, 5 fps) (2026-10-10)
**Pedido:** actualizar «necesita» con `arte\EMI-CLAUDE-NECESITA` (1.png a 8.png, 1254x1254, transparencia real, ~47 % transparente, texto «¡TE NECESITO!» y contorno oscuro). 8 fotogramas distintos, ninguno idéntico.
**Método:** modo `ilustrada` (Lanczos premultiplicado, escena ancha), sin tarjeta lila (fondo transparente, como las demás de la serie naranja). Error de color nat60 15,5 y nat28 14,1 (paleta de 88; el rojo/dorado del vestido y el pelo pierden matiz).
**Dónde:** estado `necesita` añadido a `animacion_nativa.py`, `animaciones_mod.py` (hojas `N5`/`N5S`), `exportar_frames.py` (HD, para Emi escritorio), laboratorio (`necesita.ts`, `convdibujo.ts`, `/emiconv necesita`) y pruebas del mod (`necesita` ya no es el ejemplo de estado sin animación propia: pasó a `falla`; prueba nueva para `necesita`). Cubre los 5 lugares: panel y banda del terminal, panel y banda de escritorio y Emi escritorio.
**Copias:** `respaldos\necesita-originales\` (con SHA-256) y `respaldos\mascota-2026-10-10-antes-de-necesita\`.
**Verificación:** mod 54/54, laboratorio 21/21, tsc de ambos limpio, validate (mod y raíz) pasa con avisos, `prueba_humo.py` OK. Emi escritorio reiniciada y caché `cache_hd` borrada. **No visto en pantalla todavía.**
**Pendiente de arte nuevo:** nueva, falla, para y duerme.

## 34. «Duerme» con arte nuevo (8 fotogramas, 5 fps) (2026-10-10)
**Pedido:** actualizar «duerme» con `arte\EMI-CLAUDE-DUERME` (1.png a 8.png, 1254x1254, transparencia real, contorno oscuro). Emi dormida de lado con «zzz» azules; 8 fotogramas distintos.
**Método:** modo `ilustrada`, sin tarjeta lila. Error de color nat60 15,6 y nat28 12,1. La figura es baja y ancha: en el 60x60 ocupa la mitad inferior del lienzo y las «zzz» salen pequeñas.
**Dónde:** `animacion_nativa.py`, `animaciones_mod.py` (hojas `D5`/`D5S`), `exportar_frames.py` (HD), laboratorio (`duerme.ts`, `convdibujo.ts`, `/emiconv duerme`) y pruebas del mod (el ejemplo de estado de 4 fotogramas pasó de `duerme` a `para`; prueba nueva para `duerme`). Los 5 lugares: panel y banda del terminal, panel y banda de escritorio y Emi escritorio.
**Copias:** `respaldos\duerme-originales\` (SHA-256) y `respaldos\mascota-2026-10-10-antes-de-duerme\`.
**Verificación:** mod 55/55, laboratorio 21/21, tsc limpio, validate (mod y raíz) con avisos, `prueba_humo.py` OK. Emi escritorio reiniciada, caché borrada. **No visto en pantalla.**
**Pendiente de arte nuevo:** nueva, falla y para.

## 35. El chat de Emi escritorio muestra el modelo (2026-10-11)
**Pedido:** debajo del detalle del chat (frase de estado) de Emi escritorio, el modelo que trabaja; si Opus delega en un ayudante (`emi-sonnet`, `emi-haiku`), que salga el del ayudante.
**Cómo (mínimo):** `register.tsx` anota en `agent.spawn` el modelo de cada ayudante por su `agentId`; en `tool.call` toma el de la sesión (`$.session.model()`) o el del ayudante, y lo publica como `modelo` en el archivo de sesión. Al terminar el turno vuelve al de la sesión. `emi_escritorio.pyw` lo añade como última línea del detalle. Formato: «Opus 5.5», «Sonnet 5.5 (emi-sonnet)».
**Solo en el chat de Emi escritorio**; el panel y la banda dentro de Claude no cambian.
**Copia:** `respaldos\mascota-2026-10-11-antes-de-modelo-en-chat\`. **Verificación:** mod 55/55, tsc limpio, validate con avisos, `prueba_humo.py` OK. Sin prueba automática del cambio de modelo (el kit no simula ayudantes). **No visto en pantalla.**

## 36. Barra del límite de la sesión en el chat de Emi escritorio (2026-10-11)
**Pedido:** una barra con el % que queda de la sesión actual. **Interpretación:** el límite de uso de la suscripción en su ventana de **5 horas** («sesión actual» del uso de Claude), no la ventana de contexto de la conversación.
**Cómo:** `register.tsx` escucha `session.measure` (lo envía el motor tras cada turno y cuando el límite se mueve un punto), toma `rateLimits` de tipo `five_hour` y publica `restante = 100 - percentUsed`. `emi_escritorio.pyw` (`barra`) lo dibuja como texto: `██████░░░░ 62 % de la sesión`, última línea del chat. Sin suscripción o antes del primer turno no sale.
**Copia:** `respaldos\mascota-2026-10-11-antes-de-barra-limite\`. **Verificación:** autocomprobación de `barra`, mod 55/55, tsc limpio, `prueba_humo.py` OK. **No visto en pantalla**; el evento no se puede simular en el kit.

## 37. Barra de la sesión: muestra lo usado y con diseño gráfico (2026-10-11)
**Pedido:** ver el % **usado** (no el que queda) y un diseño menos simple. **Cambio:** el mod publica `usado` (`percentUsed` de `five_hour`) en vez de `restante`; Emi escritorio dibuja al final del chat un texto pequeño «Sesión actual: 20 % usado» y una barra de color en un `Canvas` (verde < 50 %, ámbar < 80 %, rojo después). Se quitó la barra de texto `█░`.
**Copia:** `respaldos\mascota-2026-10-11-antes-de-barra-grafica\`. **Verificación:** mod 55/55, tsc limpio, `prueba_humo.py` con comprobaciones nuevas (texto, colores, barra al final). **No visto en pantalla.**

## 38. Barra de la sesión: vertical, a la derecha de Emi (2026-10-11)
**Pedido:** la barra del % usado, vertical, a la derecha de Emi escritorio y con el número dentro. **Cambio:** sale del chat; ahora es un `Canvas` opaco (24 px de ancho, 45 % del alto de Emi) colocado en el borde derecho de la ventana de Emi (`dibujar_uso`), se llena desde abajo con el color por tramos (verde/ámbar/rojo) y lleva «20%» en el centro. Se ve siempre que haya dato, aunque el chat esté oculto. Solo cambió `emi_escritorio.pyw` (y `prueba_humo.py`).
**Copia:** `respaldos\mascota-2026-10-11-antes-de-barra-vertical\`. **Verificación:** `prueba_humo.py` OK (barra colocada a la derecha, texto «20%», se oculta sin dato). **No visto en pantalla.**

## 39. Cuenta atrás de la sesión sobre la barra (2026-10-11)
**Pedido:** encima de la barra, cuándo se renueva la sesión actual. **Cambio:** el mod publica `reinicio` (`resetsAt` de `five_hour`); Emi escritorio muestra encima de la barra lo que falta («2h10m», «35m»), con `falta()`, y lo refresca cuando cambia el texto. **Copia:** `respaldos\mascota-2026-10-11-antes-de-reinicio\`. **Verificación:** mod 55/55, tsc limpio, `prueba_humo.py` (cuenta atrás y casos sin dato o pasados). **No visto en pantalla.**

## 40. Tuerca de configuración en Emi escritorio (2026-10-11)
**Pedido:** una tuerca bajo la barra que abra una interfaz con botones: activar/desactivar la barra, ver el cuadro de estados y ocultar/mostrar a Emi; la tuerca nunca desaparece; la interfaz con cerrar y minimizar arriba a la derecha.
**Cómo:** `⚙` en la ventana de Emi bajo la barra (siempre colocada en `dibujar_uso`). La interfaz es una ventana normal de Windows (`abrir_panel`, sin maximizar): sus botones nativos de minimizar y cerrar están arriba a la derecha; pulsar la tuerca la vuelve a mostrar. «Ver cuadro de estados» abre una tabla con las columnas fijas, calculada de los fotogramas cargados (`filas_cuadro`). Ocultar a Emi quita el dibujo y el chat; la barra y la tuerca siguen. Barra y oculta se guardan en `escritorio.json`.
**Verificación:** `prueba_humo.py` (tuerca visible con barra apagada y Emi oculta, 11 filas del cuadro, panel se cierra). **No visto en pantalla.** Sin copia previa de este paso (la última es `respaldos\mascota-2026-10-11-antes-de-reinicio\`).

## 41. Caída al soltar (2026-10-11)
**Pedido:** al arrastrar a Emi hacia arriba y soltarla, que caiga al suelo; con un botón en la tuerca. Los costados no importan (el usuario hará después una animación para moverla de lado).
**Cómo:** botón «Caída al soltar: activada/desactivada» (por defecto activada, se guarda como `caida`). Al soltar (`soltar` → `caer`), baja acelerando cada 16 ms hasta que su borde inferior toca el **suelo**: el borde del área útil de Windows (`SPI_GETWORKAREA`, encima de la barra de tareas; en este equipo y = 816 en una pantalla de 1536×864). Si ya está abajo no sube. La x no cambia.
**Copia:** `respaldos\mascota-2026-10-11-antes-de-caida\`. **Verificación:** `prueba_humo.py` (soltada en y = 20 llega exacto al suelo). **No visto en pantalla.**

## 42. Estado nuevo «guardando» (en Obsidian) (2026-10-11)
**Pedido:** crear el estado de guardar en Obsidian con `arte\EMI-CLAUDE-SAVE-OBSIDIAN` (1–8.png, 1254x1254, transparencia; Emi con nota y cristal morado, globo «Guardando en mi segundo cerebro…»).
**Cuándo sale:** una herramienta que escribe (`Write`, `Edit`, `Bash`, `PowerShell`, MCP de escritura) cuyo destino o comando menciona «obsidian» (ruta del vault, CLI `obsidian`) o un MCP de Obsidian (`estadoDeHerramienta(tool, entrada)`). Leer el vault sigue siendo «leyendo».
**Dónde:** estado `guardando` en `types`, `estados.ts` (frases, color `#9b6bdf`, cara `(•ᴗ•)📝`), hojas `G5`/`G5S` (modo `ilustrada`, error de color 19,9 / 16,2: el texto del globo del dibujo no se lee a 60x60), HD de Emi escritorio (frase, prioridad 3, chat activo, cuadro de estados con 12 filas), laboratorio (`/emiconv guardando`). Tamaños antiguos (mini) sin sprite propio: usan el de guardia.
**Copias:** `respaldos\guardando-originales\` (SHA-256), `respaldos\mascota-2026-10-11-antes-de-guardando\`. **Verificación:** mod 57/57 (prueba de hoja y de detección), laboratorio 21/21, tsc, validate, `prueba_humo.py`. **No visto en pantalla.**

## 43. Estado «caida» con animación (solo Emi escritorio) (2026-10-11)
**Pedido:** animar la caída al soltar con `arte\EMI-CLAUDE-CAIDA` (8 PNG 1254x1254: 1–4 cayendo, 5 aterriza con polvo, 6–8 se levanta).
**Cómo:** solo en Emi escritorio (la caída no existe dentro de Claude, así que no va a los otros 4 lugares). `exportar_frames.py` copia `caida` a `hd\`. Al empezar a caer (`caer`), `caida_fase = ('cae', t)`: repite 1–4 a 5 fps; al tocar el suelo, `('aterriza', t)`: pasa una vez por 5–8 (0,8 s) y `fin_caida` vuelve al estado de Claude. Si ya estaba en el suelo, no hay animación. Fila «caida» en el cuadro de estados.
**Copias:** `respaldos\caida-originales\` (SHA-256), `respaldos\mascota-2026-10-11-antes-de-caida-animada\`. **Verificación:** `prueba_humo.py` (cae, aterriza con fotogramas 5–8 y termina). **No visto en pantalla.**

## 44. Estado «sujeta» al arrastrar (solo Emi escritorio) (2026-10-11)
**Pedido:** cuando el usuario presiona a Emi con el cursor para arrastrarla, animación de `arte\EMI-CLAUDE-SUJETA` (8 PNG, Emi mareada, en bucle).
**Cómo:** al pulsar (`empezar_arrastre`) se anota `sujeta`; `pintar` da prioridad a la caída, luego a «sujeta» (bucle a 5 fps), luego al estado de Claude. Al soltar (`soltar`) se quita y, si está activada, empieza la caída. `exportar_frames.py` copia `sujeta` a `hd\`. Fila en el cuadro de estados (14).
**Copias:** `respaldos\sujeta-originales\` (SHA-256), `respaldos\mascota-2026-10-11-antes-de-sujeta\`. **Verificación:** `prueba_humo.py`. **No visto en pantalla.**

## 45. Barra del caché («tiempo para perder el contexto») (2026-10-11)
**Pedido:** una segunda barra a la derecha con el tiempo estimado para perder el contexto, de 1 hora. **Significado:** el caché de la conversación dura 1 h desde la última petición al modelo (5 min si la cuenta pasa a sobreconsumo); al caducar, el siguiente mensaje reprocesa toda la conversación y gasta más. La conversación no se borra.
**Cómo:** el mod publica `actividad` (ms) en cada herramienta y al terminar cada turno de la sesión principal. Emi escritorio dibuja una barra vertical a la izquierda de la de uso, rotulada «caché», que se vacía en 60 min, con los minutos dentro («40m») y color verde > 30 min, ámbar > 10, rojo después. Se enciende/apaga con el mismo botón «Barra de uso» de la tuerca.
**Copia:** `respaldos\mascota-2026-10-11-antes-de-barra-cache\`. **Verificación:** mod 57/57, tsc limpio, `prueba_humo.py` (texto, colocación). Es una estimación: el motor no informa del caché real. **No visto en pantalla.**
**Arreglo (mismo día):** las barras toman `usado`/`reinicio` de la sesión más reciente que los tenga y `actividad` de la más reciente de todas, no solo de la sesión que muestra Emi (otras sesiones con un mod viejo no los publican). Tras `/reload-plugins`, la barra del caché aparece con la primera herramienta.
**Barras fuera del dibujo (mismo día):** la ventana de Emi escritorio es `margen` (2×24+24 px) más ancha por la derecha y Emi se coloca centrada en su zona (`poner_emi`), así las barras y la tuerca quedan a su derecha sin taparla.

## 46. Estado «caminando»: vuelve a su sitio (solo Emi escritorio) (2026-10-11)
**Pedido:** si el usuario deja a Emi en otra posición horizontal, que vuelva caminando al punto donde estaba, con `arte\EMI-CLAUDE-CAMINANDO` (8 PNG, mira a la derecha).
**Cómo:** «su sitio» es `casa_x` (se guarda en `escritorio.json`; arranca en la x guardada entonces, 1208). Al soltarla: si «caída al soltar» está activada, cae, aterriza y luego camina; si no, camina directamente (`volver`: 2 px cada 16 ms ≈ 125 px/s, animación a 5 fps, reflejada con `subsample(-1, 1)` cuando va a la izquierda). Agarrarla de nuevo corta la caída o el paseo (`movimiento`). Fila en el cuadro de estados (15).
**Copias:** `respaldos\caminando-originales\` (SHA-256), `respaldos\mascota-2026-10-11-antes-de-caminando\`. **Verificación:** `prueba_humo.py` (vuelve exacta a su sitio) y espejo probado en Tk. **No visto en pantalla.** Pendiente: no hay botón para cambiar «su sitio».

## 47. Paseo cuando no tiene nada que hacer (2026-10-11)
**Pedido:** si Emi no hace nada durante 1 min, que se ponga a caminar. **Cómo:** en Emi escritorio, si el estado es de guardia o dormida y no la sujetas, no cae ni camina, tras `PASEO_S = 60` s sale de paseo (`pasear`): camina a un punto a 120–300 px de su sitio (dentro de la pantalla), espera 3 s y vuelve a su sitio. Cualquier trabajo de Claude o agarrarla reinicia el minuto. Oculta no pasea.
**Arreglo encontrado al probar:** podían quedar dos paseos a la vez (p. ej. el de después de una caída y otro); ahora cada paseo nuevo cancela el anterior (`caminar_a` sube `movimiento`). La prueba de humo ya no deja que su Emi se cierre sola a mitad.
**Copia:** `respaldos\mascota-2026-10-11-antes-de-paseo\`. **Verificación:** `prueba_humo.py` (vuelve a su sitio, paseo llega a ≥ 100 px). **No visto en pantalla.**

## 48. Tiempo trabajado en la conversación, junto a la tuerca (2026-10-11)
**Pedido:** una barra horizontal pequeña a la izquierda de la tuerca con el tiempo total que Claude ha trabajado en el chat (2 min + 30 s = «2m 30s»).
**Cómo:** el mod suma la duración de cada turno de la sesión principal (`trabajado`, ms) y publica también `inicioTurno` mientras trabaja; al cargar (`session.start`, también tras `/reload-plugins`) recupera `trabajado` de su archivo de sesión; `/clear` lo pone a 0. Emi escritorio muestra «⏱ 2m 30s» (formatos: «45s», «2m 30s», «1h 05m»), contando en vivo el turno en marcha, de la conversación que muestra Emi. Se apaga con el botón «Barra de uso».
**Copia:** `respaldos\mascota-2026-10-11-antes-de-tiempo-trabajado\`. **Verificación:** mod 57/57, tsc, `prueba_humo.py` (formato). Las pruebas de caminar/pasear de la prueba de humo tenían márgenes de tiempo cortos y fallaban de forma intermitente: ampliados. **No visto en pantalla.**
**Recuperar al recargar (mismo día):** en `session.start` el mod relee de su archivo de sesión `usado`, `reinicio`, `actividad` y `trabajado`, así las barras no se vacían tras `/reload-plugins`.

## 49. Un interruptor por barra en la tuerca (2026-10-11)
Antes un solo botón «Barra de uso» apagaba todo. Ahora hay tres: «Barra de uso de la sesión», «Barra del caché» y «Tiempo trabajado» (`BARRAS`; se guardan como `barra_uso`, `barra_cache`, `barra_tiempo`; si no existen, toman el valor del antiguo `barra`). Copia: `respaldos\mascota-2026-10-11-antes-de-botones-barras\`. `prueba_humo.py` OK. No visto en pantalla.

## 50. Banda en la app de Claude: apagada por defecto, botón en la tuerca (2026-10-11)
**Pedido:** un botón en la tuerca para mostrar u ocultar la banda de Emi en la app de escritorio de Claude (sobre el prompt), siempre desactivada salvo que el usuario la encienda.
**Cómo:** Emi escritorio escribe `~\.claude\mascota\banda_app.txt` («on»/«off») con el botón «Emi en la app de Claude»; el mod lo lee al empezar y cada 2 s (`leerBandaApp`) y, si está apagada, la banda de las superficies que no son el terminal (app de escritorio, editor, móvil) no dibuja nada. El terminal no cambia. También `/emi app` y `/emi sin-app`.
**Copia:** `respaldos\mascota-2026-10-11-antes-de-banda-app\`. **Verificación:** mod 58/58 (prueba nueva: apagada por defecto, `/emi app` la muestra, `/emi sin-app` la quita), tsc, `prueba_humo.py`. **No visto en pantalla.**

## 51. Marco de arte para las barras de uso y caché (2026-10-11)
**Usuario:** usar `arte\barra-emi-claude\1.png` para la barra; en las dos (uso y caché), unos 60 px.
**Hecho:** `exportar_frames.py` genera `escritorio\marco_barra.png` (60×130, hueco interior vaciado, vecino más cercano, alfa todo o nada). En `emi_escritorio.pyw`, `pintar_barra()` dibuja fondo claro + relleno desde abajo en el hueco (24,26)-(37,107), el marco encima y el texto girado 90° (el hueco mide 13 px). Colores verde/ámbar/rojo sin cambios. Prueba de humo ok; captura real con Tk revisada. Respaldo: `respaldos\escritorio-2026-10-11-antes-de-marco-barra\`.
**Ajuste (mismo día):** barras más grandes (90×196, hueco (36,39)-(55,160)); número en horizontal arriba del hueco sobre una pastilla clara (en el medio lo tapan las gemas); «caché» y el tiempo de renovación centrados encima de su barra.
**Barras pegadas (mismo día):** Emi y las dos barras se dibujan en un solo Canvas (`lienzo`; Emi es el ítem `emi`, las barras llevan tags `barra`/`cache`/`uso`). `mostrar()` calcula fila por fila el perfil derecho de Emi y el izquierdo del marco (`perfil()`, cacheado, ~17 ms por dibujo) y deja el marco a 2 px de ella; los lazos entran en sus huecos. Uso a 4 px del caché (`SEP_BARRAS`). La ventana ya no se sale por la derecha. Prueba de humo actualizada y en verde; captura real revisada.
**Barras quietas (mismo día):** la posición se calcula con el dibujo más ancho de todo el estado (`mostrar(foto, grupo, todas)`, cacheado por grupo y escala): no bailan con la animación, pero se mueven al cambiar de estado. La de uso va pegada a la del caché (`paso_barras()`: lazos a 2 px, `SEP_BARRAS = 2`). Prueba nueva: 8 fotogramas, misma posición.
**Globo semitransparente (mismo día):** con el ratón encima, el globo (frase de estado) baja a opacidad 0,45 (`ALFA_GLOBO`); al salir vuelve a 1. `globo_opaco()` comprueba que el ratón salió de verdad (el `<Leave>` también salta entre sus etiquetas).
**Sin caída = quieta (mismo día):** con «caída al soltar» desactivada, al soltarla se queda donde la dejaste (ese punto pasa a ser `casa_x`), no vuelve caminando y no sale a pasear. Prueba de humo actualizada.
**Panel de configuración nuevo (mismo día):** con el arte de `arte\interfaz` (1 ventana, 3/4 fila normal/encima, 6/7 interruptor sí/no). `exportar_frames.py` genera `escritorio\interfaz\` (fondo 380×565 con el interior vaciado y alargado, filas 330×46 con los extremos conservados, interruptores, cabecera con la cabeza de Emi de guardia), con Lanczos y alfa todo o nada. El panel es un Toplevel sin marco de Windows hecho con un Canvas: se arrastra por la barra de título, minimizar lo esconde (la tuerca lo reabre) y cerrar lo cierra. Filas en `FILAS_PANEL`; cada una se resalta al pasar el ratón. Prueba de humo actualizada.
**Cabecera del panel:** ahora usa `arte\interfaz\emi-para-interfaz.png` (Emi apoyada en una barra), recortada hasta la barra y reducida a 112 px de alto; la barra queda sobre la primera fila. El panel se abre en el centro de la pantalla.
**Iconos y un interruptor en cada fila:** iconos de `arte\interfaz\ICONO-INTERFAZ\1..7.png` (exportados a `interfaz\icono_<clave>.png`, 34 px). «Ver cuadro de estados» y «Ocultar a Emi» también llevan interruptor (cuadro abierto / Emi oculta); al cerrar el cuadro con la X su interruptor se apaga.
**Atenuar fuera de Claude (opción 8 del panel, activada por defecto):** cada 0,5 s `vigilar_foco()` mira la ventana en primer plano (`ventana_delante()`, ctypes): si no es Claude (`claude.exe`, `windowsterminal.exe`), ni el escritorio/barra de tareas, ni la propia Emi, Emi y su globo bajan a opacidad 0,4 (`ALFA_LEJOS`). Se guarda como `atenuar` en escritorio.json. Icono provisional: el del ojo (falta un 8.png en ICONO-INTERFAZ). Panel alargado a 8 filas (fondo 380×617).
**Opción «Frase de estado» en el panel (9.ª fila):** interruptor que muestra u oculta el globo (`alternar_mensaje`, ya existía en el menú de clic derecho). Icono provisional: el del ojo. Panel alargado a 9 filas (fondo 380×669).
