# EMI ASISTENTE CLAUDE — Emilia (Emi), mascota pixel para Claude Code

Mod de Claude Code (hooks en TS/TSX) con una mascota animada: 11 estados en uso a 5 fps (pensando, responde, escribiendo, leyendo, terminado, hula, necesita y duerme con arte nuevo de 8 fotogramas; nueva, falla y para con el arte original de 4), panel lateral acoplado (Dock), banda sobre el prompt y una Emi flotando en el escritorio de Windows. Creado con Claude Code 2.1.294 / 2.1.295 en Windows 11.

## Instalarlo (una sola línea)
En una sesión de **terminal** de Claude Code (2.1.294 o más nuevo, Windows):

```
/plugin install mascota --marketplace SMRJ1421/EMI-ASISTENTE-CLAUDE
```
Responde `y` a «Add marketplace?», elige el ámbito (usuario) con Enter, y listo: Emi funciona en esa sesión y en las siguientes (también en la app de escritorio, que carga los mods instalados desde la terminal). Para actualizar: `claude plugin update mascota`.

Si la descarga tarda más de 2 minutos (conexión lenta), sube el límite antes de instalar: `CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS=600000`.

**Requisitos**
- **Emi** (banda, panel, escritorio de Claude): solo Claude Code. Los sonidos y avisos usan PowerShell (Windows).
- **Emi escritorio** (la que flota fuera de Claude): además **Python 3 con tkinter** (el instalador de python.org lo trae; `pythonw` en el PATH). Sin Python, Emi sigue funcionando dentro de Claude y avisa una vez. No necesita ningún otro paquete.
- El repositorio debe ser **público** (o la persona debe tener acceso a él) para que la instalación funcione.

**Primeros pasos dentro de Claude**
- `/emi panel` (panel acoplado), `/emi banda`, `/emi probar` (enseña los estados).
- `/emi escritorio` y `/emi sin-escritorio`: Emi flotando sobre el escritorio mientras haya una conversación abierta (se arrastra; clic derecho: tamaño o cerrar).
- Más: `/emi grande | normal | mini | compacta | oculta | sonido | silencio | avisos | sin-avisos`.

**Para desarrollarlo desde la carpeta:** `claude --plugin-dir "<ruta>\emilia-mascota\mod"` (o `CLAUDE_CODE_PLUGIN_DIRS`). Comprobar: `claude plugin validate mod` y `claude plugin test mod` (55 pass); laboratorio: `claude plugin test laboratorio` (21 pass).

## Carpetas
| Carpeta | Contenido |
|---|---|
| `mod\` | **El mod principal** (lo que se instala), con `escritorio\` (Emi escritorio: programa Python con sus fotogramas) y `hooks\animaciones.ts` (estados con animación propia). `hooks\register.tsx` es el módulo; `sprites.ts` los 5 tamaños de sprites; `dibujo.ts` celdas Raster/SVG; `deteccion.ts` fallo real; `estados.ts` frases y estados; `tests\` |
| `laboratorio\` | Mod aparte `mascota-lab` con prototipos y bancos (`/emilab`, `/emiproto`). No es necesario para usar a Emi |
| `arte\` | PNG originales. **No se sube a GitHub** (pesa ~100 MB y no hace falta para instalar); queda solo en el equipo del autor |
| `.claude-plugin\marketplace.json` | Hace del repositorio un marketplace: es lo que permite instalar con una sola línea |
| `scripts\pipeline-sprites\` | Python que convierte los PNG en `sprites.ts` (`emi_lib2.py`, `gen_ts.py`, `regen2.py`…). Revisa rutas: apuntan a `C:\Users\Admin0011\Downloads\…`; cámbialas a `..\..\arte\` |
| `scripts\diagnostico\` | Scripts de comparación y diagnóstico de fidelidad |
| `scripts\tsconfig\` | tsconfig usados para comprobar TypeScript (`npx -y -p typescript@5.6 tsc -p <carpeta>`) |
| `docs\` | `INFORME_TECNICO_EMILIA.md` (secciones 1–13) e `INFORME_COMPARATIVO_MASCOTAS.md` (4 repos estudiados, licencias, bench) |
| `investigacion\`, `pruebas\` | Capturas y comparativas antes/después, informes de etapas |
| `referencia-api\` | Extracto de los tipos de la API de mods (`claude-code`) |
| `datos-laboratorio\` | `medidas.json` (dock 64×35, banda 15 filas), `bench.json`, `bench_v1_2026-10-08.json` |
| `respaldos\` | Copias del mod antes de cada cambio grande |

## Estado a 2026-10-11 (el proceso completo está en `docs\CHAT_ACTUALIZACION_ANIMACION.md`)
- Todos los estados van a 5 fps (cada dibujo 200 ms; ciclo de 1,6 s con 8 fotogramas y 0,8 s con 4). Estado `baile` fuera de uso.
- Con arte nuevo (8 fotogramas, fondo transparente): pensando, responde, escribiendo, leyendo, terminado, hula, necesita, duerme. Con el arte original de 4 fotogramas: nueva, falla, para.
- Emi escritorio (ventana flotante) con su «frase de estado» (el cuadro junto a ella). Sonido de «listo» cada vez que Claude termina.
- Sin verificar en terminal real: correlación `tool.check` → `tool.call`; aspecto en el Windows Terminal del autor de los sprites 60x60 y 28x28.

## Notas
- Las preferencias de Emi (tamaño, sonido, avisos) viven en el almacén del motor (`$.store`) de cada PC; no viajan con la carpeta.
- Nunca guardar claves ni tokens aquí.
- Idea de la detección de fallos tomada de dgokcin/claude-pokemon-mod (sin licencia): solo la idea, código propio.
