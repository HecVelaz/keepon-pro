# Pruebas de banco de los servos

Objetivo: comprobar que cada servo funciona, medir lo que el firmware necesita saber (pulso del centro, grados por µs, extremos, banda muerta, consumo) y decidir qué servo va en cada eje.

Esto **no** es el firmware del robot. `prueba_servo/prueba_servo.ino` es un programa de prueba para la **ESP32-C3-DevKitM-1** que se maneja desde el monitor serie.

## Servos disponibles

| Servo | Tipo | Par (4,8 V / 6 V) | Peso | Cables (−, +, señal) | ¿Sirve? |
|---|---|---|---|---|---|
| Hitec **HS-7955TG** | Digital, posición | ~18 / 24 kgf·cm | 65 g | negro, rojo, amarillo | **Sí** → pitch |
| TowerPro **MG996R** | Analógico/digital, posición | ~9,4 / 11 kgf·cm | 55 g | marrón, rojo, naranja | **Sí** → yaw |
| TowerPro **MG995** | Digital, posición | ~8,5 / 10 kgf·cm | 55 g | marrón, rojo, naranja | **Sí** → roll |
| SpringRC **SM-S4315R** | **Rotación continua** (la "R") | — | 60 g | (verificar) | **No como articulación** |

Pares tomados de fichas de vendedores. Hay que comprobarlos con las pruebas, no darlos por buenos.

**Por qué el SM-S4315R no sirve:** en un servo de rotación continua el pulso controla la **velocidad**, no la posición. Con 1500 µs se queda quieto, y con otros pulsos gira sin parar. No tiene realimentación de ángulo, así que no puede mantener la cabeza en un ángulo. La prueba 1 lo confirma: si gira sin detenerse, es de rotación continua. (El modelo de posición equivalente es el SM-S4315**M**.)

**Asignación propuesta:**
- **Pitch → HS-7955TG**, el de más par, porque pitch es el eje que carga contra la gravedad. Su cuerpo va montado sobre la plataforma de yaw.
- **Yaw → MG996R**. Con el eje vertical, la gravedad no le hace par, pero el **rodamiento** tiene que soportar el peso y el vuelco: ahora los servos que se mueven pesan ~120 g más que con los micro.
- **Roll → MG995**. Es el que tiene peor fama de temblor y banda muerta, y en roll se nota menos.
- Los micro (MG90S/SG90) quedan de repuesto o para pruebas.

## Conexionado

```
 FUENTE 6 V (+) ──── BORNERA V+  ──┬── rojo YAW ──┬── rojo PITCH ──┬── rojo ROLL
                                   │                  
                              C 2200 µF ≥10 V (+ a V+, − a GND)
                                   │
 FUENTE 6 V (−) ──── BORNERA GND ──┴── negro/marrón de cada servo
                                   └── GND de la ESP32-C3   (masa común)

 ESP32-C3-DevKitM-1                         señal (amarillo/naranja)
   GPIO0 ──[330 Ω]──────────────────────── servo YAW   (MG996R)
   GPIO1 ──[330 Ω]──────────────────────── servo PITCH (HS-7955TG)
   GPIO3 ──[330 Ω]──────────────────────── servo ROLL  (MG995)
   GND   ───────────────────────────────── bornera GND
   USB   ───────────────────────────────── notebook (alimenta SOLO a la ESP32)
```

| ESP32-C3 | Va a | Notas |
|---|---|---|
| GPIO0 | señal de yaw | fila de abajo de la placa |
| GPIO1 | señal de pitch | fila de abajo |
| GPIO3 | señal de roll | fila de abajo |
| GPIO10 | (buzzer, más adelante) | no se usa en esta prueba |
| GND | bornera GND | **obligatorio**: sin masa común el servo no entiende la señal |
| 5V / 3V3 | **nada** | no alimentar servos desde la placa |

Reglas:
- **Fuente de servos de 6 V**, separada. El HS-7955TG tiene un mínimo de 4,8 V, así que con 5 V cualquier caída lo deja fuera de rango. Con el eje trabado cada servo puede pedir 2,5–4,2 A. Para probar un servo a la vez alcanza con 3 A; para los tres juntos hace falta **≥ 6 A**. Si es una fuente de laboratorio, poner un límite de corriente.
- **Nunca** conectar el + de la fuente de servos al 5V de la ESP32, de la Pi ni del USB.
- La resistencia de 330 Ω en la señal es opcional y protege el GPIO. La señal de 3,3 V suele alcanzar; si un servo tiembla o no responde, ver `docs/REVISION_CODEX_HW.md` (buffer 74AHCT125).
- Capacitor de 1000–2200 µF y ≥ 10 V en la bornera, respetando la polaridad.
- Cables cortos y borneras, no protoboard (las pistas de un protoboard no aguantan amperes).

## Fuentes para la prueba individual (un servo a la vez)

| Fuente | Uso | Ajuste |
|---|---|---|
| **De laboratorio** (preferida) | Todas las pruebas individuales | **6,0 V**, límite de corriente en **1,0 A** para empezar; subirlo a 2 A solo para la prueba de consumo |
| **ALP002 ajustable** (`docs/fuente/`): 3–24 V, **1,5 A máx.** | Solo "¿se mueve?", un servo y sin carga | Ajustar a 6,0 V **sin nada conectado** y comprobar con el multímetro |

Cuidados con la ALP002:
- Su placa dice **entrada 100–120 V de alterna**. En Paraguay la red es de 220 V: **no enchufarla directo** salvo que tenga otra etiqueta que diga 100–240 V. Si no, hace falta un transformador 220→110 V.
- La perilla llega a **24 V**: si se mueve sin querer, quema el servo. Fijar 6 V, medir con el multímetro y recién ahí conectar. No tocar la perilla con el servo conectado.
- 1,5 A alcanza para un servo sin carga (200–500 mA moviéndose), pero **no** para un servo trabado (2,5–4 A). Si el servo hace tope, la tensión cae y la fuente puede apagarse o reiniciarse.
- No sirve para los tres servos juntos ni para la cabeza armada.

Antes de cada servo:
1. Fuente **apagada**. Conectar GND de la fuente → GND del servo y GND de la ESP32.
2. Conectar la señal al GPIO del eje y el + de la fuente al rojo del servo.
3. ESP32 conectada a la notebook por USB, con el programa ya cargado.
4. Encender la fuente: el servo tiene que quedar **flojo y en silencio** (todavía no recibe pulsos). Si zumba o se mueve solo, apagar y revisar.
5. En el monitor serie: `e <eje>` y después `c`. Seguir con el procedimiento de abajo.
6. Al terminar: `o`, apagar la fuente y recién ahí desconectar.

Con la fuente de laboratorio, si el indicador de **limitación de corriente (CC)** se enciende mientras el servo está quieto, algo está mal (tope mecánico, servo dañado o cableado invertido): apagar.

## Cargar el programa

1. Desde la terminal (ya instalado en la notebook): ver los comandos `arduino-cli` en `CLAUDE.md`. O con el IDE: Arduino IDE 2 → Gestor de placas → instalar **esp32 de Espressif, versión 3.x** (el programa usa `ledcAttach`, que no existe en la 2.x).
2. Placa: **ESP32C3 Dev Module**. Abrir `pruebas_servos/prueba_servo/prueba_servo.ino` y subirlo.
3. Monitor serie a **115200 baud**, fin de línea **"Nueva línea"**. Escribir `h` para ver la ayuda.

Todos los ejes arrancan **sin pulso**. El primer comando a un eje lo hace saltar a esa posición, porque la ESP32 no sabe dónde quedó el servo. Por eso las primeras pruebas se hacen **sin brazo cargado** y con el servo suelto o bien sujeto.

## Procedimiento por servo (uno a la vez, sin carga)

Conectar solo el servo que se prueba, en el canal del eje que se le asigna (por ejemplo, el HS-7955TG en GPIO1 → `e 1`).

1. **Funciona / tipo:** `c` (1500 µs). Un servo de posición se mueve al centro y se queda quieto. Uno de rotación continua gira o se queda quieto, pero con `p 1600` empieza a girar y **no para**. Si eso pasa, `o` para apagarlo.
2. **Centro:** marcar en el brazo la posición con 1500 µs.
3. **Extremos seguros:** con `+` / `-` (pasos de 10 µs) acercarse despacio a cada lado. Si zumba fuerte sin moverse, o hace ruido de tope, es el extremo mecánico: **volver 50 µs** y anotar. Para pasar de 1000–2000 µs, ampliar primero los límites con `l 600 2400`.
4. **Grados por µs:** con un transportador, anotar el pulso a −45° y a +45°. Grados/µs = 90 / (pulso₊₄₅ − pulso₋₄₅). Lo usa el firmware para convertir ángulos.
5. **Banda muerta:** desde una posición quieta, subir el pulso de a poco con `p` (de 2 en 2 µs) hasta que el brazo se mueva. Hacerlo en los dos sentidos.
6. **Holgura (backlash):** llegar al mismo pulso desde un lado y desde el otro, y medir la diferencia de ángulo.
7. **Barrido y temperatura:** `v 300` y `b 1200 1800` durante 5 minutos. Escuchar el ruido, tocar la carcasa y ver si tiembla en los extremos. `s` para detenerlo.
8. **Consumo:** multímetro en serie con el + del servo. Medir en reposo, en barrido y sosteniendo con la mano una carga suave. **No dejarlo trabado** más de 1–2 s.
9. **Reposo:** con el servo quieto en el centro, ¿zumba? Los digitales suelen hacerlo. En un robot social se nota.

Después, los tres juntos con `b` en los tres ejes: medir la tensión en la bornera mientras se mueven. Tiene que mantenerse ≥ 5,5 V con fuente de 6 V. Si la ESP32 o la Pi se reinician, hay un problema de masa o de fuente.

## Planilla de resultados

Completar una columna por servo. Estos datos van después a la calibración del firmware (centro, límites y sentido por eje).

| Medida | HS-7955TG | MG996R | MG995 | SM-S4315R |
|---|---|---|---|---|
| Fecha / quién | | | | |
| ¿Posición o continuo? | | | | |
| Pulso del centro (µs) | | | | — |
| Extremo seguro mín / máx (µs) | | | | — |
| Pulso a −45° / +45° (µs) | | | | — |
| Grados por µs | | | | — |
| Banda muerta (µs) | | | | — |
| Holgura (°) | | | | — |
| Corriente reposo / barrido (mA) | | | | |
| Temperatura tras 5 min | | | | |
| ¿Zumba en reposo? | | | | |
| Observaciones | | | | |

## Rangos que tiene que cubrir cada eje (enunciado)

| Eje | Rango mínimo | Recorrido total |
|---|---|---|
| Yaw | ±70° | 140° |
| Pitch | −20° / +30° | 50° |
| Roll | ±20° | 40° |

Recorrido de un servo = (extremo máx − extremo mín) × grados por µs. Yaw es el que más recorrido pide: si un servo no llega a 140° entre sus extremos seguros, **no puede ir en yaw**. Muchos servos estándar dan solo ~90–120° entre 1000 y 2000 µs, así que hay que medirlo.
