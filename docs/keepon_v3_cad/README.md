# Keepon pro v3: cabeza plana con la Pi adentro

La Pi 5 va **parada dentro de la cabeza**, atornillada a la placa de roll, y la cámara en uno de los ojos. La Pi y la cámara se mueven juntas, así que la cinta de 150 mm **no se dobla ni se tuerce con ningún movimiento** (yaw, pitch ni roll): queda fija con una sola curva en U. Es lo que recomendó la revisión de Codex (`docs/REVISION_CODEX_ARQ.md`, sección 2).

El cuello es el de la v2 (`../keepon_v2_cad/`): mismos servos, caja base, tapa, soportes de pitch y horquilla. El script importa esas piezas.

## Medidas

| | v2 | v3 |
|---|---|---|
| Cabeza | esfera Ø165 | **75 × 107 × 40 mm** (ancho × alto × fondo) |
| Cuerpo | elipsoide Ø200 | no tiene |
| Plato de yaw | Ø180 | Ø146, cortado adelante (forma de D) |
| Altura total | ≈ 240 mm | ≈ 227 mm |
| Volumen a imprimir | ≈ 850 cm³ | ≈ 630 cm³ (450 son la caja base y la tapa) |
| Cabeza impresa | 145 cm³ (+ 100 del cuerpo) | 71 cm³ |

Cabeza armada: unos 160 g (70 de la Pi con el cooler). El centro de masa queda unos 55 mm delante del eje de pitch: ≈ 0,9 kgf·cm para el HS-7955TG (da ~18). En roll queda casi centrado.

## La cinta

```
   cámara (ojo)          La Pi va parada, con los componentes hacia la cara.
   ┌──┐                  La cinta sale del conector hacia abajo, baja pegada a la Pi
   │  │← entra desde     (pasa por encima de los micro-HDMI y del USB-C), da una U de
   └┬─┘  abajo           radio 6,5 mm debajo de la Pi y sube por delante hasta la cámara.
    │      ┌─┐
    │      │P│← conector  Recorrido + inserciones: 147 mm de 150. Sobran 3 mm, para no
    │      │i│   CSI      tirar de los conectores.
    │      │ │
    ╰──U───╯ │
```

- **Sin torsión ni dobleces de costado:** en el plano de la Pi 5 (`raspberry-pi-5-mechanical-drawing.pdf`), los conectores CAM/DISP están **perpendiculares** al borde de los HDMI. La cinta sale a lo largo del lado largo, con su ancho a lo largo del corto. Por eso la Pi va parada (con el lado largo vertical) y la cámara está corrida 19 mm hacia el costado, alineada con la cinta: es el ojo izquierdo del robot (el derecho visto de frente).
- La U es estática: la cinta nunca se mueve. 6,5 mm de radio es mucho para una FFC quieta.
- El largo de la cinta **ubica la cámara**: si `FFC_LARGO` cambia, el script mueve la cámara (y la cabeza) solo.
- La U queda a la vista por la abertura de abajo de la cabeza: se puede revisar sin desarmar.

## Antes de imprimir: verificar en la Pi y medir con calibre

| Parámetro | Valor usado | Qué hacer |
|---|---|---|
| `PI_CSI_SALIDA` | `"usbc"` | **Mirar en la Pi hacia qué extremo sale la cinta** del conector: el del USB-C o el del Ethernet. Si es el del Ethernet, cambiarlo a `"ethernet"`: la Pi se da vuelta y la cámara sube ~12 mm. |
| `PI_CSI_U` | 48,5 mm desde el extremo del USB-C | El conector usado (el más cercano a los HDMI). El otro está en 54,3. |
| `FFC_LARGO` | 150 mm | Medir la cinta de punta a punta. |
| `COOLER_H` | 11 mm | Altura del Active Cooler sobre la placa. |
| Cámara | lente a 14,5 mm del borde de abajo, agujeros 21 × 12,5 | Camera Module 3 NoIR estándar. |
| Servos (`Fb`, `S`, `a`) | los de la v2 | Ver `../keepon_v2_cad/README.md`. |

## Alimentación y cables de la Pi

- **El USB-C queda abajo, pegado a la U de la cinta: no se puede enchufar.** La Pi se alimenta por el GPIO: 5 V en los pines 2 y 4, GND en el 6. Hace falta una fuente de 5,1 V y ≥ 3 A bien regulada, porque el GPIO no tiene la protección del USB-C. La pared del lado del GPIO tiene una abertura para los cables.
  - Sin USB-C, la Pi limita los USB a 600 mA. La ESP32 consume mucho menos, así que no hace falta tocar `config.txt`.
- **Los USB-A quedan arriba.** La pared de arriba está abierta sobre ellos. Para la ESP32 conviene un cable USB-A acodado.
- Los cables que bajan de la cabeza (5 V, USB a la ESP32) son redondos. Dejarles un bucle de servicio en roll (alrededor del horn), en pitch (cerca del eje) y en yaw (la espiral dentro de la caja, como en la v2).

## Piezas impresas (`step/` y `stl/`)

| Pieza | Volumen | Cómo imprimirla |
|---|---|---|
| `caja_cabeza` | 39 cm³ | Apoyada sobre la cara, sin soportes |
| `placa_roll` | 30 cm³ | Plana; los separadores de la Pi hacia arriba |
| `ojo_camara`, `ojo_otro` | 1 + 1 cm³ | En negro, con el bisel apoyado en la cama |
| `plato_yaw` | 57 cm³ | Plano |
| `cuna_esp32`, `porta_buzzer` | 7 + 1 cm³ | Como en la v2 |
| `soporte_pitch_izq/der`, `horquilla_cabeza` | 10 + 13 + 26 cm³ | Las mismas de la v2 |
| `caja_base`, `tapa_base` | 285 + 164 cm³ | Las mismas de la v2 (o MDF de 3 mm) |

`keepon_v3_ensamble.step` es el ensamble completo para SolidWorks (*Archivo → Abrir*, tipo STEP).

## Orden de montaje

1. Cuello como en la v2: plato con la ESP32, el buzzer y los soportes; HS en el soporte izquierdo; horquilla con el MG996R.
2. `placa_roll` al horn del MG996R (los tornillos del horn quedan debajo de la Pi: van antes).
3. La Pi parada sobre los separadores (4 × M2,5 × 6), la cinta conectada a la Pi.
4. La cámara a los separadores de `caja_cabeza` (4 × M2) y los ojos pegados. Conectar la cinta a la cámara.
5. `caja_cabeza` sobre la placa: 4 × M2,5 × 12 autorroscantes desde atrás, por la placa, a las costillas.

## Verificado con el script

```bash
cd docs/keepon_v3_cad/fuente
~/cq_env/bin/python keepon_v3_cad.py --verificar   # STEP, STL, interferencias y holguras
~/cq_env/bin/python vistas.py                      # vistas/*.png (VTK, sin errores de oclusión)
```

- **Sin interferencias** en 15 poses: pitch −32 / −16 / 0 / +11 / +22 × roll −22 / 0 / +22 (pitch > 0 es nariz abajo).
- **Holgura mínima de la cabeza contra lo fijo:** 3 mm con el plato, en el peor caso (nariz abajo 22° + roll 22°, más que lo que pide `config.yaml`). Sin roll: 6 mm. Con la nariz arriba 32°: ≥ 14 mm.
- **El pitch se monta con los 30° hacia arriba y los 20° hacia abajo** (`config.yaml`: −20/+30). La persona está más alta que el robot, y hacia abajo la holgura con el plato se termina poco después de los 22° (con roll). Al definir `signo` del pitch, que "arriba" sea el lado de los +30°.

## Pendiente

- Confirmar `PI_CSI_SALIDA` y medir lo de la tabla de arriba antes de imprimir.
- El cooler toma aire de adelante (16 mm hasta la cara) y lo saca por los costados. Medir la temperatura de la Pi con la cabeza cerrada y la percepción corriendo (`vcgencmd measure_temp` no está en Ubuntu: usar `cat /sys/class/thermal/thermal_zone0/temp`).
- La imagen no necesita rotarse (la cámara va derecha), pero la lente no está sobre el eje de roll: queda 19 mm al costado y 57 mm arriba. El control de mirada usa ángulos de la imagen, así que no cambia nada; solo hay que tenerlo en cuenta al calibrar.
- El alto de 107 mm lo fija la Pi parada (85 mm + la U de la cinta + la cámara). Para algo más bajo haría falta otra cinta (más corta, o una que permita poner la Pi acostada).
