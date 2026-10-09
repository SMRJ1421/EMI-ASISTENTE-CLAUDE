# Emilia (Emi) — mascota pixel para Claude Code

Mod de Claude Code (hooks en TS/TSX) con una mascota animada: 12 estados × 4 fotogramas, panel lateral acoplado (Dock) o banda sobre el prompt. Creado con Claude Code 2.1.294 / 2.1.295 en Windows 11.

## Usarlo en otra PC
1. Requisitos: Claude Code con soporte de mods (≥ 2.1.294) y Windows (los avisos y sonidos usan PowerShell).
2. Copia esta carpeta completa.
3. Carga el mod: `claude --plugin-dir "<ruta>\emilia-mascota\mod"` (o copia `mod\` dentro de tu carpeta `dev-mods` con hot reload).
4. Dentro de Claude: `/emi panel` (panel acoplado), `/emi banda`, `/emi probar` (enseña los 12 estados). Resto de comandos: grande, normal, mini, compacta, oculta, sonido, silencio, avisos, sin-avisos.
5. Comprobar: `claude plugin validate mod` y `claude plugin test mod` (esperado: 34 pass). El laboratorio: `claude plugin test laboratorio` (15 pass).

## Carpetas
| Carpeta | Contenido |
|---|---|
| `mod\` | **El mod principal** (lo que se instala). `hooks\register.tsx` es el módulo; `sprites.ts` los 5 tamaños de sprites; `dibujo.ts` celdas Raster/SVG; `deteccion.ts` fallo real; `estados.ts` frases y estados; `tests\` |
| `laboratorio\` | Mod aparte `mascota-lab` con prototipos y bancos (`/emilab`, `/emiproto`). No es necesario para usar a Emi |
| `arte\` | PNG originales: hoja de 12 estados, hoja de animación y `animacion.png` (20 estados nuevos, **aún no integrados**) |
| `scripts\pipeline-sprites\` | Python que convierte los PNG en `sprites.ts` (`emi_lib2.py`, `gen_ts.py`, `regen2.py`…). Revisa rutas: apuntan a `C:\Users\Admin0011\Downloads\…`; cámbialas a `..\..\arte\` |
| `scripts\diagnostico\` | Scripts de comparación y diagnóstico de fidelidad |
| `scripts\tsconfig\` | tsconfig usados para comprobar TypeScript (`npx -y -p typescript@5.6 tsc -p <carpeta>`) |
| `docs\` | `INFORME_TECNICO_EMILIA.md` (secciones 1–13) e `INFORME_COMPARATIVO_MASCOTAS.md` (4 repos estudiados, licencias, bench) |
| `investigacion\`, `pruebas\` | Capturas y comparativas antes/después, informes de etapas |
| `referencia-api\` | Extracto de los tipos de la API de mods (`claude-code`) |
| `datos-laboratorio\` | `medidas.json` (dock 64×35, banda 15 filas), `bench.json`, `bench_v1_2026-10-08.json` |
| `respaldos\` | Copias del mod antes de cada cambio grande |

## Estado a 2026-10-08
- Hecho: sprites fieles a los PNG (5 tamaños), panel Dock con tamaño adaptativo, fallo real (denegaciones/interrupciones no asustan), `ExitPlanMode` → «necesita», celdas Raster con espacio (63 % menos glifos, imagen idéntica).
- Pendiente de tu decisión: 8 fps con redibujo normal (`/emiproto atomo8`); `blit` descartado por el banco real.
- Fuera de alcance por ahora: los 20 estados nuevos / 8 fotogramas y el sprite de banda 18×28.
- Sin verificar en terminal real: correlación `tool.check` → `tool.call`; aspecto de las celdas nuevas en tu Windows Terminal.

## Notas
- Las preferencias de Emi (tamaño, sonido, avisos) viven en el almacén del motor (`$.store`) de cada PC; no viajan con la carpeta.
- Nunca guardar claves ni tokens aquí.
- Idea de la detección de fallos tomada de dgokcin/claude-pokemon-mod (sin licencia): solo la idea, código propio.
