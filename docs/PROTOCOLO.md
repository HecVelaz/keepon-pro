# Protocolo serie PC/Pi ⇄ ESP32-S3 (v1)

Contrato entre `keepon/` (Python) y `firmware/` (ESP32-S3). La especificación **ejecutable** es `keepon/sim_esp32.py`: el firmware debe comportarse igual, y `tests/test_protocol_sim.py` lista los casos.

## Formato

- USB CDC nativo del ESP32-S3 (`/dev/ttyACM0`), 115200 baud.
- Líneas ASCII terminadas en `\n`, máximo 64 caracteres, campos separados por un espacio.
- Ángulos en grados con un decimal. Convención: **yaw + = derecha**, **pitch + = arriba**, **roll + = horario visto desde atrás** (verificar al montar).
- Todo comando lleva `seq` (entero creciente) para asociar respuestas.

## Comandos (Pi → ESP32)

| Comando | Efecto | Respuesta |
|---|---|---|
| `HELLO 1` | La Pi abre sesión con la versión del protocolo (sin seq). Reinicia la numeración de sonidos. | `HELLO 1 <fw> <proto>` o `ERR 0 BAD_VERSION` |
| `J seq yaw pitch roll` | Nueva referencia articular. **Reemplaza** a la anterior (no se encola). Se recorta a los límites. | `ACK seq` o `ACK seq CLIPPED` |
| `S seq NOMBRE` | Reproduce un sonido. Un `seq` **menor o igual** al mayor `S` de la sesión (reenvío o viejo) se confirma con ACK pero **no se reproduce**. | `ACK seq`, luego `DONE seq` al terminar |
| `CANCEL seq SOUND` | Corta el sonido actual | `ACK seq` |
| `PING seq` | Keepalive + estado | `ACK seq` + `STATE seq ...` |
| `STOP seq` | Frena suave y corta el sonido. **Enclavado** hasta `RESUME`. No va a HOME. | `ACK seq` |
| `RESUME seq` | Libera el STOP | `ACK seq` |
| `HOME seq` | Va a la postura HOME con rampa | `ACK seq` |

Sonidos: `R2D2 POLCA ABUCHEO PIROPO DESAPROBACION BEEP_NEUTRO BEEP_TIMIDO BEEP_ATREVIDO BEEP_MALEDUCADO`.

## Respuestas (ESP32 → Pi)

| Respuesta | Significado |
|---|---|
| `ACK seq [CLIPPED]` | Comando **aceptado** (no significa que el movimiento terminó) |
| `DONE seq` | El sonido `seq` terminó naturalmente |
| `ERR seq MOTIVO` | `BAD_SEQ BAD_ARGS BAD_NUMBER TOO_LONG EMPTY UNKNOWN_CMD UNKNOWN_SOUND STOP_ACTIVE`; `ERR 0 WATCHDOG`; `ERR 0 BAD_VERSION` |
| `STATE seq ESTADO yaw pitch roll SONIDO` | `ESTADO` ∈ `RUN STOPPED WATCHDOG`. Los ángulos son **referencias del generador de trayectoria**, no medidos (los servos no tienen realimentación). |
| `HELLO 0 fw proto` | **Arranque/reinicio** del ESP32 (servos en HOME, sin sonido) |
| `HELLO 1 fw proto` | Sesión aceptada (respuesta al `HELLO` de la Pi) |

## Sesión y reinicios

1. La Pi manda `HELLO 1` y no comanda nada hasta recibir `HELLO 1 fw proto` (lo reintenta cada 0,5 s).
2. Si con la sesión abierta llega `HELLO 0 ...`, el ESP32 **se reinició**. Entonces la Pi:
   - cancela todas las acciones (el ESP32 ya no reproduce nada),
   - toma HOME como referencia y reabre la sesión,
   - reenvía `STOP` si el operador lo tenía activo.
3. Toda línea mal formada, en cualquier dirección, se descarta con `ERR` o se ignora: nunca corta el programa.

## Reglas del firmware

1. **No bloqueante:** nada de `delay()`. Lazo de trayectoria a 100 Hz con `millis()`/`micros()`.
2. **Trayectoria:** por eje, planificación discreta exacta con `vmax`/`amax` de `config.yaml`. Copiar la fórmula cerrada de `keepon/trajectory.py` (`_v_max_to_stop`). Garantiza que las **posiciones emitidas** no superen amax y que el último paso caiga justo en el objetivo. STOP y watchdog frenan hacia `brake_target()`.
3. **Límites:** yaw ±70°, pitch −20°/+30°, roll ±20°.
4. **Watchdog 500 ms:** sin comandos válidos → corta el sonido, frena y **mantiene la postura**; manda `ERR 0 WATCHDOG`. El próximo comando lo rearma. La Pi manda `PING` cada 200 ms si no mandó otra cosa.
5. **STOP enclavado:** mientras está activo, `J S HOME CANCEL` responden `ERR seq STOP_ACTIVE`.
6. **ESP32-S3:** usar el conector marcado USB (nativo, GPIO19/20), no el de UART. Confirmar en el esquema de la placa. En Arduino: `USB CDC On Boot: Enabled`.
7. **Timers LEDC separados** para servos (50 Hz) y buzzer (frecuencia variable): cambiar la nota no debe alterar el PWM de los servos.
