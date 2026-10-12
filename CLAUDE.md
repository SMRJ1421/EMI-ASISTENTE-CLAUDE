# Emilia (Emi) — guía del proyecto para sesiones nuevas

Lee esto primero. Es el historial completo del proyecto, las reglas del usuario y lo que falta. El README.md explica cómo cargar y compartir el mod; este archivo explica **cómo se llegó aquí y cómo seguir**.

## 0. Estado vigente (2026-10-11) — manda sobre el resto de este archivo
- **Estados:** 11 en uso (`baile` fuera). Arte nuevo naranja, 8 fotogramas: pensando, responde, escribiendo, leyendo, terminado, hula, necesita, duerme. Arte lila, 4 fotogramas: nueva, falla, para. **Todos a 5 fps** (`PASO_MS = 200` en `dibujo.ts`; `PASO_S` en Emi escritorio).
- **Emi escritorio** (`mod\escritorio\emi_escritorio.pyw`): chat (= «frase de estado») con frase, detalle y **modelo que trabaja**; se vuelve semitransparente con el ratón encima. **Dos barras** con el marco de `arte\barra-emi-claude` (90×196): caché (1 h) y % de la sesión (5 h), número en horizontal arriba. Emi y las barras van en **un solo Canvas**: las barras quedan a 2 px de Emi (perfil fila a fila) y quietas durante la animación (manda el dibujo más ancho del estado). Estados solo de escritorio: sujeta, caida, caminando (y guardando).
- **Panel de la tuerca ⚙** con el arte de `arte\interfaz` (ventana, filas, interruptores, `emi-para-interfaz.png`, iconos `ICONO-INTERFAZ\1..7`): 8 opciones con interruptor, se abre centrado. Opción 8 «Atenuar fuera de Claude»: Emi al 40 % si delante no está `claude.exe`/`windowsterminal.exe` ni el escritorio. Sin «caída al soltar», Emi se queda donde la dejas. Piezas generadas por `exportar_frames.py` en `mod\escritorio\interfaz\`.
- **Pruebas:** mod 58/58, laboratorio 21/21, `mod\escritorio\prueba_humo.py`. Recargar el mod sin abrir otra sesión: `/reload-plugins`.
- **GitHub:** público, `SMRJ1421/EMI-ASISTENTE-CLAUDE`, versión 0.2.0; `arte\` no se sube. Instalar: `/plugin install mascota --marketplace SMRJ1421/EMI-ASISTENTE-CLAUDE`. Último commit subido: `5334491` (2026-10-11).
- **Equipo Emi (global, no del mod):** Opus esfuerzo bajo por defecto; ayudantes `emi-haiku` y `emi-sonnet` en `~\.claude\agents\`.
- **Historial completo:** `docs\CHAT_ACTUALIZACION_ANIMACION.md` (secciones 1–51).

## 1. Qué es
Mod de Claude Code (hooks en TS/TSX, API de mods de Claude Code ≥ 2.1.294) con una mascota pixel, «Emilia / Emi»: 12 estados (11 en uso; ver §0), en un panel lateral acoplado (Dock) o en una banda sobre el prompt. Usuario: hispanohablante, Windows 11, Claude Code 2.1.295. **Prioridad nº 1: fidelidad al arte original (PNG).**

Estados: nueva, pensando, responde, leyendo, escribiendo, necesita, falla, para, terminado, baile, hula, duerme.

## 2. Reglas del usuario (obligatorias)
- **No reemplazar el sistema Dock ni reescribir Emilia desde cero.**
- Incorporar una técnica **solo si demuestra una mejora real**; presentar resultados y **pedir autorización antes de cambios definitivos** en el mod principal. Los prototipos van en `laboratorio\`.
- Hacer **copia de seguridad antes de modificar** (aquí: commit de Git antes de cada cambio, o carpeta en `respaldos\`).
- No ejecutar ni instalar código de terceros. Sin servicios de pago ni claves de API. No tocar otros plugins, proyectos ni Obsidian.
- **No declarar que algo se ve bien en su Windows Terminal si solo se simuló**; dejar una prueba sencilla para que el usuario lo compruebe.
- Mantener: comandos `/emi`, avisos de Windows y sonidos, panel Dock, los estados y sus fotogramas (ver §0).
- Las animaciones nuevas llegan con **8 fotogramas**; si no se indican fps, preguntar.
- **No borrar archivos del usuario.** Él limpia lo que sobre.
- No subir a GitHub (`git push`) sin que lo pida. Repo **público**: https://github.com/SMRJ1421/EMI-ASISTENTE-CLAUDE (antes emilia-mascota)
- Responder en español, conciso, distinguiendo hechos / hipótesis / límites.

## 3. Estructura
Ver tabla en README.md. Resumen: `mod\` (el mod; fuente de verdad), `laboratorio\` (mod `mascota-lab` con `/emilab` y `/emiproto`), `arte\` (PNG), `scripts\` (pipeline de sprites, diagnóstico, tsconfig), `docs\` (informes técnico y comparativo), `datos-laboratorio\` (medidas y bancos), `respaldos\` (copias antiguas; fuera de Git).

Archivos del mod: `hooks\register.tsx` (único módulo de hooks), `sprites.ts` (429 KB generado, 5 tamaños × 12 × 4, RLE), `dibujo.ts` (celdas Raster, SVG, `elegirTam`, `planPanel`), `estados.ts` (frases, estados por herramienta), `deteccion.ts` (fallo real). Pruebas: `claude plugin test mod` (34), `claude plugin test laboratorio` (15), `claude plugin validate mod`. TypeScript: `npx -y -p typescript@5.6 tsc -p scripts\tsconfig\tc-mod` (y `tc2-lab`; ajusta rutas si falla).

## 4. Cómo se llegó aquí (cronología)
1. **Idea y primera versión.** Del pack `pack-mods-claude-code` (fuera de este proyecto) surgió la mascota. Se creó el mod a partir de la hoja de 12 estados y luego de `animacion de Emilia pixel de estados.png` (4 fotogramas por estado). No consume tokens (todo local).
2. **Fidelidad visual.** El render salía mal. Diagnóstico y correcciones: fondo quitado con *flood-fill* (umbral de color 28, no por umbral simple, que borraba partes blancas); rejilla real del arte de **4,75 px** (no 4); fase de rejilla compartida por estado; regla de «borde» (contorno); paleta de 88 colores con semillas por tono; compresión RLE; muestreo vecino más cercano. Un filtro eliminó zapatos/piernas (reglas de línea plana demasiado agresivas): se corrigió (ancho ≥ 90, umbral 0,8).
3. **Tamaños.** 5 sprites: S 13×20, N 26×40, M 40×60, L 52×80, XL 64×96 (píxeles). Lo que se elige depende del espacio.
4. **El límite de la banda.** Sobre el prompt solo hay 15 filas en este terminal (`AbovePrompt` se limita a media pantalla en fullscreen), así que cabía solo S. **Solución: panel Dock** (`Pane`, 64×35) que admite M, más tamaño adaptativo (`elegirTam`/`planPanel`). La banda se mantiene como respaldo (`/emi banda`).
5. **Laboratorio.** Hubo que fusionar el código de prototipos en un solo `register.tsx` porque el motor admite **un módulo de hooks por plugin** y no se puede pasar `$` entre archivos.
6. **Investigación de 4 repos** (sin ejecutar nada; ver `docs\INFORME_COMPARATIVO_MASCOTAS.md`): dgokcin/claude-pokemon-mod (sin licencia: solo se reimplementó la idea), TeXmeijin (MIT), clawd (código MIT, arte restringido), octaviusp (sin LICENSE, solo macOS). Técnicas T1–T10 evaluadas; el *vote-zoom* de dgokcin se probó y se descartó (peor que nuestros métodos).
7. **Integración autorizada (2026-10-08):** (a) *fallo real*: denegación, rechazo de permiso o interrupción ya no asustan a Emi; `ExitPlanMode` → «necesita». (b) *Celdas Raster con espacio*: si las dos mitades de una celda son iguales, un espacio con fondo en vez de `▀` (63 % menos glifos en M; imagen idéntica en los 240 fotogramas). Resultado: 34/34 pruebas, tsc limpio.
8. **Banco `blit`** (3.º punto, NO integrado): ver §7.
9. **Empaquetado:** esta carpeta + repositorio Git (hoy público; commits `68d7580`, `200a6f7`).

## 5. Cosas del motor que ya costaron tiempo (no repetir)
- Un solo módulo de hooks por plugin; `$` no se pasa a funciones de otros archivos; dos `session.start` sin matcher se rechazan.
- `Raster`/`Image` solo en terminal; `Svg` en escritorio/vscode/móvil: hay que proteger con `if (e.surface === 'terminal')`.
- Raster: celdas = tripletas Uint32 [glifo, fg, bg] en base64; límites 512×256 celdas y 1024 pares de color.
- `$.audio.play` solo funciona en macOS: en Windows se usan pitidos/globo de PowerShell.
- En Windows `HOME` puede no existir: usar `USERPROFILE`.
- Los dobles de prueba de `ui.open`/`ui.close` deben responder `{ value: … }`. Con `$.clock.now()` en el código hay que usar `mock.clock(on)`. En el kit el resultado de una herramienta trae `result` pero no `text`.
- `Write` exige `Read` previo; en Bash, los heredocs pueden colapsar `\\`.
- Los tipos de la API los escribe el motor en `mod\.claude-plugin\types\`; hay un extracto en `referencia-api\`.

## 6. Lo hecho vs. lo que falta (mejoras pendientes, por prioridad)
**Pendiente de verificar (el usuario debe mirar o probar):**
1. Aspecto de las celdas nuevas en **su Windows Terminal real** (`/emi panel`, `/emi probar`). Solo está probado que los colores coinciden exactamente; no hay captura real.
2. Con una herramienta **rechazada de verdad**, que Emi no se asuste (la correlación `tool.check` → `tool.call` por `tool_use_id` **no se puede probar en el kit**; hay respaldo por texto `RECHAZO` y por `turno abortado`).
3. Que cargue bien desde esta carpeta: `claude --plugin-dir "<ruta>\mod"`.

**Decisión del usuario pendiente:** 4 fps (actual) o **8 fps con redibujo normal** (tick 125 ms, fotograma por tiempo; coste medido igual al actual). Comparar `/emiproto atomo8` con `/emiproto blit`. **No integrar sin su aprobación.**

**Mejoras no hechas (proponer, no aplicar sin permiso):**
- `classic.PermissionRequest` y despertar a Emi con `prompt.edit` (idea de otros repos, sin integrar).
- Los **20 estados nuevos / 8 fotogramas** de `arte\animacion.png` y el sprite de banda 18×28 (el usuario dijo «para más adelante»).
- Hacer los scripts de `scripts\pipeline-sprites` portables: rutas fijas a `C:\Users\Admin0011\Downloads\…`; apuntar a `..\..\arte\` y dejar un único script de regeneración documentado (hoy hay muchos de pruebas).
- Prueba automatizada para el panel Dock (hoy se prueba el cálculo `planPanel`, no el montaje real).
- Decidir licencia del proyecto (el repo es público) (los PNG son del usuario; el arte de clawd NO se usa).
- Guardar las preferencias de Emi (`$.store`, por PC) en un archivo exportable si el usuario quiere llevarlas a otra PC.
- Quitar del repo `laboratorio\tests\tmp_cifras.test.ts` (marcador vacío) y los scripts duplicados entre `pipeline-sprites` y `diagnostico`.

## 7. Resultados del banco `blit` (para no volver a medir)
Panel acoplado, sprite M, 12 s por fase (`datos-laboratorio\bench_v2_2026-10-08.json`):
control 250 ms: 49 pasadas, 45 ms · 8 fps sin blit: 94 pasadas, 41 ms · blit 4 fps: 2 pasadas, 94 ms · blit 8 fps: 1 pasada, 211 ms.
**Ojo:** el banco v1 (`bench_v1…`) decía que blit no reducía pasadas; era una medición contaminada y **está desmentida**. `blit` quita las pasadas de dibujo pero cuesta más dentro de nuestros hooks y los bytes no bajan; el ahorro de CPU del motor no se midió (reloj de pared). Recomendación vigente: no integrar blit; si se quiere fluidez, 8 fps sin blit.

## 8. Cómo trabajar a partir de aquí
- Edita **solo en esta carpeta** (`mod\`, `laboratorio\`), no en `~\.claude\dev-mods`. La sesión puede cargar el mod con `--plugin-dir`.
- Antes de cambios grandes: `git status` limpio y commit. Después: `claude plugin validate mod`, `claude plugin test mod`, tsc.
- Los cambios en `mod\` se presentan al usuario y se esperan sus «autorizo».
- Informes: añadir secciones nuevas a `docs\INFORME_TECNICO_EMILIA.md` (va por la sección 13).
- Si el usuario pide guardar algo en su Obsidian, hay reglas propias en su `CLAUDE.md` global (usar la skill `obsidian-cli`); aquí no se escribe en Obsidian por iniciativa propia.
- Nunca guardar claves o tokens en este repositorio.
