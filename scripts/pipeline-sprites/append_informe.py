ruta = r"C:\Users\Admin0011\Proyectos\mods-claude\emilia-mascota\docs\INFORME_TECNICO_EMILIA.md"
texto = open(ruta, encoding="utf-8").read()
assert "## 12. Actualización" not in texto

anexo = r'''

---

## 12. Actualización (implementación posterior al informe)

> Las secciones 2, 5 y 6 describen la versión **anterior** a esta actualización (sprites de 26×40 y 13×20 en la banda, sin panel). Esta sección la sustituye.

### 12.1 Qué se implementó

| Problema | Solución | Estado |
|---|---|---|
| La banda `AbovePrompt` solo da 15 filas y el sprite grande (20) se recortaba | **Elegir el sprite según `e.props.maxRows`**: el mayor de {S 13×20 (10 filas), N 26×40 (20), M 40×60 (30), L 52×80 (40), XL 64×96 (48)} que quepa; si no cabe ninguno, línea compacta. En tu terminal: S | HECHO + probado con el kit (`mascota.test.ts`) |
| No se podía ver a Emi grande | **Panel acoplado** (`Pane`, `/emi panel`): usa `e.props.scroll.bodyRows` y `bodyColumns` del panel y elige el mayor sprite con el texto debajo o al lado (`planPanel`) | Implementado y probado en el kit; **la altura real del dock en tu terminal está sin medir** (ver 12.5) |
| Sprites de 40×60, 52×80 y 64×96 | Generados **desde el PNG original** (`scripts\hires.py`), paleta propia por tamaño con semillas por tono, limpieza de píxeles grises sueltos (7 en total), compresión por tramos | HECHO; ida y vuelta TS ↔ datos: 240 fotogramas, 0 diferencias |
| Escritorio (SVG) | Sprites de más resolución con escala entera ×2: `grande` XL 64×96 (128×192 px), `normal` L 52×80 (104×160), `mini` N 26×40 (52×80) | Árbol válido en el kit; **no visto en ventana real** |
| Estabilidad | Panel no colocado → se cierra solo y Emi sigue en la banda; si la persona cierra el panel, vuelve a la banda y se guarda; una recarga lo reabre si el modo guardado es `panel` | HECHO (pruebas) |

Decisión de diseño: **no se abre ningún panel por sorpresa**. Por defecto Emi sigue en la banda (adaptada al espacio); el panel solo se abre con `/emi panel`.

### 12.2 Cambios en el código (referencias)

- `mascota\hooks\dibujo.ts` (nuevo, ~170 líneas): `elegirTam`, `planPanel`, `descomprimir`, `celdas(tam, filas)`, `dibujoSvg(tam, filas)`, `medidas`.
- `mascota\hooks\sprites.ts` (nuevo, 429 307 B): `TAMANOS` con 5 tamaños × 12 estados × 4 fotogramas, paleta por tamaño, tramos comprimidos (`§` + longitud + color).
- `mascota\hooks\register.tsx`: `topeDe`, `abrirPanel`, `aBanda`, `guardarAjustes`; hook `ui.close`; hook `ui.render` de `Pane` (`requestId: 'emi'`); banda adaptativa; comandos `panel` y `banda`; ajuste `modo` (`banda`|`panel`) y estado `panel`.
- `mascota\types\index.d.ts`: `MascotaModo`, `modo` en `MascotaAjustes`, `panel` en el estado.
- `mascota-lab\hooks\register.tsx`: `/emilab 13|26|40|52|64`, `/emilab pane`, medidas en `C:\Users\Admin0011\Proyectos\mods-claude\emilia-mascota\datos-laboratorio\medidas.json` (banda: `maxRows`, `bodyColumns`, `isFullscreen`; panel: `placement`, `bodyColumns`, `bodyRows`). Medición automática de una sola vez (marca `auto.txt`).
- Sin cambios: los 12 estados y sus 4 fotogramas, `estados.ts`, los avisos y sonidos de Windows, los indicadores de otras conversaciones, `turn.*`, `tool.call` y `classic.Notification`.

### 12.3 Pruebas (HECHO)

| Prueba | Resultado |
|---|---|
| `claude plugin validate mascota` / `mascota-lab` | Pasan (solo la advertencia del campo `author`) |
| `claude plugin test mascota` | **26 / 26** (datos, fidelidad, elección de tamaño, rendimiento, banda, estados, panel, comandos) |
| `claude plugin test mascota-lab` | **8 / 8** |
| `tsc` (TypeScript 5.6) en ambos | Sin errores |
| 240 fotogramas (12 × 4 × 5) | Todos rectangulares, con colores válidos, cuerpo completo (> 15 % de la superficie opaca) y suelo estable entre los 4 fotogramas |
| Rendimiento (en el entorno de pruebas) | Convertir los 240 fotogramas a celdas: < 5 s; 40 redibujos de los 5 tamaños ya convertidos: < 0,5 s |

Datos medidos al generar: error de cuantización 4,3-5,3/255; cobertura del primer plano 96,3 % (nativo) a 98,7 % (64×96); 0 píxeles compartidos entre fotogramas vecinos.

### 12.4 Cómo elige el tamaño (resumen)

`ajustes.tamano` fija el tope: `grande` → hasta XL, `normal` → hasta L (por defecto), `mini` → S. El tamaño real es el mayor que quepa en las filas y columnas que da el motor (banda: `maxRows − 1` filas; panel: `scroll.bodyRows`). Con tu terminal (156×41, banda de 15 filas): banda → S (10 filas) con la pista «más grande: /emi panel».

### 12.5 Limitaciones y comprobaciones pendientes (LÍMITE / HIPÓTESIS)

1. **Altura útil real del dock:** no la he medido. `PaneOpenArgs.columns` dice que el dock se abre «de suelo a techo», pero `scroll.bodyRows` descuenta al menos una fila de la marca de cierre. Con ~39-40 filas útiles: M (30 filas) cabe con texto debajo; L (40) solo cabría con el texto al lado y si hay 40 filas. La medición automática queda armada en `mascota-lab`.
2. **No se ha visto en un Windows Terminal real:** las imágenes `simulacion_banda.png` y `simulacion_panel.png` son **simulaciones**, no capturas.
3. **Escritorio:** SVG sin verificar visualmente.
4. **Compatibilidad con otras bandas** (termómetro, objetivo): la banda sigue componiéndose con `next(e)`, pero no se probó con ellos instalados.

### 12.6 Comandos

`/emi` (estado y ayuda) · `/emi grande|normal|mini|compacta|oculta` · **`/emi panel`** · **`/emi banda`** · `/emi sonido|silencio` · `/emi avisos|sin-avisos` · `/emi probar` · `/emilab` (laboratorio, no hace nada hasta que se usa).

### 12.7 Respaldos

- `C:\Users\Admin0011\Proyectos\mods-claude\emilia-mascota\respaldos\mascota-2026-10-08-antes-de-fidelidad\` (antes de la corrección de fidelidad)
- `C:\Users\Admin0011\Proyectos\mods-claude\emilia-mascota\respaldos\mascota-2026-10-08-1954-antes-del-panel\` (justo antes de esta actualización, versión de 26×40)
- `C:\Users\Admin0011\Proyectos\mods-claude\emilia-mascota\respaldos\mascota-lab-2026-10-08-1954-antes-del-panel\`

Para volver atrás: copiar el contenido de la carpeta de respaldo sobre `...\dev-mods\...\mascota\`.

### 12.8 Imágenes de esta actualización

`C:\Users\Admin0011\Proyectos\mods-claude\emilia-mascota\pruebas\final-mod\`: `tamanos_*.png` (los 5 tamaños por estado, a partir de los datos finales), `simulacion_banda.png` y `simulacion_panel.png` (simulaciones), `informe_datos_finales.txt`.
'''
open(ruta, "w", encoding="utf-8").write(texto.rstrip("\n") + "\n" + anexo)
print("anexo añadido:", len(anexo), "caracteres")
