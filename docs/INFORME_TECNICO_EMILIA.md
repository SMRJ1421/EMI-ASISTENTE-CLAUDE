# Informe técnico: Mod «Emilia / Emi» para Claude Code (resolución y tamaño en Windows Terminal)

Fecha: 2026-10-08 · Claude Code 2.1.295 (tipos de la API escritos por 2.1.294) · Windows 11 · idioma de trabajo: español

**Para quién es:** otro asistente de IA (ChatGPT) que debe proponer una solución definitiva al problema de tamaño y resolución.
**Cómo leerlo:** cada afirmación lleva una etiqueta.

| Etiqueta | Significado |
|---|---|
| **[HECHO]** | Comprobado con una prueba, una medición o el código; se indica dónde verificarlo |
| **[DOC]** | Lo dice la documentación de tipos de la API (`claude-code/index.d.ts`), con línea; no lo he observado en la práctica |
| **[HIPÓTESIS]** | Razonamiento o conocimiento general, **no comprobado** en este equipo |
| **[LÍMITE]** | Cosa que no pude comprobar o que no se puede hacer con lo disponible |

No hay claves, tokens ni datos privados en este documento. Las rutas contienen el nombre de usuario local de Windows porque son necesarias para verificar.

---

## 0. Resumen ejecutivo

1. **[HECHO] El límite real no es el Mod, ni Raster, ni la resolución de los sprites: es la altura que el motor de Claude Code concede a la banda `AbovePrompt`.** Medido en tu terminal con el Mod de laboratorio: ventana de **156 × 41 celdas**, banda de **151 columnas × 15 filas máximo** (§3).
2. **[HECHO] El sprite actual (26 × 40 px → 20 filas de terminal) ya excede esas 15 filas.** `/emilab` marcó «NO cabe entero» para los cuatro tamaños (26×40, 40×60, 52×80, 64×96). **[DOC]** Cuando el árbol es más alto que `maxRows`, el motor lo desplaza en una ventana (`scroll.bodyRows`) y la banda lleva una fila «n more»: es decir, Emi se ve recortada. **[LÍMITE]** No tengo una captura de esa situación real.
3. **[HECHO] Los sprites generados desde los PNG son fieles.** Cobertura 96,3 %, sin contaminación de sprites vecinos, rejilla real del dibujo medida (4,75 px). A 52×80 y 64×96 se recupera más detalle (§4, §8).
4. **[DOC] El límite de filas depende del layout de pantalla completa:** en pantalla completa el hueco se limita a la mitad de las filas del terminal (incluido el cuadro de texto); fuera de ella, a la altura del terminal. **No hay en la API un ajuste para subirlo.** Lo que sí está documentado (y **no he probado**): el layout de pantalla principal (`CLAUDE_CODE_NO_FLICKER=0`), un panel acoplado (`Pane` en `dock`, «de suelo a techo»), más filas de terminal, o la superficie de escritorio con SVG (§6, §9).
5. **Recomendación corta (§10):** (a) elegir el sprite según `e.props.maxRows`, (b) probar un `Pane` acoplado con el Mod de laboratorio, que es lo único documentado que escapa del tope de la banda sin cambiar la configuración global.

---

## 1. Entorno

| Dato | Valor | Etiqueta |
|---|---|---|
| Claude Code | 2.1.295 (`claude --version`) | HECHO |
| Tipos de la API | «Written by Claude Code 2.1.294» (línea 1 del `.d.ts`) | HECHO |
| Sistema | Windows 11, PowerShell | HECHO |
| Terminal | «Windows Terminal» según el usuario | **HECHO (declarado por el usuario)**; no pude comprobarlo: en mi shell `WT_SESSION` y `TERM_PROGRAM` están vacíos |
| `CLAUDE_CODE_NO_FLICKER` | no definida en mi shell ni en `~/.claude/settings.json` (búsqueda de «NO_FLICKER», «tui», «fullscreen») | HECHO, pero **[LÍMITE]**: es el entorno de mi shell, no necesariamente el de tu sesión |
| Medida del terminal real | `superficie terminal`, `bodyColumns 151`, `maxRows 15`, ventana `156 × 41` | HECHO (salida de `/emilab`, §3) |
| Celda de terminal | ≈ 8,7 × 17,3 px (relación 1 : 2,0) | **HIPÓTESIS**: estimada de una captura antigua del terminal (`C:\Users\Admin0011\OneDrive\Imágenes\Screenshots\Captura de pantalla 2026-10-08 182953.png`) con otro sprite; no re-medida |

---

## 2. Arquitectura actual del Mod

Carpeta raíz de los Mods en desarrollo: `C:\Users\Admin0011\.claude\dev-mods\da5e8c78-c252-4d1c-9f43-47016e40a9d5\`
Copia de seguridad anterior a la corrección de fidelidad: `C:\Users\Admin0011\.claude\dev-mods-backup\mascota-2026-10-08-antes-de-fidelidad\`

### 2.1 Archivos (HECHO, medidos con PowerShell)

| Ruta (bajo `mascota\`) | Bytes | Líneas | Función |
|---|---|---|---|
| `.claude-plugin\plugin.json` | 349 | 6 | Manifiesto (`name: mascota`, `types: ./types/index.d.ts`) |
| `hooks\hooks.json` | 34 | 1 | `{ "modules": ["./register.tsx"] }` |
| `hooks\register.tsx` | 16 310 | 403 | Todos los hooks, el comando `/emi` y la barra |
| `hooks\dibujo.ts` | 3 795 | 89 | Pose, fotograma, conversión a celdas Raster y a SVG (funciones puras) |
| `hooks\estados.ts` | 5 071 | 139 | Frases, colores, caritas, qué estado le toca a cada herramienta |
| `hooks\sprites.ts` | 67 713 | 58 | Datos generados: paleta de 88 colores y 12 estados × 4 fotogramas × 2 tamaños (L 26×40, X 13×20) |
| `types\index.d.ts` | 778 | 27 | Contrato de `$.state` (`mascota.animo/tic/ajustes/otras`) |
| `tests\mascota.test.ts` | 7 891 | 160 | 14 pruebas |
| `.claude-plugin\types\claude-code\index.d.ts` | 614 113 | 15 202 | API completa escrita por el motor (la fuente de las referencias `:línea` de este informe) |

Mod de laboratorio, **separado** (`mascota-lab\`): `hooks\register.tsx` (154 líneas), `hooks\datos.ts` (173 317 B; sprites a 26/40/52/64 de 3 estados), `tests\lab.test.ts` (48 líneas), `types\index.d.ts`.

### 2.2 Tecnologías

TypeScript/TSX compilado por el motor (JSX contra el global `h`; no hay DOM ni Node); `claude-code` solo como módulo de tipos. Dibujo con `Raster` (terminal) y `Svg` (escritorio). Estado en `atom`/`read`/`update`. Temporizador `$.clock.every(250 ms)`. Pruebas con `claude plugin test`.

### 2.3 Hooks y comandos (HECHO: salida de `claude plugin validate mascota`)

| Hook | Línea en `register.tsx` | Qué hace |
|---|---|---|
| `session.start` | ~178 | Registra `/emi`, lee ajustes, arranca el latido de 250 ms |
| `session.end` | — | Marca la sesión cerrada; `/clear` → estado «nueva» |
| `turn.start` / `turn.complete` | — | «pensando» → «terminado» o «baile» (>120 s o ≥25 herramientas); avisos de Windows |
| `turn.step` (generador) | 234 | Solo observa chunks `text`/`thinking`; no modifica la respuesta |
| `tool.call` | 255 | Estado por herramienta (leyendo/escribiendo/necesita); `isError` o `deny` → «falla» |
| `classic.Notification` | 268 | «Te necesita» (permiso o pregunta) |
| `command.run {command=emi}` | 301 | `/emi grande\|normal\|mini\|compacta\|oculta\|sonido\|silencio\|avisos\|sin-avisos\|probar` |
| `ui.render {component=AbovePrompt}` | 333 | Dibuja la banda (única superficie de dibujo del Mod) |

El Mod **no llama al modelo** ni añade contexto (la lista de llamadas del validador no incluye `$.model`).

### 2.4 Flujo del dibujo (HECHO, leído del código)

`latir()` cada 250 ms → `update(tic)` → el hook `ui.render` suscrito a `tic` redibuja → `fotograma(estado, tam, tic)` elige 1 de 4 fotogramas → `celdas(filas)` (terminal) o `dibujoSvg(filas)` (escritorio) → `<Raster>` o `<Svg>` dentro de un `<Box flexDirection="row">` con el texto de Emi a la derecha.

Mapeo de tamaños (`register.tsx:378` y `:410-411`): terminal `mini` → sprite X (13×20 px = 10 filas); `grande` y `normal` → sprite L (26×40 px = 20 filas). Escritorio: siempre L en SVG con escala ×4 (`grande`), ×3 (`normal`), ×2 (`mini`).

---

## 3. Limitación real: por qué 156 × 41 celdas solo da 15 filas

### 3.1 Medición (HECHO)

Salida literal de `/emilab` en tu terminal (Mod de laboratorio, `mascota-lab\hooks\register.tsx`, que guarda `e.props.maxRows`, `e.props.bodyColumns` y `e.viewport` en cada render):

```
Medido por el motor en tu terminal: superficie terminal, banda de 151 columnas por 15 filas como máximo, ventana de 156 x 41.
  26: sprite 26 x 40 -> 26 columnas x 20 filas: NO cabe entero
  40: sprite 40 x 60 -> 40 columnas x 30 filas: NO cabe entero
  52: sprite 52 x 80 -> 52 columnas x 40 filas: NO cabe entero
  64: sprite 64 x 96 -> 64 columnas x 48 filas: NO cabe entero
```

### 3.2 Explicación y quién impone el límite

- **Columnas: [DOC + HECHO coherente].** `bodyColumns` es «su columna menos las cinco del motor al extremo derecho» (`index.d.ts:10212-10219`); 156 − 5 = 151. ✔
- **Filas: [DOC].** `maxRows` es «las filas que puede ocupar la banda: en pantalla completa, lo que le queda al hueco inferior sobre el prompt; si no, la altura del terminal. **Ese hueco está limitado a la mitad de las filas del terminal, contando las del prompt.**» (`index.d.ts:10200-10209`). Un árbol de como máximo `maxRows` filas se muestra entero; uno más alto «se desplaza en una ventana de `scroll.bodyRows`», que es `maxRows` menos la fila «n more» (`index.d.ts:10222-10226`).
- **Cálculo [HIPÓTESIS coherente con el dato]:** mitad de 41 filas = 20 (si se redondea hacia abajo); 20 − 15 = 5 filas reservadas para el cuadro de texto y sus bordes/pies. Es **un solo dato**: no sé el redondeo ni cuántas filas reserva exactamente el prompt. Extrapolación lineal (no probada): `maxRows ≈ floor(filas_terminal / 2) − 5`.
- **Qué componente impone el tope: [DOC]** el layout de pantalla completa (alternate screen) de la superficie `terminal` de Claude Code (Ink). **No** es el Mod, **no** es el elemento `Raster` (su límite documentado es 512 × 256, `index.d.ts:9195-9202`) y **no** es Windows Terminal.
- **¿Estás en pantalla completa? [HIPÓTESIS fuerte, no leí el flag].** `RenderViewport.isFullscreen` lo dice (`index.d.ts:10350`), pero el Mod de laboratorio no lo imprime. Indicios: `maxRows = 15` ≪ 41 es incompatible con «si no, la altura del terminal»; y `CLAUDE_CODE_NO_FLICKER` no está definida en mi entorno (el valor `0` es lo que da el layout de pantalla principal, `index.d.ts:1753-1754`).
- **¿Es configurable?**
  - **[DOC]** El layout de pantalla principal existe con `CLAUDE_CODE_NO_FLICKER=0` (`index.d.ts:1753-1754`, que añade «tmux por defecto»). Allí `maxRows` sería «la altura del terminal». **[LÍMITE] No lo probé** (cambiaría la configuración global y los efectos secundarios sobre el resto de la interfaz no están documentados).
  - **[DOC]** Todas las props de la banda son «solo lectura»: el Mod no puede pedir más filas (`index.d.ts:10198, 10210, 10219`).
  - **[HECHO]** No existe en la API ningún ajuste para cambiar la mitad del tope (búsqueda de `maxRows`, `fullscreen`, `isFullscreen`, `NO_FLICKER` en el `.d.ts` y en `reference.md`).
  - Aumentar las filas del terminal sí lo sube (consecuencia directa del tope proporcional). Con la extrapolación anterior, 20 filas de banda necesitarían ≈ 50 filas de terminal, 30 ≈ 70, 40 ≈ 90, 48 ≈ 106. **[HIPÓTESIS]**

### 3.3 Consecuencia práctica ya presente

Tamaños del Mod actual frente al tope medido (15 filas):

| `/emi …` | Filas que ocupa | ¿Cabe en 15? |
|---|---|---|
| `grande` / `normal` | 20 | **No** (HECHO por `/emilab 26`) |
| `mini` | 10 | Sí (cálculo; no lo medí con captura) |
| `compacta` | 1 | Sí |

**[LÍMITE]** Falta una captura de `/emi grande` con el tope de 15 filas para ver exactamente cómo se recorta o se desplaza.

---

## 4. Resoluciones probadas (26×40, 40×60, 52×80, 64×96)

Todas generadas **desde el PNG original** (no desde los sprites reducidos), con el mismo recorte, la misma rejilla (4,75 px), el mismo anclaje y paso de muestreo igual en X e Y (píxel cuadrado). Script: `C:\Users\Admin0011\Downloads\diagnostico-emi\scripts\hires.py`. Informe numérico: `...\diagnostico-emi\alta-resolucion\informe_alta_resolucion.txt`.

| | **Actual 26×40** | 40×60 | 52×80 | 64×96 |
|---|---|---|---|---|
| Muestras por píxel del dibujo (4,75 px) | 1,0 | 1,5 | **2,0 exacto** | 2,4 |
| Celdas de terminal | 26 col × 20 filas | 40 × 30 | 52 × 40 | 64 × 48 |
| Cobertura del primer plano (48 fotogramas) | 96,3 % | 97,4 % | 98,6 % | 98,7 % |
| Error medio frente al PNG (/255) | ≈ 30 (otra rejilla) | 27,3 | 20,0 | 17,9 |
| Muestras que difieren del píxel nativo | 0 % | 31,8 % | 26,8 % | 29,1 % |
| Pares de color (arriba, abajo) por fotograma, máximo | — | 482 | 658 | 812 |
| Límite del Raster de pares | 1024 | 1024 | 1024 | 1024 |
| Datos por redibujo (base64) | ≈ 8 KB | 18,8 KB | 32,5 KB | 48,0 KB |
| Píxeles del PNG fuera del lienzo (≈ 1 %) | igual | 98 | 114 | 98 |
| Error de cuantización (/255) | 4,3 | 4,8 | 4,8 | 4,8 |

Conclusiones **[HECHO]** (medidas) e **[HIPÓTESIS]** (interpretación):

- 40×60 usa 1,5 muestras por píxel del dibujo → el pixel art sale irregular (se ve en `...\alta-resolucion\misma_altura_escribiendo_0.png`: el `>` del terminal queda roto). **No recomendable.**
- 52×80 es una duplicación exacta ×2 del dibujo: limpio. 64×96 (2,4) es algo irregular pero el más detallado; añade bordes suavizados y algunos píxeles grises de antialiasing.
- **[HIPÓTESIS]** «Más resolución» no crea píxeles de dibujo nuevos: la figura tiene ≈ 21 × 32 píxeles reales. Lo que aporta es detalle de bordes/sombras (26-32 % de las muestras difieren del píxel nativo) y mayor tamaño en pantalla.
- **[HECHO] Límites del motor para Raster**, verificados con un plugin de prueba aparte (`...\diagnostico-emi\scripts\rastertest\`, `claude plugin test`): acepta 26×20, 40×30, 52×40, 64×48, 128×96 y **512×256**; **rechaza** 513 columnas o 257 filas. **[LÍMITE]** Esta prueba solo valida el árbol; no prueba cómo lo pinta Windows Terminal ni el comportamiento al superar 1024 pares de color (el Raster, según el `.d.ts:9185-9187`, pinta 1024 pares distintos «a la vez» y el resto «como el más cercano»).
- **[HECHO] Ninguna de las tres cabe en las 15 filas medidas** (ni siquiera la actual).

Imágenes comparativas (todas en `C:\Users\Admin0011\Downloads\diagnostico-emi\alta-resolucion\`): `misma_altura_*.png` (detalle a igual altura), `tamano_real_en_pantalla.png` (tamaño relativo real con celda 8×16).

---

## 5. Código relevante

### 5.1 `hooks\register.tsx` — la banda en terminal (líneas 333-404, extracto fiel)

```tsx
on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
  const aj = await read($, ajustes)
  if (e.props.hasSurvey || aj.tamano === 'oculta') {
    return next(e)
  }
  const a = await read($, animo)
  const n = await read($, tic)          // leer `tic` suscribe el dibujo: cada latido redibuja
  // ...
  const resto = await next(e).catch(() => undefined)   // convive con otras bandas (termometro/objetivo)
  const ajeno = tieneContenido(resto) ? resto : null
  // ... rama 'compacta' (una línea de texto) ...
  if (e.surface === 'terminal') {
    const { Box, Button, Raster, Text } = $.ui.resolve(e)
    const c = celdas(fotograma(a.estado, aj.tamano === 'mini' ? 'X' : 'L', n))   // :378
    const banda = (
      <Box flexDirection="row" gap={1}>
        <Raster key="emi" columns={c.columnas} rows={c.filas} cells={c.cells} />
        <Box flexDirection="column"> {/* nombre, frase, detalle, botón «compacta» */} </Box>
      </Box>
    )
    return ajeno ? <Box flexDirection="column">{banda}{ajeno}</Box> : banda
  }
  // escritorio / vscode / móvil: Svg con escala entera
  const { Box, Button, Svg, Text } = $.ui.resolve(e)
  const d = dibujoSvg(fotograma(a.estado, 'L', n))                                  // :410
  const escala = aj.tamano === 'grande' ? 4 : aj.tamano === 'mini' ? 2 : 3          // :411
  // <Svg source={d.source} alt=... width={d.ancho * escala} height={d.alto * escala} />
})
```

**Observación [HECHO, del código]:** el Mod **no lee `e.props.maxRows`**: elige el sprite solo por el ajuste del usuario, no por el espacio disponible.

### 5.2 `hooks\dibujo.ts` — de filas de píxeles a celdas Raster (líneas 42-72)

```ts
export const TARJETA = 0xf5e6fd          // lila del PNG: hace visible el contorno negro en terminal oscuro
const color = (c: string) => { const i = ALFABETO.indexOf(c); const hex = i >= 0 ? PALETA[i] : undefined
                               return hex ? parseInt(hex.slice(1), 16) : TARJETA }

export function celdas(filas: readonly string[]): Celdas {            // 2 píxeles por celda
  const ancho = filas[0]?.length ?? 0
  const pares = Math.ceil(filas.length / 2)
  const palabras = new Uint32Array(ancho * pares * 3)                 // [codepoint, fg, bg] por celda
  let k = 0
  for (let r = 0; r < pares; r += 1) {
    const arriba = filas[r * 2] ?? ''; const abajo = filas[r * 2 + 1] ?? ''
    for (let x = 0; x < ancho; x += 1) {
      const a = arriba[x] ?? '.'; const b = abajo[x] ?? '.'
      palabras[k] = 0x2580                                            // ▀ medio bloque superior
      palabras[k + 1] = a === '.' ? TARJETA : color(a)                // fg = píxel de arriba
      palabras[k + 2] = b === '.' ? TARJETA : color(b)                // bg = píxel de abajo
      k += 3
    }
  }
  return { columnas: ancho, filas: pares, cells: (new Uint8Array(palabras.buffer) as Uint8Array & { toBase64: () => string }).toBase64() }
}
```

Animación (`dibujo.ts:30-40`): 4 fotogramas por estado; avanza uno por tic (250 ms), o uno cada 2 tics en `nueva/pensando/leyendo/duerme`.

### 5.3 `mascota-lab\hooks\register.tsx` — medición y banda de prueba (extracto)

```tsx
let medido = { maxRows: 0, bodyColumns: 0, columnas: 0, filas: 0, superficie: '' }   // un hook de dibujo no puede escribir estado

on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
  medido = { maxRows: e.props.maxRows, bodyColumns: e.props.bodyColumns,
             columnas: e.viewport?.columns ?? 0, filas: e.viewport?.rows ?? 0, superficie: e.surface }
  const sel = await read($, seleccion)
  if (sel.tam === 'off' || e.props.hasSurvey || e.surface !== 'terminal') return next(e)
  // ... dibuja <Raster key="lab" columns rows cells/> + texto «Cabe entero» / «NO cabe entero»
  //     cabe = e.props.maxRows >= c.filas
})
```

Comando: `/emilab` (informe), `/emilab 26|40|52|64` (dibuja), `/emilab off`. No hace nada hasta que se invoca.

---

## 6. API: qué permite cambiar altura, ubicación y representación

Referencias: `C:\Users\Admin0011\.claude\dev-mods\da5e8c78-c252-4d1c-9f43-47016e40a9d5\mascota\.claude-plugin\types\claude-code\index.d.ts` (extracto en `...\diagnostico-emi\API_EXTRACTO_claude-code.d.ts`).

| Elemento / método | Qué permite | Línea | Estado |
|---|---|---|---|
| `AbovePrompt` (componente) | Banda sobre el prompt; **solo terminal y escritorio** | 10180-10190 | DOC; HECHO que funciona en terminal |
| `e.props.maxRows`, `bodyColumns`, `scroll.bodyRows`, `hasSurvey`, `isWorking` | Medir el espacio de la banda (**solo lectura**) | 10196-10226 | DOC + HECHO (medido) |
| `e.viewport` (`columns`, `rows`, `isFullscreen?`) | Tamaño de la superficie y layout | 10325-10351 | DOC; `columns/rows` HECHO, `isFullscreen` **no leído** |
| `Raster` (`key`, `columns` 1–512, `rows` 1–256, `cells`) | Rejilla de celdas con glifo + fg + bg; **solo terminal**; «1024 pares de color a la vez» | 9188-9215 | DOC; límites 512×256 HECHO (kit) |
| `$.ui.blit({ requestId, key, cells \| source })` | Repintar un Raster o cambiar un Image con clave **sin pasar por el render**; hasta 120/s, ~60 mostrados | 2351-2371 | DOC; **no usado ni probado** |
| `Image` (`source` png/rgba/file/shm, `columns`, `rows`, `alt`) | Píxeles reales sobre una caja de celdas **«donde el terminal puede (kitty, Ghostty), el `alt` en otro caso»**; solo terminal | 5273-5309 | DOC; **no probado** |
| `Svg` (`source` ≤ 131 072 caracteres, `width`, `height`, `alt`, `isInteractive`) | Dibujo vectorial; superficies remotas (escritorio, vscode, móvil) | 12203-12230 | DOC; árbol validado por el kit, **no visto en pantalla** |
| Tabla de elementos por superficie (`Elements`) | `terminal`: Box, Text, Button, Input, Select, Link, Code, Markdown, Client, **Raster, Image**; `desktop`: …, **Svg**, Client | 3774-3841 | DOC |
| `$.ui.open({ id, title, focus, closeOnEscape, holdToasts, rows, columns })` | Abrir un **panel** | 2450-2472, 7333-7403 | DOC; **no probado** |
| `Pane` (props `placement: 'dock'\|'inline'`, `bodyColumns`, `scroll.bodyRows`) | Panel «acoplado junto a la conversación (en pantalla completa desde 110 columnas)» o en línea sobre el prompt | 10247-10292 | DOC; **no probado** |
| `PaneOpenArgs.rows` | Filas pedidas **solo en línea**; «el dock la ignora» | 7383-7390 | DOC |
| `PaneOpenArgs.columns` | Columnas pedidas **solo acoplado**; el dock se abre «de suelo a techo» con ese ancho | 7391-7402 | DOC |
| Colocación de un panel no pedido | Si no lo pide el usuario, desde 144 columnas (110 si lo pidió) | 2454-2456 | DOC |
| `$.ui.status(text)` / `$.ui.toast(text)` | Línea de estado fija / aviso; **solo texto** | 2437-2449 | DOC; HECHO que funcionan en otros Mods |
| `$.ui.invalidate('ui.render')` | Forzar redibujo (máx. 10/s; 30/s en terminal) | 2338-2350 | DOC |
| `$.process.run(argv, init)` | Ejecuta un comando y **espera a que termine** (timeout 30 s por defecto, 10 min máx.; «rechaza si sigue corriendo») | 3470-3487 | DOC; HECHO que funciona para PowerShell breve |
| `$.audio.play` | Solo reproduce con `afplay` (macOS); en Windows «no reproduce nada» | 2638-2640 | DOC |

---

## 7. Alternativas (verificado / no verificado)

| # | Alternativa | Qué se sabe | Estado |
|---|---|---|---|
| A | **Raster en `AbovePrompt`** (actual) | Funciona; limitado a `maxRows` (15 aquí) | **VERIFICADO** (funciona) y **medido** (el límite) |
| B | **Elegir el sprite según `e.props.maxRows`** | Solo requiere leer una prop ya disponible; `mini` (10 filas) cabe | Técnicamente simple; **no implementado** |
| C | **`Pane` acoplado (`placement: 'dock'`) con Raster dentro** | Documentado «de suelo a techo» (`:7393`) y desde 110 columnas (`:10268`); tu terminal tiene 156 columnas | **NO verificado.** Interrogantes: altura útil real del dock en 41 filas (¿≈ 39-40?, el `.d.ts` dice que una fila es para la marca de cierre, `:10280`), y cuántas columnas le quita a la conversación |
| D | `Pane` en línea (`placement: 'inline'`) | «el marco se ajusta al árbol», `rows` es una petición (`:7383-7389`), «hasta lo que el layout permita» | NO verificado; probablemente heredaría el mismo tope |
| E | **Layout de pantalla principal** (`CLAUDE_CODE_NO_FLICKER=0`) | `maxRows` pasaría a ser «la altura del terminal» (`:10200-10202`) | NO verificado; **cambia la configuración global**; efectos secundarios sobre la interfaz no documentados |
| F | **Más filas de terminal** (ventana más alta o fuente menor) | Consecuencia directa del tope proporcional | HIPÓTESIS (fórmula de §3.2 extrapolada de un solo punto) |
| G | **`Svg` en la app de escritorio** (`AbovePrompt` + `Svg`) | El Mod ya genera el SVG y el kit valida el árbol en la superficie `desktop` (`mascota.test.ts`: «se dibuja en el terminal… y en el escritorio») | Árbol VÁLIDO (HECHO); **no visto en una ventana real**; el SVG no depende de celdas de terminal (≤ 131 072 caracteres) |
| H | **`Image` (protocolo kitty/Ghostty)** | El `.d.ts` dice que solo pinta píxeles «donde el terminal puede (kitty, Ghostty)», en otro caso muestra `alt` | **HIPÓTESIS (conocimiento general, sin verificar)**: Windows Terminal no implementaría ese protocolo; habría que probarlo |
| I | `$.ui.blit` para animar sin redibujar la banda | Documentado para Raster/Image con clave | NO usado ni probado; reduciría coste, **no** cambia el tope de filas |
| J | **Ventana independiente** lanzada con `$.process.run` (PowerShell/otra app) | `run` espera a que el proceso termine y rechaza si sigue vivo (`:3478-3480`); haría falta lanzarlo «desacoplado» | **NO verificado.** Rompe la integración con el motor; sin acceso a los eventos salvo mediante archivos |
| K | Texto en `$.ui.status` / `compacta` | Siempre cabe | HECHO (funciona; es la versión actual `compacta`) |

---

## 8. Calidad de los sprites

### 8.1 Origen y extracción (HECHO, scripts en `...\diagnostico-emi\scripts\`)

- Fuente: `C:\Users\Admin0011\Downloads\animacion de Emilia pixel de estados.png`, 1448 × 1086, hoja de 12 paneles (3 columnas × 4 filas) con 4 fotogramas por estado. Paneles: x = 15-473, 490-955, 975-1435; y = 30-262, 283-515, 538-777, 795-1043 (`emi_lib.py`).
- Existe otra hoja con 20 estados nuevos y 8 fotogramas (`C:\Users\Admin0011\Downloads\animacion.png`): **no usada todavía**.
- Pasos del pipeline (`emi_lib.py`, `emi_lib2.py`, `build6.py`, `gen_ts.py`):
  1. Recorte por panel con **fronteras compartidas** entre fotogramas (partición exacta; verificada: 0 píxeles en dos fotogramas) y búsqueda del hueco de menor contacto (±34 px).
  2. Fondo: *flood-fill* desde el borde con tolerancia 28 sobre el lila del panel (≈ 245,230,253). No es un umbral por píxel: así se conservan las zonas blancas interiores.
  3. Rejilla real del dibujo: **4,75 px**, único periodo con pico de contraste en los dos ejes (K=4 daba 6,5 % y 9,8 %; en 4,75: 19,8 % y 17,9 %); grosor del contorno 4,4 px horizontal / 4,2 px vertical (píxel casi cuadrado).
  4. Muestreo: un píxel nativo por bloque de la rejilla; mediana del 60 % central; si el bloque tiene ≥ 30 % de trazo oscuro se toma el color oscuro real del bloque (contornos aislados 16,3 % → 3,9 %).
  5. Lienzo común 26 × 40 anclado abajo-centro; fase de rejilla compartida por los 4 fotogramas de cada estado.
  6. Reducción `mini` por vecino más cercano (mitad exacta, 13 × 20) con el desfase 0/1 de menor error por estado.
  7. Paleta de 88 colores (3 semillas por tono vivo + corte de medianas): error de cuantización 4,3/255.
  8. Escritura a `hooks\sprites.ts` (filas separadas por `/`, un carácter por color, `.` transparente).
- Verificación **[HECHO]**: la escritura a TypeScript es exacta (0 diferencias en 144 fotogramas); cobertura media del primer plano 96,3 % (mín. 94,4 %); sin contaminación; desviación de alineación máx. 1,8 píxeles nativos.

### 8.2 Qué resolución tienen los datos

L: 26 × 40 px por fotograma (≈ 21 × 32 de figura + margen para efectos); X: 13 × 20. Cada «píxel» del sprite equivale a 4,75 px del PNG (123,5 × 190 px de PNG cubiertos).

### 8.3 Qué se pierde

- **[HECHO]** Detalle dentro de cada bloque de 4,75 px (26-32 % de las muestras a doble resolución difieren del píxel nativo).
- **[HECHO]** En 12 fotogramas los sprites del PNG **se solapan entre sí** (`duerme` 26-28 px de contacto, `para` 33, `leyendo` 23, `terminado` 9-15): se separan por el punto de menor contacto, así que en el borde del solape puede faltar o sobrar hasta ≈ 6 píxeles nativos.
- **[HECHO]** ≈ 1 % del primer plano queda fuera del lienzo común.
- **[HECHO]** `mini` pierde detalles finos (a veces los ojos).
- **[HIPÓTESIS]** Los ojos celestes se perdían con paletas pequeñas; se resolvió con semillas por tono (los ojos salen celestes en los 4 tamaños de prueba).

---

## 9. Pruebas, errores y límites

### 9.1 Resultados automáticos (HECHO)

| Prueba | Resultado |
|---|---|
| `claude plugin validate mascota` | Pasa (1 advertencia: falta el campo `author`) |
| `claude plugin test mascota` | **14 / 14** |
| `claude plugin test mascota-lab` | **3 / 3** |
| `tsc` (TypeScript 5.6, tipos de la API) sobre `mascota` y `mascota-lab` | Sin errores |
| Plugin de prueba `rastertest` (aparte, en carpeta temporal) | 2 / 2: acepta hasta 512 × 256, rechaza 513 columnas o 257 filas |

### 9.2 Errores encontrados en el camino y corregidos (HECHO)

1. Recorte fijo cortaba la figura en 21 de 48 fotogramas → fronteras compartidas.
2. Umbral de fondo por píxel borraba el vestido y el moño blancos → *flood-fill*.
3. Cuadrícula de 4 px fija (real 4,75) → muestreo con rejilla fraccionaria.
4. Un filtro de «líneas planas» y un umbral de filas demasiado bajo **borraban zapatos y piernas** → umbrales corregidos y verificados por una prueba de suelo.
5. Contorno partido y ojos verdosos → muestreo de trazo y paleta con semillas por tono.
6. Sprites antiguos de 70 % y 50 % mezclaban colores → eliminado el 70 %; `normal` = nativo.

### 9.3 Imágenes y capturas (rutas)

| Qué | Ruta |
|---|---|
| Comparativas antes/después del pipeline | `C:\Users\Admin0011\Downloads\diagnostico-emi\correccion\antes_despues_*.png`, `final_*.png`, `contacto_corregido_L.png` (48 fotogramas) |
| Diagnóstico por etapas | `C:\Users\Admin0011\Downloads\diagnostico-emi\etapas_1_4_*.png`, `comparativa_*.png`, informes `.txt` |
| Alta resolución | `C:\Users\Admin0011\Downloads\diagnostico-emi\alta-resolucion\` |
| Captura antigua del terminal (sprite anterior, ya corregido) | `C:\Users\Admin0011\OneDrive\Imágenes\Screenshots\Captura de pantalla 2026-10-08 182953.png` |
| Hojas originales | `C:\Users\Admin0011\Downloads\Emilia Claude pixel de estados y emociones.png`, `...\animacion de Emilia pixel de estados.png` (usada), `...\animacion.png` (20 estados nuevos, sin usar) |

### 9.4 Límites de las pruebas (LÍMITE)

- **No hay captura del terminal real con los sprites actuales ni con el laboratorio** (solo la salida de texto de `/emilab`).
- Las comparativas son **simulaciones** a partir de los datos reales (celdas de 8 × 16 px), no capturas de Windows Terminal.
- No medí coste de CPU, parpadeo del terminal ni tasa real de refresco; solo calculé bytes por redibujo.
- No se probó el Mod en la app de escritorio con una ventana real.
- No leí `viewport.isFullscreen` en tu sesión.

---

## 10. Recomendación técnica

Ordenada por viabilidad (con lo ya comprobado), calidad visual, rendimiento y dificultad.

| # | Propuesta | Viabilidad | Calidad | Rendimiento | Dificultad | Etiqueta |
|---|---|---|---|---|---|---|
| 1 | **Adaptar el sprite a `e.props.maxRows`** (`mini` de 10 filas si `maxRows < 20`; 20 filas si cabe; `compacta` si ni eso). Corrige ya que `grande` y `normal` se recortan | Alta | Media (en 15 filas solo cabe `mini`) | Excelente | Baja (≈ 10 líneas en `register.tsx:378`) | Seguro de implementar; mejora real asegurada; **no resuelve la fidelidad** |
| 2 | **Probar un `Pane` acoplado** con el Raster de 52×80 (40 filas) o 40×60 (30 filas) | **Por comprobar** (es lo único documentado que no usa el tope de la banda) | Alta si cabe | Buena (≈ 24-33 KB por redibujo) | Media (nuevo hook `ui.render {component:'Pane'}`, `$.ui.open`, comando para abrirlo) | **HIPÓTESIS.** Hay que medir con el laboratorio la altura útil real (`scroll.bodyRows`) y `placement` |
| 3 | **Subir las filas disponibles**: ventana más alta o fuente menor (el tope es proporcional) | Alta | Alta | Igual | Ninguna (acción del usuario) | HIPÓTESIS (fórmula con un solo punto: 41 → 15) |
| 4 | **Layout de pantalla principal** (`CLAUDE_CODE_NO_FLICKER=0`) | Media | Alta si `maxRows` = altura del terminal | Sin datos | Baja (variable de entorno), pero **cambia la experiencia global** | DOC; **no probado** |
| 5 | **SVG en la app de escritorio** a alta resolución (52×80 / 64×96 con escala entera) | Media | **Muy alta**, no depende de celdas ni de filas de terminal | Buena | Baja (el Mod ya genera el SVG; falta usar sprites mayores y comprobar el tamaño ≤ 131 072 caracteres) | Árbol válido (HECHO); **sin ver en pantalla** |
| 6 | **`Image` en terminal** | Baja en Windows Terminal | Muy alta si se soporta | Alta | Media | HIPÓTESIS: Windows Terminal probablemente no soporta el protocolo; probar con `alt` como respaldo |
| 7 | **Ventana independiente** (proceso aparte) | Baja | Muy alta | Variable | Alta; pierde integración con el motor | HIPÓTESIS, no verificada |
| 8 | **Subir resolución de los sprites sin más** (40×60, 52×80, 64×96 en `AbovePrompt`) | **No viable con 15 filas** (HECHO) | — | — | — | Descartada mientras el tope no cambie |

**Elección de resolución:** si el espacio se amplía (opciones 2-5), **52×80** es la mejor relación (duplicación exacta ×2, 98,6 % de cobertura, 658 pares de color); **64×96** es lo máximo que valida el motor y conserva más detalle (98,7 %, 812 pares, el 79 % del límite de 1024) pero ocupa 48 filas. **40×60 no compensa** (1,5 muestras por píxel).

### Comprobaciones pendientes para cerrar las hipótesis (no hechas por restricción de este encargo)

1. Imprimir `e.viewport.isFullscreen` en `/emilab` (una línea) para confirmar el layout.
2. Añadir a `mascota-lab` un comando `/emilab pane` con `$.ui.open({ id: 'emilab', rows, columns })` y un hook `Pane` que muestre `placement`, `bodyColumns` y `scroll.bodyRows`, para medir la altura útil del dock en 41 filas.
3. Captura de `/emi grande` y de `/emilab 64` en el terminal real.
4. Probar `Image` con `alt` para ver qué hace Windows Terminal.
5. Probar el Mod en la app de escritorio.

---

## 11. Archivos que conviene dar a ChatGPT

**Imprescindibles (texto, caben en un mensaje):**
1. Este informe: `C:\Users\Admin0011\Downloads\INFORME_TECNICO_EMILIA.md`
2. `...\dev-mods\...\mascota\hooks\register.tsx`, `hooks\dibujo.ts`, `hooks\estados.ts`, `types\index.d.ts`, `.claude-plugin\plugin.json`
3. `...\dev-mods\...\mascota-lab\hooks\register.tsx`
4. `C:\Users\Admin0011\Downloads\diagnostico-emi\API_EXTRACTO_claude-code.d.ts` (35 KB: solo los rangos de la API relevantes; el archivo completo pesa 614 KB)
5. Una captura del terminal con `/emi grande` y otra con `/emilab 64` (**aún no existen**)

**Recomendados:**
6. `...\mascota\tests\mascota.test.ts`
7. `...\diagnostico-emi\alta-resolucion\informe_alta_resolucion.txt` y 3-4 imágenes `misma_altura_*.png`
8. `...\diagnostico-emi\correccion\contacto_corregido_L.png` (los 48 fotogramas) y `antes_despues_nueva_0.png`

**Solo si debe regenerar sprites:**
9. `...\diagnostico-emi\scripts\` (`emi_lib.py`, `emi_lib2.py`, `build6.py`, `gen_ts.py`, `hires.py`, `eval5.py`, `rastertest\`) y las hojas PNG de §9.3

**No hace falta compartir:** `hooks\sprites.ts` y `mascota-lab\hooks\datos.ts` (datos generados de 68 KB y 173 KB), ni `.claude-plugin\types\claude-code-mcp` / `claude-code-tools`.


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
- `mascota-lab\hooks\register.tsx`: `/emilab 13|26|40|52|64`, `/emilab pane`, medidas en `C:\Users\Admin0011\.claude\mascota-lab\medidas.json` (banda: `maxRows`, `bodyColumns`, `isFullscreen`; panel: `placement`, `bodyColumns`, `bodyRows`). Medición automática de una sola vez (marca `auto.txt`).
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

- `C:\Users\Admin0011\.claude\dev-mods-backup\mascota-2026-10-08-antes-de-fidelidad\` (antes de la corrección de fidelidad)
- `C:\Users\Admin0011\.claude\dev-mods-backup\mascota-2026-10-08-1954-antes-del-panel\` (justo antes de esta actualización, versión de 26×40)
- `C:\Users\Admin0011\.claude\dev-mods-backup\mascota-lab-2026-10-08-1954-antes-del-panel\`

Para volver atrás: copiar el contenido de la carpeta de respaldo sobre `...\dev-mods\...\mascota\`.

### 12.8 Imágenes de esta actualización

`C:\Users\Admin0011\Downloads\diagnostico-emi\final-mod\`: `tamanos_*.png` (los 5 tamaños por estado, a partir de los datos finales), `simulacion_banda.png` y `simulacion_panel.png` (simulaciones), `informe_datos_finales.txt`.

---

## 13. Actualización: detección de fallos reales y celdas más ligeras (autorizado)

Respaldo previo: `C:\Users\Admin0011\.claude\dev-mods-backup\mascota-2026-10-08-antes-de-fallos-y-celdas\`

### 13.1 Cambios en el mod principal

| Cambio | Archivos | Qué hace |
|---|---|---|
| **Fallo real** | `hooks\deteccion.ts` (nuevo), `hooks\register.tsx` (`tool.call`, `tool.check`, `turn.start`, `turn.complete`) | Emilia solo se asusta si la herramienta devuelve un error de verdad. Una herramienta **denegada** (hook o permiso), un permiso **rechazado** o una **interrupción** ya no cuentan como fallo y Emi vuelve a «pensando» (Claude sigue trabajando). Las denegaciones del permiso se anotan con `tool.check`; los rechazos se reconocen además por el texto (`RECHAZO`) y por `turnoAbortado` |
| **ExitPlanMode** | `hooks\estados.ts` | Aprobar un plan es «te necesita», igual que una pregunta (`AskUserQuestion`); detalle «te pide aprobar el plan» |
| **Celdas con espacio** | `hooks\dibujo.ts` (`celdas`, `leerCeldas`, `colorDe`) | Si las dos mitades de una celda tienen el mismo color se emite un espacio con ese color de fondo en vez del glifo `▀`. La imagen es idéntica |

Sin cambios: panel acoplado, banda adaptativa, los 12 estados con sus 4 fotogramas, avisos y sonidos de Windows, indicadores de otras conversaciones, `/emi`, SVG del escritorio.

### 13.2 Pruebas (HECHO)

| Prueba | Resultado |
|---|---|
| `claude plugin validate mascota` | Pasa; ahora hay 12 hooks (nuevo: `tool.check`, con `.catch`) |
| `claude plugin test mascota` | **34 / 34** (antes 26): 8 pruebas nuevas |
| `tsc` (TypeScript 5.6) | Sin errores |
| Imagen idéntica | En los **240 fotogramas** (12 estados × 4 × 5 tamaños) los colores de arriba y de abajo de cada celda coinciden exactamente con los esperados |
| Menos glifos | Solo se pinta `▀` en el **33-47 %** de las celdas según el tamaño (en 40×60, el del panel, **36,6 %**) |
| Fallo real | Una denegación y un rechazo del usuario ya no muestran la frase de «falla» (antes sí, comprobado en una copia aparte); un error real (`ENOENT`) sigue mostrándola |

### 13.3 Limitaciones

- **[LÍMITE]** El beneficio de pintado de las celdas con espacio en Windows Terminal no está medido; sí está probado que la imagen no cambia.
- **[LÍMITE]** La correlación `tool.check` → `tool.call` (por `tool_use_id`) no se puede reproducir en el kit de pruebas; en la sesión real queda sin verificar. El texto del rechazo (`RECHAZO`) es una heurística que cubre el caso aunque `tool.check` no avise.
- **[LÍMITE]** `classic.PermissionRequest` y el despertar con `prompt.edit` siguen sin integrarse.
