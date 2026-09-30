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
| `HELLO 1` | La Pi anuncia la versión del protocolo | `HELLO 0 <fw> <proto>` |
| `J seq yaw pitch roll` | Nueva referencia articular. **Reemplaza** a la anterior (no se encola). Se recorta a los límites. | `ACK seq` o `ACK seq CLIPPED` |
| `S seq NOMBRE` | Reproduce un sonido. Un `seq` repetido no se reproduce dos veces. | `ACK seq`, luego `DONE seq` al terminar |
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
| `ERR seq MOTIVO` | `BAD_SEQ BAD_ARGS BAD_NUMBER TOO_LONG UNKNOWN_CMD UNKNOWN_SOUND STOP_ACTIVE`; `ERR 0 WATCHDOG` |
| `STATE seq ESTADO yaw pitch roll SONIDO` | `ESTADO` ∈ `RUN STOPPED WATCHDOG`. Los ángulos son **referencias del generador de trayectoria**, no medidos (los servos no tienen realimentación). |
| `HELLO 0 fw proto` | El ESP32 arrancó o se reinició: la Pi debe resincronizar |

## Reglas del firmware

1. **No bloqueante:** nada de `delay()`. Lazo de trayectoria a 100 Hz con `millis()`/`micros()`.
2. **Trayectoria:** por eje, perfil trapezoidal online con `vmax`/`amax` de `config.yaml` (ver `keepon/trajectory.py`, fórmula de frenado discreto).
3. **Límites:** yaw ±70°, pitch −20°/+30°, roll ±20°.
4. **Watchdog 500 ms:** sin comandos válidos → corta el sonido, frena y **mantiene la postura**; manda `ERR 0 WATCHDOG`. El próximo comando lo rearma. La Pi manda `PING` cada 200 ms si no mandó otra cosa.
5. **STOP enclavado:** mientras está activo, `J S HOME CANCEL` responden `ERR seq STOP_ACTIVE`.
6. **Timers LEDC separados** para servos (50 Hz) y buzzer (frecuencia variable): cambiar la nota no debe alterar el PWM de los servos.
