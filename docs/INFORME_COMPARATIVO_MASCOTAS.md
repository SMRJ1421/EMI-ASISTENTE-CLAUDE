# Informe comparativo: mascotas animadas para Claude Code frente a Emilia

Fecha: 2026-10-08 (hora de Lima) · Claude Code 2.1.295 · Windows 11 · Mod `mascota` con panel acoplado (dock)

**Método:** solo lectura. Para cada repositorio consulté la API pública de GitHub (metadatos y árbol de archivos), su README y el código fuente relevante con `WebFetch`. **No descargué, instalé ni ejecuté nada de esos proyectos.** Las pruebas son mías, en el mod de laboratorio y en copias aparte.

**Etiquetas:** **[HECHO]** comprobado (fuente o prueba indicada) · **[DOC]** lo dice un README o el código de terceros, sin verificarlo yo · **[HIPÓTESIS]** razonamiento no comprobado · **[LÍMITE]** no se pudo comprobar.

> **No se ha modificado el mod principal `mascota`.** Todo lo nuevo está en `mascota-lab` (prototipos) y en archivos de informe. Antes de integrar nada espero tu autorización.

---

## 0. Punto de partida (estado actual de Emilia)

- **[HECHO]** Panel acoplado funcionando. Medido por el motor en tu terminal: dock `placement: dock`, **64 columnas × 35 filas**, `isFullscreen: true`; la banda sobre el prompt sigue limitada a 15 filas (`C:\Users\Admin0011\.claude\mascota-lab\medidas.json`).
- **[HECHO]** Con ese espacio el mod elige el sprite de **40×60 (30 filas)** más 4 de texto = 34 ≤ 35. Los sprites de 52×80 (40 filas) y 64×96 (48 filas) no caben en tu dock.
- **[HECHO]** 26/26 pruebas del mod principal siguen pasando tras estos experimentos.

---

## 1. Los cuatro repositorios: existencia, licencia y compatibilidad

Datos de `api.github.com/repos/<repo>` y de los archivos `LICENSE`, `package.json` y `plugin.json` de cada uno.

| | Repositorio | Existe | Licencia | Última actividad | Tecnología | Compatible con nuestra versión y Windows 11 |
|---|---|---|---|---|---|---|
| 1 | [dgokcin/claude-pokemon-mod](https://github.com/dgokcin/claude-pokemon-mod) | **Sí** (22 ★, creado 2026-10-03) | **Ninguna** (la API devuelve `license: null`; el README no declara licencia del código) | push 2026-10-09 | JavaScript; **mismo sistema de mods que el nuestro** (`hooks.json` → `register.js`, `ui.render`, `$.ui.blit`) | Pide **Claude Code ≥ 2.1.287** (nosotros 2.1.295 ✔). Terminal con truecolor (cita iTerm2, Ghostty, kitty, WezTerm); **Windows no se menciona**. También dibuja en la app de escritorio (SVG) |
| 2 | [TeXmeijin/claude-code-mascot-statusline](https://github.com/TeXmeijin/claude-code-mascot-statusline) | **Sí** (28 ★) | **MIT** (© meijin 2026), verificado en `LICENSE` | push 2026-04-26 | TypeScript; **línea de estado** (`statusLine`) + hooks clásicos; no es un mod de este tipo | Versión mínima no indicada. Averigua el ancho con `ps` y `stty` (entorno Unix) → **Windows dudoso** |
| 3 | [KebeliSamet0/clawd](https://github.com/KebeliSamet0/clawd) | **Sí** (21 ★) | Código **MIT**; **las ilustraciones tienen otra licencia** (`assets/LICENSE-clawd`: uso personal sí; copiar, modificar o distribuir el arte sin permiso escrito, no; sin uso comercial) | push 2026-05-18 | Electron ^30 (ventana flotante, bandeja del sistema), GIF/SVG, CSS | **Windows sí** (instalador `.exe`), pero **no se integra con Claude Code** (ver §3) |
| 4 | [octaviusp/claude-fx-plugin](https://github.com/octaviusp/claude-fx-plugin) | **Sí** (12 ★) | **Ambigua**: `plugin.json` dice `"license": "MIT"`, pero el repositorio **no contiene ningún archivo LICENSE** (GitHub no detecta licencia) | push 2026-01-16 | Python 3.9 + PyObjC (ventana transparente nativa de macOS), hooks clásicos (`python3 …/hook-handler.py`) | **Solo macOS** (README) → **incompatible con Windows 11** |

Notas sobre derechos **[HECHO]**:
- **Repo 1:** sin licencia el código queda con todos los derechos reservados: **se puede estudiar, no copiar**. Además sus sprites son copias de GIF de otros proyectos con derechos de Nintendo, Creatures, GAME FREAK y The Pokémon Company (lo dice su propio README). **No reutilizo ni código ni arte.** Todo lo que sigue de este repositorio son *ideas* reimplementadas por mí desde cero.
- **Repo 2:** MIT permitiría reutilizar código manteniendo el aviso de copyright. **No he copiado nada**; si en el futuro se copia código, hay que conservar «Copyright (c) 2026 meijin» y el texto MIT.
- **Repo 3:** la parte de código es MIT, pero el arte de Clawd no se puede reutilizar. Tampoco conviene (nuestro personaje es Emilia).
- **Repo 4:** con la ambigüedad de licencia y siendo solo macOS, no se toma nada de él.

---

## 2. Qué hace cada proyecto (lo que leí)

### 2.1 dgokcin/claude-pokemon-mod — el más cercano a nosotros

- **[DOC]** Pixel Pokémon «encima del prompt». Terminal: **medios bloques `▀`/`▄` con color verdadero** en un `Raster`; escritorio: **SVG a 4 px por píxel**. Igual que Emilia.
- **[HECHO, del código]** Anima con **`$.clock.every(50 ms)`** y los fotogramas se eligen **por tiempo transcurrido** (cada fotograma tiene su duración `ms`); en el terminal los envía con **`$.ui.blit`** y **omite el envío si las celdas no cambiaron**; si el motor lo deniega, vuelve a pedir un redibujo (como mucho cada 20 ticks). En el escritorio invalida el dibujo cada 100 ms.
- **[HECHO, del código]** Codificación de celdas: si las dos mitades tienen el mismo color emite **un espacio con ese color de fondo** (no `▀`); usa el color por defecto del terminal para lo transparente.
- **[HECHO, del código]** Detección de actividad: lee la propiedad `mode` del componente `Spinner` (pensando), `tool.call` (solo bucle principal), `tool.check` (guarda las **denegaciones** de permiso), `classic.PermissionRequest` y `classic.Notification` (necesita al usuario), `AskUserQuestion` y `ExitPlanMode`, `agent.spawn` (subagentes), `skill.prompt`, `prompt.edit` y `prompt.submit` (actividad / despertar). Un fallo cuenta **solo si** la herramienta devuelve error **y** el texto no coincide con un patrón de rechazo **y** no fue abortada por el usuario **y** no fue denegada por el permiso.
- **[DOC]** `hooks/zoom.js`: si no caben las filas, **reduce la escena** con un bloque por píxel de salida: gana el color con más votos, **desempate por el más oscuro**, y una regla que conserva las líneas finas que cruzan el bloque de borde a borde. Por debajo de 4 filas pasa a una línea de texto.
- **[DOC]** Datos: 151 × 4 GIF de 32×32 convertidos a `hooks/frames.js` (770 KB, texto con paleta de letras, sin compresión).
- **[DOC]** Limitaciones que declara: sin banda en VS Code ni móvil; algunas organizaciones bloquean `classic.*`; no habla de Windows.

### 2.2 TeXmeijin/claude-code-mascot-statusline

- **[DOC]** Mascota en la **línea de estado**. Se actualiza **solo cuando ocurre un hook** (el README lo llama «event-driven»): **no hay animación continua**. Dos modos de dibujo (`bg-space`: dos espacios con fondo de color; `half-block`).
- **[HECHO, del código]** Máquina de estados de 10 estados: cada evento sobrescribe el estado (sin prioridades ni caducidad; el último gana). `Notification` se interpreta por `notification_type` (`permission_prompt`, `elicitation_dialog`, `auth_success`, `idle_prompt`).
- **[HECHO, del código]** `visual-lint.ts`: mide el **desvío del centro de masa** y la **simetría izquierda/derecha** de los fotogramas (avisos si se pasan de umbrales). No comprueba recortes ni colores.
- **[DOC]** Formato de «packs» declarativo (`pack.json`/`pack.yaml`), utilidades de validación y vista previa, y una *skill* `create-mascot-pack`. Beta.
- **[DOC]** Para el ancho de terminal usa `ps` + `stty` y reconoce depender de comportamientos internos de Claude Code que pueden cambiar.

### 2.3 KebeliSamet0/clawd

- **[HECHO, del código]** Pequeña app **Electron** (ventana 128×128 transparente, sin marco, siempre encima, icono de bandeja, arranque con Windows).
- **[HECHO, del código]** **No hay ninguna integración con Claude Code**: `main.js` no usa hooks, ficheros, sockets ni procesos; `preload.js` solo expone mover la ventana, el tamaño de pantalla y listar GIF; `renderer/motion.js` hace aparecer la mascota **en un intervalo aleatorio de 60 a 120 segundos**. Es decir, **los estados «según tu actividad» que anuncia el README no se derivan de Claude Code** en el código que leí (**[LÍMITE]**: no leí `renderer/avatar.js` ni `index.html`).

### 2.4 octaviusp/claude-fx-plugin

- **[DOC]** Ventana transparente nativa de macOS junto al terminal; un PNG por estado (8 estados), efectos procedurales (respiración, balanceo, destellos, «Zzz»), burbujas de texto, sonidos por estado.
- **[HECHO, del código]** Cinco hooks clásicos (`SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`, `SessionEnd`) que lanzan `python3 hook-handler.py` y se comunican por socket con la ventana.
- **[DOC]** PNG de 1,6 a 4,4 MB por estado en sus temas.

---

## 3. Comparación con Emilia

| Aspecto | Emilia (hoy) | dgokcin | TeXmeijin | clawd | octaviusp |
|---|---|---|---|---|---|
| Detección automática de actividad | Hooks de turno, `tool.call`, `classic.Notification`; **un fallo incluye denegaciones y rechazos** | **La más completa** (§2.1) | 10 eventos clásicos, sin prioridad | **Ninguna** (aleatoria) | 5 hooks, sin detalle |
| Cambio de estados | 12 estados con duraciones y siesta | Estados + alertas con prioridad, siesta a los 5 min | El último evento gana | Aleatorio | 8 estados |
| Animación | 4 fotogramas a 4 (o 2) fps, un redibujo completo por tic | Por tiempo, `ms` por fotograma, `blit` | Solo cuando hay un evento | CSS/GIF | Procedural sobre PNG |
| Sprites PNG/GIF | PNG → datos de texto con paleta y tramos | GIF → texto con paleta | Packs JSON | GIF/SVG | PNG estáticos |
| Transparencia y color | Tarjeta lila + paleta de 88 colores | Transparente (color por defecto del terminal) | Fondo negro opcional | Ventana transparente | Ventana transparente |
| Resolución | De 13×20 a 64×96; panel 40×60 | 32×32 | 16 caracteres de ancho | 128×128 px | Cualquiera (se escala) |
| Adaptación al tamaño | Elige el mayor sprite que cabe (banda y panel) | Reduce por votación hasta 4 filas | Ancho con `ps/stty` | No aplica | `heightRatio`, `maxHeight` |
| Panel acoplado / ventana | **Panel acoplado** (dock) | Solo banda | Solo línea de estado | **Ventana flotante** | Ventana flotante (macOS) |
| Rendimiento/memoria | Datos 429 KB; 4 redibujos/s | Datos 770 KB; `blit`, omite lo que no cambia | Reejecuta todo en cada evento | Electron (sin cifras) | PNG de varios MB |
| Windows 11 | **Sí** | No mencionado | Dudoso | Sí (sin integración) | **No** |

---

## 4. Técnicas encontradas, procedencia y veredicto

Cada técnica la reimplementé yo; **ninguna copia código ajeno**.

| # | Técnica | Procede de | Problema de Emilia que toca | Qué probé | Resultado | Veredicto |
|---|---|---|---|---|---|---|
| T1 | **Animar con `$.ui.blit`** en vez de redibujar el panel entero | dgokcin (**[HECHO]** en su código) | Cada fotograma ejecuta hoy un redibujo completo (lectura de estado, árbol, validación) | `mascota-lab`: modo `atomo` (como el mod actual) frente a `blit`, reloj simulado 5 s, panel de 40×60 | **Control: 21 pasadas de dibujo. `blit`: 1 pasada y 20 envíos, 0 denegados** (8 fps: 1 pasada y 40 envíos) | **Adoptar**, sujeto a la medición real (ver §5). Los bytes enviados no bajan (cada envío lleva todas las celdas): lo que baja es el trabajo del motor |
| T2 | **Fotograma por tiempo transcurrido** y fps por perfil | dgokcin | Ritmo atado a los redibujos; imposible subir de 4 fps sin más redibujos | `animacion.ts` + pruebas; perfil «fluido» a 8 fps | Funciona (el índice depende solo del tiempo) | **Adoptar con T1.** Si 8 fps queda mejor **solo lo decides tú mirando** (`/emiproto fluido`): tenemos 4 fotogramas distintos por estado y a 8 fps el ciclo dura medio segundo |
| T3 | **Celda = espacio con fondo** cuando las dos mitades son iguales | dgokcin y TeXmeijin (modo `half-block`) | Menos glifos para pintar | `celdas2.ts`; comparación celda a celda con la codificación actual en los 240 fotogramas | **Idéntico en los 240** y solo un **33-47 %** de las celdas necesitan glifo `▀` (en 40×60: 36,6 %) | **Adoptar** (riesgo bajo). **[LÍMITE]** el beneficio de pintado en Windows Terminal no está medido |
| T4 | **Fallo real**: ignorar denegaciones, rechazos del usuario e interrupciones; registrar las denegaciones con `tool.check` | dgokcin | Emilia se asusta cuando **rechazas** un permiso o un hook bloquea una herramienta | Copia aparte del mod actual: dos pruebas de caracterización | **Confirmado el defecto:** ante `deny` y ante «The user doesn't want to proceed…» el mod actual muestra la frase de «falla». El prototipo (`deteccion.ts`) lo evita en todos los casos de su prueba (denegación de hook, permiso denegado, interrupción, rechazo por texto) y sigue contando un error real | **Adoptar.** **[LÍMITE]** el patrón de texto de rechazo es una heurística; la fuente fiable es `tool.check` |
| T5 | **«Te necesita»** también con `ExitPlanMode` (aprobar un plan) y `classic.PermissionRequest` | dgokcin | Hoy solo `AskUserQuestion` y `classic.Notification` | Función `pidePersona` con pruebas (`ExitPlanMode`: sí) | `PermissionRequest` **no está probado** en ejecución | **Adoptar `ExitPlanMode`** (trivial); `PermissionRequest` queda pendiente de probar |
| T6 | **Escribir en el cuadro despierta** a Emi (`prompt.edit`) | dgokcin | Emi puede seguir dormida mientras escribes | Función `despierta` con pruebas | No integrado en un hook real | Opcional, valor bajo |
| T7 | **Reducir por votación** (más votos, desempate por el más oscuro, conservar líneas finas) | dgokcin (`zoom.js`) | Llenar las 14 filas útiles de la banda | Comparación 18×28 de 6 métodos sobre 48 fotogramas (§4.1) | **No mejora lo nuestro** | **No adoptar** |
| T8 | **Medidas de calidad de sprite** (centro de masa y simetría) | TeXmeijin (`visual-lint.ts`) | Pruebas automáticas de alineación | Leído; no integrado | La simetría **no sirve**: Emi está dibujada de tres cuartos (no es simétrica). El desvío del centro de masa entre fotogramas sí es útil y ya lo cubre nuestra prueba de «suelo» | Posible mejora menor de las pruebas |
| T9 | **Formato de packs declarativo** (estados → fotogramas → duración) | TeXmeijin | Cuando lleguen los 20 estados y 8 fotogramas | Solo estudio | — | **Considerar más adelante**, no ahora |
| T10 | Sonidos por estado, efectos procedurales, burbujas | octaviusp | — | Estudio | Dependen de macOS (`NSSound`, PyObjC) | **No compatible**; ideas ya cubiertas (frases, sonidos de Windows) |

### 4.1 T7 en detalle: ¿ayuda reducir por votación a llenar las 14 filas de la banda?

Destino 18×28 (14 filas). Seis métodos, 48 fotogramas, imágenes en `C:\Users\Admin0011\Downloads\diagnostico-emi\investigacion\proto_zoom_*.png`:

| Método | Error frente al PNG (/255) | Apariencia a distancia (menor = mejor) | Contorno aislado | Ojos celestes (px) |
|---|---|---|---|---|
| A nearest desde 26×40 (nuestro método) | 46,8 | 11,96 | 11,0 % | 5,9 |
| B votos desde 26×40 | 62,2 | 26,46 | 1,3 % | 7,8 |
| C votos desde 52×80 | 52,5 | 16,94 | 11,0 % | 2,7 |
| D votos desde 64×96 | 51,3 | 15,79 | 12,1 % | 2,8 |
| E muestreo directo del PNG | 40,1 | **6,15** | 37,6 % | 4,6 |
| **G directo del PNG + regla de trazo oscuro** | 42,4 | 10,95 | **9,3 %** | 4,6 |

- **[HECHO]** La votación (B, C, D) **es peor que nuestro método actual (A)** en apariencia a distancia; B oscurece demasiado por el desempate hacia el color oscuro. **No se adopta.**
- **[HECHO]** La mejor opción es **G, que sale de nuestro propio pipeline**: sprite de **18×28 (14 filas)** generado directamente del PNG con la regla de trazo. Se ve nítido (ojos celestes, contorno continuo) y es **un 40 % más alto que el mini actual** (14 frente a 10 filas).
- **[LÍMITE]** Es una mejora **solo para la banda** (que ya no usas si trabajas con el panel) y mi métrica de apariencia favorece a E por construcción (comparte el muestreo con la referencia). La decisión entre G y el mini actual es visual.

---

## 5. Lo que implementé en el laboratorio (`mascota-lab`)

Ruta: `C:\Users\Admin0011\.claude\dev-mods\da5e8c78-c252-4d1c-9f43-47016e40a9d5\mascota-lab\`

| Archivo | Contenido |
|---|---|
| `hooks\celdas2.ts` | T3: codificación de celdas con espacios y lectura de vuelta para comprobar que no se pierde nada |
| `hooks\animacion.ts` | T2: fotograma por tiempo y perfiles `actual` (4/2 fps) y `fluido` (8/4 fps) |
| `hooks\deteccion.ts` | T4, T5, T6: fallo real, patrón de rechazo, herramientas que piden algo a la persona, despertar |
| `hooks\register.tsx` | Comando `/emiproto atomo\|blit\|fluido\|bench\|off` y panel de prototipo (`requestId: emiproto`) con contadores; comparación automática `bench` |
| `tests\proto.test.ts` | Pruebas de los prototipos (incluye el comparativo con reloj simulado) |

**Resultados de pruebas [HECHO]:** laboratorio **15/15**, validación correcta, TypeScript sin errores; mod principal **26/26** (sin cambios).

**Dos descubrimientos técnicos [HECHO]:** (a) el motor **solo admite un módulo de hooks por plugin** y **no permite pasar `$` a otro archivo ni registrar dos `session.start` sin filtro en el mismo módulo**; por eso el prototipo vive dentro de `register.tsx`; (b) con un reloj simulado `mock.clock` se pueden contar pasadas de dibujo de forma reproducible.

### Medición real en tu sesión (pendiente de lectura)

Al recargarse el laboratorio (al terminar este turno) se ejecuta **una sola vez** una comparación de unos 40 segundos con un panel acoplado de prueba: A control (redibujo cada 250 ms), B `blit` a 4 fps y C `blit` a 8 fps. Guarda en `C:\Users\Admin0011\.claude\mascota-lab\bench.json` el número de pasadas de dibujo, el tiempo dentro del dibujo, los envíos, los saltados y los denegados. **[LÍMITE]** Mide trabajo dentro del hook, no CPU del terminal ni parpadeo: eso solo lo puedes valorar tú mirando.

---

## 6. Qué no es compatible o no conviene

- **clawd:** ventana flotante de Electron (pesada), **sin conexión con Claude Code** (movimiento aleatorio) y arte con licencia restrictiva. No sirve ni como código ni como arte.
- **octaviusp:** macOS únicamente, licencia ambigua, sprites de varios MB.
- **TeXmeijin (línea de estado):** no puede animar (se refresca solo con eventos) y depende de `ps`/`stty`. Sus ideas (estados, formato de packs) sí son aprovechables.
- **dgokcin:** sin licencia: **no se puede copiar nada** (ni código ni sprites); todo lo adoptado son ideas reimplementadas.
- **Reducción por votación (T7):** probada y descartada.

---

## 7. Limitaciones pendientes

1. La **mejora real de rendimiento y fluidez** con `blit` no está confirmada en tu terminal (la medición automática está armada; lo visual lo decides tú).
2. **`classic.PermissionRequest`** y el **despertar con `prompt.edit`** no están probados en ejecución.
3. El **patrón de texto de rechazo** (T4) es una heurística; la comprobación robusta es `tool.check`.
4. El sprite de 18×28 para la banda (G) está comparado en imágenes, **no generado como datos** ni integrado.
5. Los beneficios de T3 (menos glifos) en Windows Terminal **no están medidos**.
6. No he leído `renderer/avatar.js` de clawd, ni el final de `register.js` de dgokcin más allá de lo resumido.

---

## 8. Propuesta para tu autorización

Si me autorizas, integraría en el mod principal **solo lo demostrado**, en este orden y probando cada paso:

1. **T4** (fallo real) y **T5** (`ExitPlanMode`): corrigen un comportamiento comprobado.
2. **T3** (celdas con espacio): idéntico a la vista, menos glifos.
3. **T1 + T2** (`blit` y tiempo), **solo si** `bench.json` confirma la mejora; el perfil de 8 fps quedaría como opción (`/emi fluido`) para que lo veas.
4. Opcional: el sprite de 14 filas para la banda (G).

Seguiría sin tocar nada hasta tu «adelante».

---

## 9. Fuentes

- https://github.com/dgokcin/claude-pokemon-mod (README, `hooks/register.js`, `hooks/zoom.js`, `scripts/build-frames.mjs`, API del repositorio)
- https://github.com/TeXmeijin/claude-code-mascot-statusline (README, `LICENSE`, `src/lib/state-machine.ts`, `visual-lint.ts`, `renderer.ts`)
- https://github.com/KebeliSamet0/clawd (README, `main.js`, `preload.js`, `renderer/motion.js`, `package.json`, `assets/LICENSE-clawd`)
- https://github.com/octaviusp/claude-fx-plugin (README, `hooks/hooks.json`, `.claude-plugin/plugin.json`, árbol de archivos)
- API pública de GitHub (`api.github.com/repos/<repo>`) para licencia, fechas y árbol de archivos.

Archivos de esta investigación: `C:\Users\Admin0011\Downloads\diagnostico-emi\investigacion\` (comparativas de reescalado), `...\scripts\` (`proto_zoom.py`, `celdas_stats.py`, `caracterizacion_deny.test.ts`).

---

## 10. Resultados de bench.json (medición real, 12 s por fase, panel acoplado, sprite 40×60)

Datos: `C:\Users\Admin0011\.claude\mascota-lab\bench_v1_2026-10-08.json`. Tiempos medidos con el reloj de pared **dentro de los hooks** (incluyen esperas; no son CPU).

| Fase | Pasadas de dibujo | Tiempo medio por pasada | Envíos `blit` | Tiempo medio por envío | Saltados | Denegados | Bytes de celdas |
|---|---|---|---|---|---|---|---|
| **A** control: redibujo cada 250 ms (como el mod) | 50 | 0,8 ms | 0 | — | 0 | 0 | 960 KB |
| **B** `blit` a 4 fps | **54** | 17,2 ms | 41 | 3,1 ms | 6 | 0 | 1 037 KB + 787 KB |
| **C** `blit` a 8 fps | **30** | 11,9 ms | 86 | 3,0 ms | 7 | 0 | 358 KB + 1 629 KB |

Lectura **[HECHO]**:
1. **La hipótesis de la prueba simulada no se cumple en el motor real.** Con reloj simulado `blit` dejaba **1** pasada de dibujo; en tu sesión real el dibujo se siguió ejecutando **54 veces** (B) y **30** (C), casi igual que el control (50). `blit` **no eliminó** las pasadas de dibujo.
2. Cada envío `blit` costó **~3 ms** de reloj de pared, frente a **0,8 ms** de una pasada del control. Con `blit` el tiempo total dentro de nuestros hooks fue **15-26 veces mayor** que en el control (1 055 ms y 615 ms frente a 40 ms en 12 s). **[LÍMITE]** Es reloj de pared con esperas intercaladas: no permite concluir uso de CPU, pero **no hay ninguna señal de ahorro**.
3. Ningún envío fue denegado: `blit` funciona; simplemente no aporta aquí.
4. Los bytes **no bajan**: cada `blit` lleva todas las celdas (≈19 KB en 40×60).
5. Fotogramas efectivamente entregados: B ≈ 3,4/s, C ≈ 7,2/s.

**Pregunta abierta:** por qué el dibujo se sigue ejecutando con `blit`. No lo sé. La segunda medición, ya armada, añade un contador de «pasadas justo después de un blit» para saber si el propio `blit` provoca el redibujo.

### Recomendación sobre el punto 3 (no integrado)

- **No integrar `blit`**: en la medición real no redujo las pasadas de dibujo y cada envío cuesta más que una pasada.
- **4 fps frente a 8 fps:** entre las dos variantes con `blit`, C entrega el doble de fotogramas con menos tiempo total en hooks que B (615 frente a 1 055 ms), pero ambas son peores que el control. **Mi recomendación es mantener el ritmo actual (4 fps, redibujo normal).**
- **Si quieres más fluidez**, la opción a probar es **8 fps con el redibujo normal** (tick de 125 ms y fotograma elegido por tiempo, sin `blit`): una pasada del control cuesta ~0,8 ms, así que 8 por segundo serían ~6 ms/s. **Está medido solo en simulación**; la segunda medición real (fase D) lo confirma. Para valorar el aspecto: `/emiproto atomo8` frente a `/emiproto atomo`.
