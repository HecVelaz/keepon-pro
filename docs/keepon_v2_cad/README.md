# Keepon pro v2: modelo mecánico

Carcasa estilo Keepon (cabeza esférica y cuerpo elipsoidal) sobre un cuello de 3 GDL con los servos elegidos, la Pi 5 y la ESP32-C3 **sobre la plataforma de yaw** (para que la cinta de la cámara no se tuerza) y una caja base con la batería y los reguladores. Diagrama eléctrico: `docs/diagrama_sistema/index.html`.

La carpeta `docs/keepon_mg996r_step/` (tres MG996R, sin electrónica) queda como referencia; este modelo la reemplaza.

## Cómo abrirlo en SolidWorks

- `step/keepon_v2_ensamble.step`: ensamble completo con colores y nombres. En SolidWorks: *Archivo → Abrir*, tipo STEP. Lo importa como ensamble con una pieza por componente.
- `step/<pieza>.step`: cada pieza imprimible por separado.
- Las piezas importadas son sólidos sin árbol de operaciones. Para editarlas en SolidWorks se puede usar *FeatureWorks* (reconoce extrusiones y agujeros), pero es más fácil cambiar los parámetros en `fuente/keepon_cad.py` y volver a exportar.
- `stl/`: las mismas piezas para el slicer.

## Regenerar

```bash
python3 -m venv ~/cq_env && ~/cq_env/bin/pip install cadquery
cd docs/keepon_v2_cad/fuente && ~/cq_env/bin/python keepon_cad.py
```

Todas las medidas están en la sección PARÁMETROS del script. Las cotas que dependen de otras (la altura del plato, el eje de pitch, el ancho de la horquilla) se recalculan solas. `ensamble(yaw, pitch, roll)` arma cualquier pose, e `interferencias()` lista los pares de piezas que se superponen.

## Disposición

```
            cabeza_izq + cabeza_der + 2 ojos       ← carcasa, gira con roll (Ø165)
            placa_cabeza + Camera Module 3 NoIR   ← roll (MG996R)
            horquilla_cabeza                       ← pitch (HS-7955TG + pivote M4)
  soporte_pitch_izq / _der    Pi 5    ESP32-C3    buzzer
  cuerpo_izq + cuerpo_der (Ø200), atornillados al plato   ← giran con yaw
  plato_yaw (Ø180)  ─── rodamiento Ø80/100 ───     ← yaw (RDS3218, en la tapa)
  tapa_base
  caja_base 200 × 190 × 70: batería (adelante), reguladores 6 V y 5 V (atrás), interruptor (pared trasera)
```

- Ejes: +X hacia adelante, +Y a la izquierda, +Z arriba. El origen está en el eje de yaw, en el piso de la caja.
- El yaw atraviesa la tapa con la brida debajo, y el plato se atornilla al horn. El **rodamiento soporta el peso y el vuelco**: el servo solo hace girar.
- **Cables por el eje de yaw:** suben por el agujero fijo de la tapa (a 26 mm del eje) y entran por la ranura en arco del plato. La ranura abarca ±75°, así que el agujero queda debajo de la ranura en todo el recorrido de ±70°. Hay que dejar una espiral de servicio dentro de la caja.
- La **Pi** va atrás, con los puertos USB hacia la ESP32 y el borde de USB-C, HDMI y conectores de cámara hacia la cabeza. La cinta CSI baja por la ventana del piso de la horquilla y solo se dobla con pitch y roll.
- El eje de pitch está 65 mm sobre el plato y 20 mm adelante del eje de yaw. El eje de roll lo corta en el mismo punto y la lente queda sobre el eje de roll.
- El HS-7955TG apoya la brida del lado de adentro del soporte izquierdo, así sobresale 5 mm menos hacia afuera y entra en la cabeza.
- Altura total ≈ 24 cm.

## Carcasa

- **Cabeza:** esfera de Ø165 y 2,5 mm de pared, centrada en el cruce de los ejes de pitch y roll. Al girar en pitch y roll ocupa siempre el mismo lugar: el mecanismo que va adentro nunca la toca. Solo hay que abrirle abajo el paso de lo que está fijo al plato (el plato, los soportes, el HS, la Pi y la ESP32). `contorno_abertura()` lo calcula muestreando pitch ±32° y roll ±22° cada 2°, con 2 mm de margen. La abertura llega a ~75° desde abajo adelante y a ~100° atrás (por la Pi).
- **Cara:** la lente de la cámara es la nariz, al ras de la cáscara (separadores M2 de 30 mm desde la placa). Los dos ojos son tapones negros que se imprimen aparte y se pegan.
- **Dos mitades, izquierda y derecha,** que entran de costado. Cada una tiene una mordaza que abraza el borde lateral de la placa de la cabeza. Se unen con dos tornillos M3 arriba (adelante y atrás). Cada mitad se imprime apoyada sobre su cara plana, sin soportes en la parte exterior.
- **Cuerpo:** elipsoide de Ø200 × 160 cortado en el plato y alrededor de la esfera de la cabeza (con 2 mm de luz), con ranuras de ventilación atrás para la Pi. También va en dos mitades que entran de costado, y cada una se atornilla al plato con 2 orejas (gira con el yaw). Se imprime apoyado sobre la cara plana del corte.
- Por qué en mitades: con la cabeza puesta, el cuerpo entero no puede bajar desde arriba; y con el cuerpo puesto, la cabeza no entra. Al entrar de costado, desde afuera hacia adentro, ningún punto del cuerpo pasa por la esfera de la cabeza.

### Orden de montaje

1. Plato con la Pi, la ESP32, el buzzer y los soportes; HS en el soporte izquierdo.
2. Horquilla con el MG996R, montada entre el horn del HS y el pivote M4.
3. Placa de la cabeza al horn de roll, y la cámara sobre los separadores. Conectar la cinta CSI.
4. Mitades de la cabeza: entran de costado hasta que las mordazas tomen la placa, y se cierran con los dos M3.
5. Mitades del cuerpo: entran de costado y se atornillan al plato.

## Verificado con el script

- Sin interferencias entre ninguna pieza en las poses (pitch, roll) = (0, 0), (±32, ±22) y (±32, ∓22), carcasa incluida.
- Montaje: cada mitad de la cabeza entra de costado sin tocar nada (sin el cuerpo puesto), y cada mitad del cuerpo entra de costado con la cabeza ya puesta (se probó desplazando cada pieza de a 8 mm, hasta 120 mm).

- Volúmenes a imprimir: caja 285 cm³, tapa 164, plato 98, cuerpo 50 + 50, cabeza 64 + 64, horquilla 26, placa 16, soportes 10 + 13, cuna 7, portabuzzer 1, ojos 1. Son unos 850 cm³, alrededor de 1 kg de PLA con 100 % de relleno. Con 20–30 % de relleno baja bastante (las carcasas son de pared fina y no cambian).
- La caja y la tapa (200 × 190 mm) entran en una cama de 220 × 220. Si la impresora es más chica, conviene cortarlas en MDF de 3 mm.

## Antes de imprimir: medir con calibre

Las medidas de los servos son nominales y cambian entre fabricantes. Si no coinciden, el agujero de la placa queda corrido respecto del eje.

| Parámetro | Qué es | Valor usado |
|---|---|---|
| `Fb` | altura de la cara superior de la brida desde la base | RDS 28,5 · HS 27 · MG 30 |
| `S` | altura de la punta del eje estriado sobre la brida | RDS 17 · HS 15 · MG 16 |
| `a` | distancia del eje al extremo del cuerpo | 10 |
| `hs`, `hw` | separación de los agujeros de la brida | 49,5 (HS 48) × 10 |
| `horn_r` | radio de los agujeros del horn que se atornillan | 8 |
| `BATERIA` | batería 3S 8000 mAh | 50 × 166 × 37 |
| `REG6`, `REG5` | reguladores | 50 × 65 × 25 · 32 × 55 × 15 |
| `ROD_*` | rodamiento (agujeros incluidos) | Ø80/100 × 8 |
| Camera Module 3 | agujeros 21 × 12,5 mm y posición de la lente | lente a 14,5 mm del borde inferior |

Lo más delicado es `S` de cada servo: de ahí sale dónde apoya cada pieza sobre su horn. Los agujeros del horn conviene marcarlos con el horn real y agrandarlos si hace falta.

## Tornillería

- M3: brida de los servos (4 por servo), tapa a la caja (4), soportes y cuna al plato (6), rodamiento (12), portabuzzer (1).
- M2,5 × 6: Pi 5 a los separadores impresos (4, autorroscantes).
- Separadores M2 de 30 mm y tornillos M2: cámara a la placa (4).
- M3 × 16 con tuerca: unión de las dos mitades de la cabeza (2). M3: mitades del cuerpo al plato (4).
- M4 × 20, arandelas y tuerca autofrenante: pivote del pitch.
- Tornillos de los horns: los que vienen con cada servo.

## Pendiente

- Las vistas de `vistas/` salen de matplotlib y tienen errores de oclusión. Para verlo bien, abrir el STEP en SolidWorks.
- El cuerpo queda ancho y bajo, porque abajo está la caja de la batería. Para un muñeco de nieve más alto habría que achicar o redondear la caja base (tipo pedestal) y bajar el cuerpo.
- Abajo y adelante queda una abertura entre el cuerpo y la cabeza: es el lugar que necesita la cabeza para inclinarse ±32°. Si se limita el pitch real (por ejemplo, −20/+30), se puede achicar con `PITCH_BARRIDO`. Atrás la cabeza queda abierta hasta un poco sobre el ecuador, por la Pi.
- Las mitades se unen solo con tornillos y mordazas. Si quedan flojas, se pueden agregar pestañas a lo largo del corte.
- Confirmar con el robot armado qué sentido de giro es "arriba", "izquierda" y "derecha" (`signo` en `config.yaml`).
- Si el yaw resulta lento por la masa de la plataforma (Pi, ESP32, HS y cabeza), bajar `amax` del yaw en `config.yaml`.
