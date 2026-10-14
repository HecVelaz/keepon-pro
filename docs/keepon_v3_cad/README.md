# Keepon pro v3: cabeza plana con la Pi adentro

La Pi 5 va **parada dentro de la cabeza**, atornillada a la placa de roll, y la cámara es **la nariz**, en el centro de la cara, con los dos ojos (decorativos) arriba. La Pi y la cámara se mueven juntas, así que la cinta de 150 mm **no se dobla ni se tuerce con ningún movimiento** (yaw, pitch ni roll): queda fija con una sola curva en U. Es lo que recomendó la revisión de Codex (`docs/REVISION_CODEX_ARQ.md`, sección 2).

El cuello es el de la v2 (`../keepon_v2_cad/`): mismos servos, caja base, soportes de pitch y horquilla. El script importa esas piezas. La diferencia es que **la v3 no lleva rodamiento de yaw** (no tenemos uno): la tapa y el plato son propios de la v3 (ver "Yaw sin rodamiento").

## Medidas

| | v2 | v3 |
|---|---|---|
| Cabeza | esfera Ø165 | **75 × 104 × 40 mm** (ancho × alto × fondo) |
| Cuerpo | elipsoide Ø200 | no tiene |
| Plato de yaw | Ø180 | Ø146, cortado adelante (forma de D) |
| Altura total | ≈ 240 mm | ≈ 227 mm |
| Volumen a imprimir | ≈ 850 cm³ | ≈ 630 cm³ (450 son la caja base y la tapa) |
| Cabeza impresa | 145 cm³ (+ 100 del cuerpo) | 71 cm³ |

Cabeza armada: unos 160 g (70 de la Pi con el cooler). El centro de masa queda unos 55 mm delante del eje de pitch: ≈ 0,9 kgf·cm para el HS-7955TG (da ~18). En roll queda casi centrado.

## La cinta

```
   de costado                      de frente (tramo que sube por delante de la Pi)
   cámara (nariz)
   ┌──┐                              ┌──┐ cámara, en y = 0
   │  │← entra desde abajo           └┬─┘
   └┬─┘                               │  tramo 2 (y = 0)
    │      ┌─┐                   ┌────┘  ← pliegue a 45°
    │      │P│← conector CSI     │ ← tramo horizontal: 19 mm al centro
    │      │i│                   └────┐  ← pliegue a 45°
    │      │ │                        │  tramo 1 (y = 19, alineado con el conector)
    ╰──U───╯ │                        U
```

La cinta sale del conector hacia abajo, baja pegada a la Pi (pasa por encima de los micro-HDMI y del USB-C), da una U de radio 6,5 mm debajo de la Pi y sube por delante. A media altura, un **doblez en Z** (dos pliegues a 45°) la corre 19 mm al centro, y sigue subiendo hasta la cámara. Recorrido + inserciones: 147 mm de 150 (sobran 3 mm, para no tirar de los conectores).

- **Por qué hace falta el doblez:** en el plano de la Pi 5 (`raspberry-pi-5-mechanical-drawing.pdf`), los conectores CAM/DISP están **perpendiculares** al borde de los HDMI. La cinta sale a lo largo del lado largo, con su ancho a lo largo del corto, corrida 19 mm del centro. Para que la cámara sea la nariz, en el centro de la cara, hay que correr la cinta esos 19 mm.
- **Cómo plegarla:** con la cinta conectada a la Pi y pasada por la U, marcar la altura del primer pliegue (`Z_DOBLEZ`, ≈ 2 mm debajo del eje de roll) y doblarla a 45° hacia el centro, apretando con el dedo, sin uñas ni pinzas. A 19 mm, doblarla otra vez a 45° hacia arriba. Los contactos quedan del mismo lado que antes (cada pliegue da vuelta la cinta). Se pliega **una sola vez**: no abrirla y volver a doblarla.
- El tramo horizontal gasta 19 mm de cinta. Por eso la nariz queda a ≈ 38 mm sobre el eje de roll y no en el centro exacto de la cara (≈ 15 mm): ahí se termina la cinta de 150 mm. Para el centro exacto haría falta una cinta de ≈ 127 mm.
- La U y los pliegues son estáticos: la cinta nunca se mueve. 6,5 mm de radio es mucho para una FFC quieta.
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
| Brazo (`BRAZO_*`) | 38 de largo (medido), cubo Ø9, espesor 2,5 | Medir el cubo, el espesor y los radios de los agujeros. |

## Yaw sin rodamiento

Como en la v1 (`../keepon_mg996r_step/`), el plato se atornilla al horn del RDS3218 y **el eje del servo carga todo**. Respecto de la v2, la tapa ya no tiene el aro elevador ni los 6 agujeros del rodamiento, y el plato tampoco tiene esos agujeros. El plato queda 14 mm por encima de la tapa, sin tocarla.

Carga estimada sobre el eje (`--verificar`, PLA con ~50 % de relleno): **≈ 330 g**, con el centro de masa a **≈ 39 mm** del eje en el peor caso (roll 22°). Eso da un momento de vuelco de **≈ 1,3 kgf·cm** sobre el eje del servo, de forma permanente, más los golpes de las aceleraciones. Codex recomendaba un rodamiento justamente por esto (`docs/REVISION_CODEX_HW.md`).

- Atornillar el plato al brazo con los 2 tornillos de las ranuras además del central. El brazo es de plástico: si cede o se rompe con el peso, cambiarlo por uno metálico.
- Después de armarlo, mirar si el plato cabecea al frenar el yaw. Si cabecea, una solución sin comprar nada son 3 o 4 patines impresos sobre la tapa, debajo del borde del plato, con ~0,5 mm de luz: solo tocan si el plato se inclina.

## Brazo de los servos

Los tres servos llevan el **mismo brazo doble de plástico** (`docs/Fotos/brazo_servo.jpeg`) en lugar del horn circular de la v2. Medido: 38 mm de punta a punta, con los agujeros cada ≈ 2,5 mm (en la foto da ≈ 3). Lo demás se estimó de la foto (cubo Ø9, ancho 6,5 → 4 mm, espesor 2,5) y hay que medirlo (`BRAZO_*` en el script).

- El plato, la horquilla y la placa de roll **no tienen agujeros fijos para el brazo**: tienen una **ranura** de 2,4 mm a cada lado del eje, de r = 5,5 a 14,5 mm. El tornillo M2 autorroscante pasa por la ranura y entra en el agujero del brazo que quede debajo, sea cual sea el paso real. Van 2 por brazo (uno de cada lado) y el tornillo central del servo.
- Las piezas tienen un rebaje de Ø10,5 × 1 mm alrededor del eje, por si el cubo sobresale del brazo.
- El brazo va **a lo largo del cuerpo del servo**. En el pitch queda vertical, y la punta de arriba sobresale 3 mm sobre la horquilla (no toca nada en todo el rango).
- **Estriado:** el HS-7955TG es Hitec (24 dientes); el RDS3218 y el MG996R, de 25. El brazo puede ser igual, pero cada uno tiene que ser el que calza en su servo.

## Relaciones de posición en SolidWorks

El STEP solo guarda dónde está cada pieza, no las relaciones de posición. Por eso el script genera la macro `solidworks/keepon_v3_relaciones.bas`, que las crea sobre el ensamble importado.

1. *Archivo → Abrir* `step/keepon_v3_ensamble.step` y guardarlo como ensamble (`.SLDASM`). **No mover ninguna pieza antes de correr la macro:** busca las caras por su posición.
2. *Herramientas → Macro → Nueva*, guardarla (por ejemplo `keepon_relaciones.swp`). En el editor de VBA: borrar el módulo vacío que crea, *Archivo → Importar archivo…* `keepon_v3_relaciones.bas` y ejecutar `main` (F5).
3. Al terminar, la macro dice cuántas relaciones creó (son 90: 28 piezas × 3 planos + 3 bisagras × 2) y, si algo falló, cuál.

Cómo están armadas (todas las piezas se exportan con el origen del robot, así que sus planos coinciden):

| Grupo | Pieza de referencia | Las demás piezas del grupo | Bisagra con el grupo de abajo |
|---|---|---|---|
| Base (fija) | `caja_base` (fijada) | tapa, batería, reguladores, interruptor, servo de yaw | — |
| Yaw | `plato_yaw` | brazo de yaw, ESP32 y su cuna, buzzer, soportes de pitch, HS-7955TG | Concéntrica: agujero central del plato ↔ eje del RDS3218. Coincidente: Alzado (XY) del plato ↔ el de la caja |
| Pitch | `horquilla_cabeza` | brazo de pitch, MG996R | Concéntrica: pivote M4 de la horquilla ↔ el del soporte derecho. Coincidente: Planta (XZ) de la horquilla ↔ la del plato |
| Roll | `placa_roll` | brazo de roll, Pi 5, cámara, cinta, caja de la cabeza, ojos | Concéntrica: cubo del brazo del MG996R ↔ su eje. Coincidente: Vista lateral (YZ) de la placa ↔ la de la horquilla |

- Cada pieza se une a la de referencia de su grupo con **tres planos coincidentes** (Alzado, Planta y Vista lateral). Las relaciones quedan con nombres como `pi5_pcb = placa_roll (XZ)` y `Bisagra pitch: eje (...)`.
- Cada bisagra deja un solo giro libre: la concéntrica fija el eje y el plano coincidente impide que la pieza se deslice a lo largo de él. Al final el ensamble se puede mover arrastrando, pero solo en yaw, pitch y roll.
- Las bisagras **no tienen límites**. Para revisar el rango con *Detección de colisiones*, se pueden agregar relaciones de ángulo límite (Avanzadas): yaw ±70°, pitch −20/+30 (los 30° hacia arriba), roll ±20°.
- La macro busca los planos y las caras por tipo y por geometría, no por nombre, así que funciona con SolidWorks en español y en inglés. Usa `AddMate5` (SolidWorks 2017 o posterior).
- **No se probó en SolidWorks** (no hay SolidWorks en Linux). Antes de exportarla, el script verifica que existan las caras cilíndricas que busca. Si alguna relación falla, se la puede agregar a mano siguiendo la tabla.

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
| `nariz_camara`, `ojo_izq`, `ojo_der` | 0,4 + 1,3 + 1,3 cm³ | En negro, con el bisel apoyado en la cama. La nariz tiene el agujero de la lente |
| `plato_yaw` | 57 cm³ | Plano |
| `cuna_esp32`, `porta_buzzer` | 7 + 1 cm³ | Como en la v2 |
| `soporte_pitch_izq/der`, `horquilla_cabeza` | 10 + 13 + 26 cm³ | Las mismas de la v2 |
| `caja_base`, `tapa_base` | 285 + 148 cm³ | La caja es la de la v2; la tapa, sin el aro del rodamiento (o MDF de 4 mm) |

`keepon_v3_ensamble.step` es el ensamble completo para SolidWorks (*Archivo → Abrir*, tipo STEP). Las relaciones de posición se agregan con la macro (ver arriba).

## Orden de montaje

1. Cuello como en la v2, sin rodamiento: el plato con la ESP32, el buzzer y los soportes se atornilla al brazo del RDS3218 (2 × M2 por las ranuras + el central). HS en el soporte izquierdo; horquilla con el MG996R.
2. `placa_roll` al brazo del MG996R (los tornillos del brazo quedan debajo de la Pi: van antes).
3. La Pi parada sobre los separadores (4 × M2,5 × 6), la cinta conectada a la Pi.
4. La cámara a los separadores de `caja_cabeza` (4 × M2) y los ojos pegados. Conectar la cinta a la cámara.
5. `caja_cabeza` sobre la placa: 4 × M2,5 × 12 autorroscantes desde atrás, por la placa, a las costillas.

## Verificado con el script

```bash
cd docs/keepon_v3_cad/fuente
~/cq_env/bin/python keepon_v3_cad.py --verificar   # STEP, STL, macro de SolidWorks, interferencias, holguras y carga del yaw
~/cq_env/bin/python vistas.py                      # vistas/*.png (VTK, sin errores de oclusión)
```

- **Sin interferencias** en 15 poses: pitch −32 / −16 / 0 / +11 / +22 × roll −22 / 0 / +22 (pitch > 0 es nariz abajo).
- **Holgura mínima de la cabeza contra lo fijo:** 3 mm con el plato, en el peor caso (nariz abajo 22° + roll 22°, más que lo que pide `config.yaml`). Sin roll: 6 mm. Con la nariz arriba 32°: ≥ 14 mm.
- **El pitch se monta con los 30° hacia arriba y los 20° hacia abajo** (`config.yaml`: −20/+30). La persona está más alta que el robot, y hacia abajo la holgura con el plato se termina poco después de los 22° (con roll). Al definir `signo` del pitch, que "arriba" sea el lado de los +30°.

## Pendiente

- Probar la macro de relaciones en SolidWorks (no se pudo probar acá).
- Con el robot armado, comprobar que el plato no cabecee sin rodamiento (ver "Yaw sin rodamiento").

- Confirmar `PI_CSI_SALIDA` y medir lo de la tabla de arriba antes de imprimir.
- El cooler toma aire de adelante (16 mm hasta la cara) y lo saca por los costados. Medir la temperatura de la Pi con la cabeza cerrada y la percepción corriendo (`vcgencmd measure_temp` no está en Ubuntu: usar `cat /sys/class/thermal/thermal_zone0/temp`).
- La imagen no necesita rotarse (la cámara va derecha). La lente está en el plano de simetría, pero no sobre el eje de roll: queda 38 mm arriba. El control de mirada usa ángulos de la imagen, así que no cambia nada; solo hay que tenerlo en cuenta al calibrar.
- El alto de 104 mm lo fija la Pi parada (85 mm + la U de la cinta). Para algo más bajo haría falta otra cinta (más corta, o una que permita poner la Pi acostada).
