# Pruebas de banco de los servos

Objetivo: comprobar que cada servo funciona, medir lo que el firmware necesita saber (pulso del centro, grados por µs, extremos, banda muerta, consumo) y decidir qué servo va en cada eje.

Esto **no** es el firmware del robot. `prueba_servo/prueba_servo.ino` es un programa de prueba para la **ESP32-C3-DevKitM-1** que se maneja desde el monitor serie.

## Servos disponibles

| Servo | Tipo | Par (4,8 V / 6 V) | Peso | Cables (−, +, señal) | ¿Sirve? |
|---|---|---|---|---|---|
| Hitec **HS-7955TG** | Digital, posición | ~18 / 24 kgf·cm | 65 g | negro, rojo, amarillo | **Sí** → pitch |
| TowerPro **MG90S** (micro) | Posición | 1,8 / 2,2 kgf·cm | 13,4 g | marrón, rojo, naranja | **Sí** → yaw provisorio |
| TowerPro **SG90** (micro) | Posición, engranajes plásticos | ~1,5–1,8 kgf·cm | 9 g | marrón, rojo, naranja | **Sí** → roll |
| SpringRC **SM-S4315R** | **Rotación continua** (la "R") | — | 60 g | (verificar) | **No como articulación** |
| DSSERVO **RDS3218** (del recolector de frutas) | Digital, posición, versión de 270° | 20 kgf·cm (etiqueta, 4,8–6,8 V) | ~60 g (ficha) | (verificar) | **Candidato para yaw final**: da ±70° con ≈ 960 / 2040 µs |

Pares tomados de fichas de vendedores. Hay que comprobarlos con las pruebas, no darlos por buenos.

**Por qué el SM-S4315R no sirve:** en un servo de rotación continua el pulso controla la **velocidad**, no la posición. Con 1500 µs se queda quieto, y con otros pulsos gira sin parar. No tiene realimentación de ángulo, así que no puede mantener la cabeza en un ángulo. La prueba 1 lo confirma: si gira sin detenerse, es de rotación continua. (El modelo de posición equivalente es el SM-S4315**M**.)

**Asignación:**
- **Pitch → HS-7955TG** (caracterizado el 09/10, ver la planilla), el de más par, porque pitch es el eje que carga contra la gravedad. Su cuerpo va montado sobre la plataforma de yaw.
- **Yaw → RDS3218 n.º 2** (caracterizado el 12/10; en `config.yaml`): versión de 270°, asimétrico 0,13 / 0,136 °/µs, ±70° con ≈ 960 / 2010 µs, banda muerta ≤ 2 µs hacia abajo y 4–6 µs hacia arriba, sin holgura. **No tiene tope**: los límites del firmware (950 / 2020 µs) son lo único que protege el cableado. Sin pulso mantiene la posición. El n.º 1 (simétrico, 0,13 °/µs, 950 / 2050 µs) queda de repuesto: **no son intercambiables sin recalibrar**. Marcar cada uno con cinta. Reemplaza al MG90S, que también queda de repuesto. Con el eje vertical la gravedad no le hace par, pero el **rodamiento** tiene que soportar el peso y el vuelco de lo que va arriba.
- **Roll → RDS3218 n.º 1** (desde el 12/10; antes, SG90, que queda de repuesto). Vibración del roll (12/10): solo anda bien (también a `v 1500`, ±45°); vibra (≈ 0,5 A) cuando el HS-7955TG está conectado **y recibe pulso**. No vibra con el HS conectado sin pulso, ni con el GPIO1 mandando pulsos sin el HS. No es el pin (pasa igual en GPIO3 y GPIO4) ni la señal del GPIO1. El RDS n.º 2 **no** vibra con el HS activo, y el n.º 1 vibró una vez estando solo: el n.º 1 tiene poco margen (¿potenciómetro gastado?) y el ruido de alimentación del HS lo dispara. **Confirmado intercambiando los RDS** (n.º 1 en GPIO0, n.º 2 en GPIO4, `v 1500`, 1300 ↔ 1700 µs): la vibración (≈ 0,5 A) **sigue al n.º 1**. Se calma si se lo lleva a 1300 µs. **El n.º 1 queda descartado para el robot.** Con el HS (GPIO0) y el n.º 2 (GPIO4) juntos a `v 1500`, el pulso del HS en espejo: sin vibración y sincronizados. Remedio previsto: capacitor de 1000–2200 µF + 100 nF cerca de los servos, GND en estrella y, si no alcanza, otro canal de fuente para el HS (GND común). Lo que sigue es lo que se evaluó para el SG90: Roll pide poco par si el eje pasa cerca del centro de gravedad de la cabeza (≈ 0,15 kgf·cm para 150 g a 1 cm, según `docs/REVISION_CODEX_HW.md`). Es liviano, lo que alivia a pitch y yaw. Engranajes plásticos: tratarlo con cuidado y tener repuesto.

## Conexionado

```
 FUENTE 6 V (+) ──── BORNERA V+  ──┬── rojo YAW ──┬── rojo PITCH ──┬── rojo ROLL
                                   │                  
                              C 2200 µF ≥10 V (+ a V+, − a GND)
                                   │
 FUENTE 6 V (−) ──── BORNERA GND ──┴── negro/marrón de cada servo
                                   └── GND de la ESP32-C3   (masa común)

 ESP32-C3-DevKitM-1                         señal (amarillo/naranja)
   GPIO0 ──[330 Ω]──────────────────────── servo YAW   (falta servo)
   GPIO1 ──[330 Ω]──────────────────────── servo PITCH (HS-7955TG)
   GPIO4 ──[330 Ω]──────────────────────── servo ROLL  (RDS3218 n.º 1)
   GND   ───────────────────────────────── bornera GND
   USB   ───────────────────────────────── notebook (alimenta SOLO a la ESP32)
```

| ESP32-C3 | Va a | Notas |
|---|---|---|
| GPIO0 | señal de yaw | fila de abajo de la placa |
| GPIO1 | señal de pitch | fila de abajo |
| GPIO4 | señal de roll | fila de los pines 4–9, entre un GND y el GPIO5. Hasta el 12/10 era GPIO3: con los tres servos moviéndose, el roll temblaba |
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

## Manejar la prueba desde la terminal

Abrir el monitor serie en la notebook (`arduino-cli` ya está instalado):

```bash
~/.local/bin/arduino-cli monitor -p /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 -c baudrate=115200
```

- Se escribe un comando y se aprieta **Enter**. **Ctrl+C** para salir.
- Usar la ruta `by-id` y no `/dev/ttyUSB0`: si la ESP32 se desconecta, al volver puede aparecer como `ttyUSB1`.
- Al abrir el monitor la ESP32 se reinicia y pierde el eje elegido: empezar siempre con `e <eje>`.
- Un solo programa por vez en el puerto. Si dice que está ocupado: `fuser -v /dev/ttyUSB*` muestra quién lo tiene.

| Comando | Qué hace |
|---|---|
| `e 0` / `e 1` / `e 2` | Elige el eje: GPIO0 (yaw) / GPIO1 (pitch) / GPIO4 (roll) |
| `c` | Va al centro (1500 µs) |
| `p <us>` | Va a ese pulso con rampa (recortado a los límites) |
| `+` / `-` | Mueve 10 µs (≈ 1°) |
| `v <us/s>` | Velocidad de la rampa: 300 ≈ 27 °/s, 700 ≈ 60 °/s, 1300 ≈ 117 °/s, 3000 es rápido |
| `l <min> <max>` | Límites del eje (por defecto 1000–2000; hasta 500–2500) |
| `b <us1> <us2>` / `s` | Barrido de ida y vuelta / lo detiene |
| `o` / `O` | Apaga el pulso de este eje / de todos |
| `?` / `h` | Estado de los ejes / ayuda |

Secuencia rápida para un servo nuevo:

```
e 0
v 700
c                 ← marcar 0°
p 1600            ← ¿va a ~9° y se queda? (si gira sin parar es continuo: o)
p 1200   p 1800   ← ¿27° a cada lado?
p 1000   p 2000   ← ¿45°? → grados/µs
```

Lo que aprendimos en las pruebas del 09/10:
- **Apagar la fuente antes de cambiar de servo.** Enchufar uno con la fuente prendida desconectó la ESP32 del USB.
- Fuente: **6 V** para el HS-7955TG y **5 V** para los micro (MG90S, SG90), con límite de corriente ~3 A y ~1 A.
- **Antes de conectar un servo desconocido, girarlo a mano sin alimentación:** si da vueltas completas sin tope, es de rotación continua (o está roto) y no sirve como articulación.
- Si un servo barato zumba sin moverse con `v 300`, probar con `v 1500`: con pasos muy chicos, a veces el motor no arranca.
- Para buscar los extremos: de a 100 µs hasta 900/2100, después de a 50. Los Hitec tienen límite electrónico (dejan de moverse sin forzar); los micro pueden tener tope mecánico.
- La banda muerta de los micro se nota poco con el oído: pegar una tira de papel larga al brazo como puntero.

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
10. **Velocidad del robot:** `v` con el límite del eje en `config.yaml` (yaw `v 2000`, pitch `v 1300`, roll `v 1000`) y `b 1300 1700`. ¿Se mueve parejo y frena limpio en los extremos?
11. **Sin señal:** `p 1700`, después `o`, y empujar el brazo con suavidad. ¿Queda flojo o mantiene la posición con fuerza? Define qué hace el firmware en el STOP.
12. **Encendido:** fuente apagada, brazo a mano a −30/−40°, prender la fuente sin pulso (¿se mueve solo?) y después `c` (¿qué tan brusco va al centro?).

Después, los tres juntos con `b` en los tres ejes: medir la tensión en la bornera mientras se mueven. Tiene que mantenerse ≥ 5,5 V con fuente de 6 V. Si la ESP32 o la Pi se reinician, hay un problema de masa o de fuente.

## Planilla de resultados

Completar una columna por servo. Estos datos van después a la calibración del firmware (centro, límites y sentido por eje).

| Medida | HS-7955TG | MG90S (5 V) | SG90 (5 V) | SM-S4315R | RDS3218 n.º 1 | RDS3218 n.º 2 |
|---|---|---|---|---|---|---|
| Fecha / quién | 09/10, Héctor + Claude por serie | 09/10, Héctor + Claude por serie | 09/10, Héctor + Claude por serie | | 11–12/10, Héctor + Claude por serie | 12/10, Héctor + Claude por serie |
| ¿Posición o continuo? | Posición. Sentido (12/10): pulso mayor = **horario** visto de frente al eje, al revés que los dos RDS3218 (comparado lado a lado con el n.º 2, 1500 → 1700 µs) | Posición. Sentido (12/10, 6 V): pulso mayor = antihorario visto de frente al eje (550 µs → horario, 2450 µs → antihorario), como los RDS3218 | Posición | **Continuo** (09/10: quieto con 1500 µs, gira sin parar con 1600 µs y hacia el otro lado con 1400 µs; con 1500 µs y pulso activo, si se lo gira a mano se queda donde lo dejan). No sirve como articulación | Posición (11/10: con `p 1600` y `p 1400` se movió un poco y se quedó quieto). Con el sketch de grados (`prueba_grados/`) va a cada ángulo de 0 a 180 (527–2382 µs). Sin alimentación el eje gira libre: en este modelo no indica falla. Sentido (12/10): pulso mayor = antihorario visto de frente al eje | Posición (`p 1600` → +13° y quieto). Sentido: pulso mayor = antihorario visto desde arriba |
| Pulso del centro (µs) | 1500 (marcado como 0°) | 1500 (marcado como 0°) | 1500 (el brazo queda algo inclinado por las estrías: corregir al montar) | — | 1500 (marcado como 0°) | 1500 (el brazo no queda derecho por las estrías; se marcó el 0° donde quedó) |
| Extremo seguro mín / máx (µs) | 750 / 2250 (≈ −68° / +68–70°). Son límites **electrónicos**: con 700 o 2300 µs no se mueve más y no fuerza. En el firmware: 760 / 2240 | No se encontró tope: 500 µs ≈ −97° y 2450 µs ≈ +80° sin zumbar. En el firmware: 600 / 2450 (−81° / +80°) | No se buscaron los topes (engranajes plásticos; roll pide ±20°). Probado hasta 1000 / 2000 µs. En el firmware: 1000 / 2000 | — | No se encontró tope ni límite: 500 µs ≈ −143° y 2500 µs ≈ +145° (recorrido ≈ 288°). Para yaw (±70°): ≈ 960 / 2040 µs | No se encontró tope ni límite: 500 µs ≈ −130° y 2500 µs ≈ +140° (recorrido ≈ 270°), sin ruido. Para yaw (±70°): ≈ 960 / 2010 µs (con 2040 µs llega a +75°) |
| Pulso a −45° / +45° (µs) | 1000 / 2000 | 1000 / ~2050 | 1000 / 2000 | — | ≈ 1145 / 1846 (interpolado) | ≈ 1154 / 1843 (interpolado) |
| Grados por µs | **0,090**, lineal en todo el recorrido (27° en 1200 y 1800, 36° en 1100 y 1900, 54° en 900 y 2100). Recorrido total ≈ 137° | **Asimétrico:** 0,090 en el lado − (lineal hasta 600 µs; de 550 a 500 se estira) y ~0,085 en el lado + (40° en 2000, 59° en 2200, 68° en 2300, 76° en 2400). ±70° ≈ 722 / 2324 µs. Recorrido ≥ 177° | **0,090**, simétrico (27° en 1200 y 1800, 45° en 1000 y 2000) | — | **0,13** entre 1000 y 2000 µs, simétrico (−37,5° en 1200, +39° en 1800, ±65° en 1000 y 2000); hacia los extremos sube a 0,15–0,16 (−94,5° en 800, −113° en 700, −127° en 600; +93,5° en 2200, +113° en 2300, +130° en 2400) | **0,13** en el lado − (−39° en 1200, −65° en 1000, −70° en 960); **≈ 0,14** en el lado + (+13° en 1600, +39° en 1800, +65–70° en 2000, +75° en 2040). Hacia los extremos: lado − **se aplana** a 0,085 (−113° en 700, −122° en 600, −130° en 500); lado + +113° en 2300, +140° en 2500. **No es intercambiable con el n.º 1 sin recalibrar** |
| Banda muerta (µs) | ≤ 2 en los dos sentidos (responde a 1500→1502 y a 1502→1500) | 20–30 en los dos sentidos (≈ 2–2,5°; la hoja dice 5) | 10–20 en los dos sentidos (≈ 1–2°) | — | ≤ 2 (responde a 1500→1502; medido solo hacia arriba, con una tira de papel como puntero) | Hacia abajo ≤ 2 µs (1500→1498); hacia arriba 4–6 µs (1500→1504 no, 1500→1506 sí) ≈ 0,5–0,8°. Medido con tira de papel |
| Holgura (°) | ≤ 1 (1600 µs desde 1400 y desde 1800) | No se nota (1600 µs desde 1400 y desde 1800) | No se nota (1600 µs desde 1400 y desde 1800) | — | No se nota (1600 µs desde 1400 y desde 1800) | No se nota (1600 µs desde 1400 y desde 1800: misma marca) |
| Corriente reposo / barrido (mA) | 6 / 150 (v 300) – 200–450 (v 1300, ±18°) | 1 / 120 (v 300) – 60–160 (v 2000, ±18°) | 1 / 55 (v 300) – ~100 (v 1000, ±18°) | | (sin medir) | ? / ~80 media, 100 máx (v 300, ±39°) – picos de **~1 A** a `v 2000` (±26°, en las aceleraciones) |
| Temperatura tras 5 min | Frío (`b 1200 1800` a `v 300`) | Frío (`b 1200 1800` a `v 300`) | Frío (`b 1200 1800` a `v 300`) | | (sin medir) | Frío (`b 1200 1800` a `v 300`, 5 min) |
| ¿Zumba en reposo? | No: silencio en el centro | No: muy silencioso, incluso en los extremos | No: silencioso | | (sin verificar) | No: silencio en el centro |
| Observaciones | A 117 °/s (`v 1300`) se mueve parejo y frena limpio; a `v 3000` es rápido. Ruido de engranajes continuo al moverse lento, sin golpes periódicos. **Sin pulso mantiene la última posición con fuerza** (pita y consume 0,15–0,22 A si se lo empuja): apagar el pulso no lo afloja. Al prender la fuente sin pulso no se mueve; el primer pulso lo lleva a la posición a velocidad máxima (58° rápido, sin pasarse) | A 180 °/s (`v 2000`) parejo y frena limpio. **Sin pulso queda flojo** (al revés que el HS): en el STOP el firmware tiene que seguir mandando el último pulso. Al prender la fuente sin pulso no se mueve; el primer pulso lo lleva a la posición rápido, sin pasarse | A 90 °/s (`v 1000`) parejo y frena limpio. **Sin pulso queda flojo**: en el STOP hay que seguir mandando el último pulso. Al prender la fuente sin pulso da un tirón de pocos grados (normal en servos analógicos baratos): encender con la cabeza cerca del centro | | Probado con `v 700` (≈ 90 °/s). **Sin pulso mantiene la posición con fuerza**, como el HS-7955TG: el STOP/watchdog lo congela, no lo afloja. Sin alimentación el eje gira libre. Es de los dos de la pinza del recolector | A `v 2000` (≈ 260 °/s) parejo, frena limpio, no rebota. Ruido de engranajes normal al moverse. **Sin pulso mantiene la posición con fuerza**, igual que el n.º 1. Sin alimentación gira libre; al prender la fuente sin pulso no se mueve; el primer pulso lo lleva directo a la posición, sin pasarse. Es el segundo de la pinza del recolector |

## Rangos que tiene que cubrir cada eje (enunciado)

| Eje | Rango mínimo | Recorrido total |
|---|---|---|
| Yaw | ±70° | 140° |
| Pitch | −20° / +30° | 50° |
| Roll | ±20° | 40° |

Recorrido de un servo = (extremo máx − extremo mín) × grados por µs. Yaw es el que más recorrido pide: si un servo no llega a 140° entre sus extremos seguros, **no puede ir en yaw**. Muchos servos estándar dan solo ~90–120° entre 1000 y 2000 µs, así que hay que medirlo.
