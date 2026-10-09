import io

# ---------- INFORME_TECNICO_EMILIA.md: sección 13 ----------
ruta = r"C:\Users\Admin0011\Downloads\INFORME_TECNICO_EMILIA.md"
t = open(ruta, encoding="utf-8").read()
assert "## 13. Actualización" not in t
t = t.rstrip("\n") + r'''

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
'''
open(ruta, "w", encoding="utf-8").write(t)

# ---------- INFORME_COMPARATIVO_MASCOTAS.md: resultado de bench v1 ----------
ruta = r"C:\Users\Admin0011\Downloads\INFORME_COMPARATIVO_MASCOTAS.md"
t = open(ruta, encoding="utf-8").read()
assert "## 10. Resultados de bench.json" not in t
t = t.rstrip("\n") + r'''

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
'''
open(ruta, "w", encoding="utf-8").write(t)
print("documentación actualizada")
