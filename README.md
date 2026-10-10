# Emilia (Emi) — mascota pixel para Claude Code

Mod de Claude Code (hooks en TS/TSX) con una mascota animada: 12 estados (pensando, hula y escribiendo con animación propia de 5 fotogramas a 60x60), panel lateral acoplado (Dock), banda sobre el prompt y una Emi flotando en el escritorio de Windows. Creado con Claude Code 2.1.294 / 2.1.295 en Windows 11.

## Instalarlo (una sola línea)
En una sesión de **terminal** de Claude Code (2.1.294 o más nuevo, Windows):

```
/plugin install mascota --marketplace SMRJ1421/emilia-mascota
```
Responde `y` a «Add marketplace?», elige el ámbito (usuario) con Enter, y listo: Emi funciona en esa sesión y en las siguientes (también en la app de escritorio, que carga los mods instalados desde la terminal). Sin reinstalar para actualizar: `claude plugin update mascota`.

**Requisitos**
- **Emi** (banda, panel, escritorio de Claude): solo Claude Code. Los sonidos y avisos usan PowerShell (Windows).
- **Emi escritorio** (la que flota fuera de Claude): además **Python 3 con tkinter** (el instalador de python.org lo trae; `pythonw` en el PATH). Sin Python, Emi sigue funcionando dentro de Claude y avisa una vez. No necesita ningún otro paquete.
- El repositorio debe ser **público** (o la persona debe tener acceso a él) para que la instalación funcione.

**Primeros pasos dentro de Claude**
- `/emi panel` (panel acoplado), `/emi banda`, `/emi probar` (enseña los estados).
- `/emi escritorio` y `/emi sin-escritorio`: Emi flotando sobre el escritorio mientras haya una conversación abierta (se arrastra; clic derecho: tamaño o cerrar).
- Más: `/emi grande | normal | mini | compacta | oculta | sonido | silencio | avisos | sin-avisos`.

**Para desarrollarlo desde la carpeta:** `claude --plugin-dir "<ruta>\emilia-mascota\mod"` (o `CLAUDE_CODE_PLUGIN_DIRS`). Comprobar: `claude plugin validate mod` y `claude plugin test mod` (49 pass); laboratorio: `claude plugin test laboratorio` (21 pass).

## Carpetas
| Carpeta | Contenido |
|---|---|
| `mod\` | **El mod principal** (lo que se instala), con `escritorio\` (Emi escritorio: programa Python con sus fotogramas) y `hooks\animaciones.ts` (estados con animación propia). `hooks\register.tsx` es el módulo; `sprites.ts` los 5 tamaños de sprites; `dibujo.ts` celdas Raster/SVG; `deteccion.ts` fallo real; `estados.ts` frases y estados; `tests\` |
| `laboratorio\` | Mod aparte `mascota-lab` con prototipos y bancos (`/emilab`, `/emiproto`). No es necesario para usar a Emi |
| `arte\` | PNG originales: hoja de 12 estados, hoja de animación y `animacion.png` (20 estados nuevos, **aún no integrados**) |
| `.claude-plugin\marketplace.json` | Hace del repositorio un marketplace: es lo que permite instalar con una sola línea |
| `scripts\pipeline-sprites\` | Python que convierte los PNG en `sprites.ts` (`emi_lib2.py`, `gen_ts.py`, `regen2.py`…). Revisa rutas: apuntan a `C:\Users\Admin0011\Downloads\…`; cámbialas a `..\..\arte\` |
| `scripts\diagnostico\` | Scripts de comparación y diagnóstico de fidelidad |
| `scripts\tsconfig\` | tsconfig usados para comprobar TypeScript (`npx -y -p typescript@5.6 tsc -p <carpeta>`) |
| `docs\` | `INFORME_TECNICO_EMILIA.md` (secciones 1–13) e `INFORME_COMPARATIVO_MASCOTAS.md` (4 repos estudiados, licencias, bench) |
| `investigacion\`, `pruebas\` | Capturas y comparativas antes/después, informes de etapas |
| `referencia-api\` | Extracto de los tipos de la API de mods (`claude-code`) |
| `datos-laboratorio\` | `medidas.json` (dock 64×35, banda 15 filas), `bench.json`, `bench_v1_2026-10-08.json` |
| `respaldos\` | Copias del mod antes de cada cambio grande |

## Estado a 2026-10-09 (resumen; el proceso completo está en `docs\CHAT_ACTUALIZACION_ANIMACION.md`)
- Hecho: sprites fieles a los PNG (5 tamaños), panel Dock con tamaño adaptativo, fallo real (denegaciones/interrupciones no asustan), `ExitPlanMode` → «necesita», celdas Raster con espacio (63 % menos glifos, imagen idéntica).
- Pendiente de tu decisión: 8 fps con redibujo normal (`/emiproto atomo8`); `blit` descartado por el banco real.
- Fuera de alcance por ahora: los 20 estados nuevos / 8 fotogramas y el sprite de banda 18×28.
- Sin verificar en terminal real: correlación `tool.check` → `tool.call`; aspecto de las celdas nuevas en tu Windows Terminal.

## Notas
- Las preferencias de Emi (tamaño, sonido, avisos) viven en el almacén del motor (`$.store`) de cada PC; no viajan con la carpeta.
- Nunca guardar claves ni tokens aquí.
- Idea de la detección de fallos tomada de dgokcin/claude-pokemon-mod (sin licencia): solo la idea, código propio.
