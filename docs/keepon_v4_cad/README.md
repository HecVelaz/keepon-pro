# Keepon pro v4: cabeza de la v3 + cuello de la v1 + baterías en la base

- **De la v3** (`../keepon_v3_cad/`): la cabeza completa (Pi 5 parada adentro, cámara-nariz, ojos, cinta con la U y el doblez en Z), los tres servos, los soportes de pitch, la horquilla y los brazos dobles. Son las mismas piezas, sin cambios.
- **De la v1** (`../keepon_mg996r_step/`, `cuerpo.png`): la disposición de los motores. Es una columna compacta: el yaw vertical en la base, una **base en U** sobre su brazo, y **el eje de pitch justo encima del eje de yaw**. En la v3 el pitch estaba 20 mm adelante, sobre un plato de Ø146.
- **Nuevo:** la caja base lleva las dos baterías: la **LiPo Zeee** para los servos y el **powerbank Xiaomi** para la Pi. Adelante, en una bahía, van el regulador de 6 V, la ESP32 y el buzzer.

![frente](vistas/01_frente_iso.png)

## Medidas

| | v3 | v4 |
|---|---|---|
| Altura total | 223,5 mm | 223,5 mm |
| Caja base (con tapa) | 200 × 190 × 74 mm | **182 × 133 × 74 mm** |
| Plataforma de yaw | plato Ø146 (57 cm³) | **base en U de 64 × 116 mm** (26 cm³) |
| Eje de pitch respecto del de yaw | 20 mm adelante | **encima** (como la v1) |
| Carga sobre el eje del yaw (sin rodamiento) | 326 g a 39 mm → 1,26 kgf·cm | **295 g a 28 mm → 0,81 kgf·cm** |
| Cabeza | 75 × 104 × 40 mm | igual |

Con el pitch sobre el yaw, el centro de masa de lo que gira queda más cerca del eje: el momento de vuelco sobre el RDS3218 baja un 35 %. Como no hay rodamiento, es la mejora más importante para el yaw.

## Base

![interior de la base](vistas/05_base_interior.png)

Vista de arriba (+X es la cara del robot):

```
 atrás (−X)                                                  adelante (+X)
 ┌──────────────────────────────────────────────────┬──────────────────┐
 │ [interruptor]                                    │ ESP32 (parada)   │ ← buzzer en la pared
 │  POWERBANK XIAOMI 128 × 73 × 32 (5 V → Pi)       │ bornera USB-C    │   (agujeros de sonido)
 │                    ┌──────┐                      ├──────────────────┤
 │─ ─ ─ ─ tabique ─ ─ │ YAW  │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │ REGULADOR 6 V    │
 │  LiPo ZEEE 138 × 47│RDS3218 (cuelga de la tapa)  │ (parado, rieles) │ ← ranuras de
 │  × 36 (→ servos)   └──────┘   ○ paso de cables   │                  │   ventilación
 └──────────────────────────────────────────────────┴──────────────────┘
```

- **Baterías acostadas** contra la pared de atrás, lado a lado, con un tabique entre las dos y topes adelante. Se fijan con velcro adhesivo en el piso.
- **El servo de yaw cuelga de la tapa** (con la brida por debajo, como en la v3) y queda **2,5 mm por encima de la LiPo**.
- **Bahía de adelante:**
  - el **regulador de 6 V** va parado entre dos rieles, con el disipador hacia arriba y ranuras de ventilación en los dos costados;
  - la **ESP32** va parada en `porta_esp32`, tomada de los extremos cortos para que los pines queden libres, con un paso para el micro-USB;
  - la **bornera USB-C** del powerbank;
  - el **buzzer**, en un aro de la pared de adelante con 5 agujeros para el sonido.
- **Pared de atrás:** el interruptor (corte de 19,2 × 12,8), por encima del powerbank. **Pared izquierda:** una ranura frente al powerbank para su cable y su botón.
- **Tapa:** 4 tornillos M3 a columnas que cuelgan de las esquinas, por encima de las baterías y del regulador. Para cargar la LiPo hay que sacar la tapa: el balanceador queda adentro.

## Alimentación

```
 LiPo Zeee 3S (11,1 V) ─ Deans ─ fusible 10 A ─ interruptor ─ regulador 6 V ─┬─ RDS3218 (yaw)
                                                                             ├─ HS-7955TG (pitch)
                                                     2200 µF + 100 nF ───────┼─ MG996R (roll)
                                                                             └─ GND ─┐
 Powerbank Xiaomi ─ USB-C ─ bornera ─ 5 V / GND (20 AWG) ─▶ GPIO 2/4 y 6 de la Pi 5   │ GND común
                                                                                      │ (por la ESP32)
 Pi 5 (cabeza) ─ USB-A ─▶ micro-USB de la ESP32 (base) ─ GPIO0/1/4 ─ señales ─────────┘
                                                        └ GPIO10 ─ 2N2222 ─ buzzer
```

- **Pi 5 con el powerbank:** el puerto USB-C de la Pi queda tapado por la cinta (como en la v3), así que entra **por el GPIO** (5 V en los pines 2 y 4, GND en el 6). El powerbank da 5 V / 3 A por puerto sin negociar PD: la Pi arranca, avisa que la fuente no es de 5 A y **limita los USB a 600 mA**. Eso alcanza para la ESP32. La Pi consume ~7 W típico y 12 W de pico, unos 2,4 A: entra en los 3 A.
  - Duración estimada: 20 000 mAh × 3,7 V ≈ 74 Wh; con ~65 Wh útiles a 5 V y 7 W, **unas 9 h**.
  - Usar 20 AWG de la base a la cabeza (≈ 0,8 m ida y vuelta: ≈ 0,08 V de caída a 3 A). Medir que lleguen ≥ 4,9 V a los pines con la percepción corriendo.
- **Servos con la LiPo:** el regulador de 6 V (módulo de 20 A) alimenta los tres servos. Los 3 juntos trabados piden hasta ~12 A; en uso normal, 2–3 A. Duración: 8000 mAh × 11,1 V ≈ 89 Wh, sobra para la demo.
- **GND común:** el negativo de la LiPo (bus de 6 V) se une al GND de la ESP32. Sin GND común, los servos no se mueven. La Pi y el powerbank quedan unidos a esa masa por el USB.
- Alarma de tensión en el balanceador de la LiPo (pita si una celda baja de ~3,5 V).

## Cableado por las articulaciones

| Articulación | Qué cruza | Cómo |
|---|---|---|
| **Yaw** (±70°) | 5 V + GND de la Pi (20 AWG), USB Pi → ESP32, cables de servo del HS y del MG996R (3 + 3 hilos) | Pasan por el **paso fijo de la tapa** (Ø10, a 26 mm del eje, hacia −Y) y por la **ranura en arco de la base en U** (±72°), que siempre queda sobre el paso. Adentro de la caja, dejar un bucle de ~10 cm por encima de la LiPo para los ±70°. El cable del RDS3218 ya está adentro. |
| **Pitch** (−20/+30°) | Lo mismo menos el HS, que es fijo al soporte izquierdo | Bajan por detrás de la horquilla, por la ventana de su piso, con un bucle de servicio cerca del eje de pitch. |
| **Roll** (±20°) | 5 V + GND de la Pi y USB a la ESP32 (salen de la cabeza) | Bucle alrededor del brazo del MG996R. |
| Dentro de la cabeza | Cinta de la cámara | **No cruza ninguna articulación**: la Pi y la cámara giran juntas (U + doblez en Z, ver la v3). |

## Uniones

| Unión | Elementos |
|---|---|
| Tapa → caja | 4 × M3 × 16 autorroscantes a las columnas |
| RDS3218 → tapa | 4 × M3 + tuerca (brida por debajo de la tapa) |
| Base en U → brazo del yaw | 2 × M2 × 8 autorroscantes por las ranuras + el tornillo central del servo |
| Soportes de pitch → base en U | 2 × M3 + tuerca cada uno |
| HS-7955TG → soporte izquierdo | 4 × M3 + tuerca |
| Horquilla → brazo del HS | 2 × M2 × 8 por las ranuras + el central |
| Horquilla → soporte derecho | Pivote M4 × 20 con 2 arandelas y tuerca autofrenante |
| MG996R → horquilla | 4 × M3 + tuerca |
| Placa de roll → brazo del MG996R | 2 × M2 × 8 por las ranuras + el central |
| Pi 5 → placa de roll | 4 × M2,5 × 6 |
| Caja de la cabeza → placa de roll | 4 × M2,5 × 12 desde atrás |
| Cámara → cara | 4 × M2 × 5 a los separadores; nariz y ojos pegados |
| Regulador, ESP32, baterías | Rieles, `porta_esp32` y topes impresos; velcro debajo de las baterías |

## Orden de montaje

1. Caja: velcro y baterías (los conectores hacia la bahía), regulador entre los rieles, `porta_esp32` con la ESP32, buzzer en su aro, interruptor en la pared de atrás. Cablear la potencia (ver arriba).
2. Tapa: atornillar el RDS3218 por debajo y llevar su cable a la ESP32. Pasar los cables que suben por el paso de la tapa y cerrar la caja.
3. Base en U al brazo del yaw (con el servo centrado en 1500 µs y la U mirando al frente), y los soportes de pitch a la U.
4. HS-7955TG al soporte izquierdo; horquilla con el MG996R al brazo del HS y al pivote M4.
5. La cabeza, como en la v3: placa de roll al brazo del MG996R, Pi, cinta (U + doblez en Z), cámara y caja de la cabeza.

## Verificado con el script

```bash
cd docs/keepon_v4_cad/fuente
~/cq_env/bin/python keepon_v4_cad.py --verificar   # STEP, STL, macro, lista de componentes, interferencias
~/cq_env/bin/python vistas.py                      # vistas/*.png
```

- **Sin interferencias** en la pose 0, en 15 poses de pitch × roll (pitch −32 / −16 / +11 / +22, roll −22 / 0 / +22) y con el yaw en ±70° con la nariz abajo.
- **Holgura mínima: 2 mm** (la horquilla contra el soporte derecho, igual que en la v3). La base en U se recortó adelante (x ≤ 32 mm) para que la cabeza no la toque con la nariz abajo y roll.
- El servo de yaw queda 2,5 mm por encima de la LiPo.

## SolidWorks

- `step/keepon_v4_ensamble.step`: el ensamble completo. Cada pieza impresa está en `step/` y `stl/`, y cada componente en `step/componentes/`.
- **Relaciones de posición:** la misma macro que en la v3, con las bisagras de la v4: `solidworks/keepon_v4_relaciones_PEGAR.txt`. Abrir el STEP, guardarlo como `.SLDASM` sin mover nada, pegar el texto en el editor de VBA y ejecutar `main`.
- `componentes_v4.txt`: todas las piezas con sus medidas, más la tornillería y los cables.

## Medir antes de imprimir

| Qué | Valor usado |
|---|---|
| Powerbank Xiaomi | 128 × 73 × 32 mm (aproximado, según la ficha) |
| LiPo Zeee | 138 × 47 × 36 mm (ficha) |
| Regulador de 6 V | 65 × 50 × 25 mm (parado: 25 × 65 × 50) |
| Lo de la v3 | Cinta, cooler, brazo de los servos y salida de la cinta (ver `../keepon_v3_cad/README.md`) |

## Pendiente

- Probar la macro de relaciones en SolidWorks.
- Medir la tensión en los pines de la Pi con el powerbank y la percepción corriendo.
- Con el robot armado, comprobar que la base en U no cabecee: el yaw sigue sin rodamiento, aunque ahora con un 35 % menos de vuelco.
