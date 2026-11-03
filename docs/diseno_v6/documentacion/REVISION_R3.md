# Revisión R3 · montaje y cotas

## Cambios coordinados

| Elemento | Revisión |
|---|---|
| Cara | Una sola pieza con los dos ojos, marcos y relieves de lentes. No se imprimen ojos separados. |
| Buzzer | PCB detrás de cara, paralelo a ella, extremo del transductor hacia Y negativo y normal acústica +X. Se conserva boca Ø12 en Y=0,Z=135. |
| Fijación buzzer | Dos M3×6 desde atrás, centros Y=±35,Z=135; insertos L4 nominales. PCB: M3×6, arandela0.8 e inserto L3 ciego desde X=60. Punta del tornillo X=63.7, cara exterior X=73. |
| Cara/cámara | Entradas frontales anteriores cerradas. Pilotos ciegos desde atrás, pared exterior residual de0.8 mm en fijación de cara y1.2 mm en cámara. Montar y retirar tornillos sólo desde el interior. |
| Pitch | Acceso coaxial Ø8.4 a través de toda la cuna, por ambos extremos, para herramienta y tornillo central del brazo. Se añade casquillo extraíble Ø8.3/4.4 en el apoyo opuesto para conservar el guiado M4. |
| Pi | Cuatro postes Ø9×10.6, frente a Ø6×12.6. Pi y reserva de cooler bajan2 mm; se extiende la reserva del extremo de cinta correspondiente. |
| Soporte base | Cuerpo del RDS3218 centrado X=0,Y=10 en soporte100×68×6. Eje de giro X=Y=0 conservado. Labios laterales para orejas y ventana de cuerpo con presión nominal0.05/lado. |
| Pilares | Cuatro ejes compartidos entre soporte y pilares: X=−18/+38,Y=±6. Soporte Ø3.4 pasante, base con alojamiento nominalØ4×6.6 para inserto M3L5. Se rellenan los antiguos pilotos desplazados. |
| Brazo doble yaw | Longitud total37.7. Anchos, espesor y cubo heredados se mantienen nominales y requieren cotejo físico. |
| Brazo simple pitch | Largo total26.4, espesor2.8, extremo pequeñoØ6.2 y extremo de ejeØ9.2. Centros separados18.7. Tangentes exteriores exactas, eje en extremo grande. |
| Disco roll | Ø20×2.6. Cuatro pasosØ3.4 a radio5, separados90°. Distancia entre centros vecinos7.071; entre opuestos10. |
| Acople roll | Bolsillo circularØ20.5 y espesor2.85, patrón coincidente de cuatro pasosM3 en carcasa; retención periférica con aberturaØ19.6 y acceso centralØ3.4. |
| Identificación | Sólidos y referencias en español; base, giro, inclinación y balanceo identificables. |

Los26.4 mm del brazo simple se interpretan como **largo total**, de acuerdo con el texto y las líneas exteriores del croquis, no como distancia entre centros. Los7 mm del disco son referencia redondeada: radio5 y90° producen7.071 mm exactos nominales.

## Secuencia de montaje

1. Probar presión de cuerpo/orejas e insertos en el material real. Insertar los cuatro M3L5 en pilares y los insertos del buzzer antes de instalar electrónica.
2. Presentar el RDS3218 desde arriba, con orejas asentadas a Z=44. Los labios abrazan sus bordes y los agujeros de orejas quedan libres. Atornillar soporte a los pilares con M3×12 nominales (6 mm de soporte y6 mm de entrada; confirmar asiento e inserto real). Fijaciones de orejas mantienen patrón del servo.
3. Montar brazo simple comercial en su bolsillo; retirar el pivote M4 y el casquillo22; usar el paso completo de la cuna para acceder al tornillo propio del eje. Reinstalar casquillo, pivote y retención antes de cargar la cabeza. No intercambiar estriados entre servos por similitud visual.
4. Presentar disco comercial de roll y comprobar patrónR5 antes de apretar retención. Los cuatro agujeros se repiten en la carcasa; elegir tornillería compatible con agujeros roscados o pasantes del brazo real. No suponer que las roscas están verificadas ni que cabe una tuerca entre disco y motor.
5. Montar Pi en sus cuatro postes rebajados. Comprobar soldaduras, conectores y flex real: la reserva geométrica no demuestra flexión ni longitud disponible.
6. Colocar PCB buzzer en bastidor desde atrás, arandela y M3×6. El tornillo de PCB entra hacia la cara y no la atraviesa. Montar bastidor con los dosM3×6 de los extremos.
7. Ensamblar cámara y cara desde el interior con tornillos adecuados a los pilotos ciegos; no reutilizar largos que atraviesen la piel frontal. Para cara: M2.5×8 nominal con asientoX=64 y puntaX=72. Cámara: elegir según espesor real de placa y enganche disponible, sin superarX=71.8.
8. Cerrar cabeza y comprobar manualmente los extremos antes de energizar servos.

## Qué está y qué no está verificado

Se comprueban B-Rep válidos, piezas imprimibles monosólidas, cotas de brazos, paso completo de pitch, correspondencia de agujeros en pilares, postes Pi y fijaciones ciegas. Se conserva evidencia de interferencias y muestreo de45 combinaciones nominales (yaw−70/−35/0/35/70, pitch−20/0/30, roll−20/0/20). No es un barrido continuo.

Los solapes nominales de eje/cubo sin estriado, la reserva de cooler con la envolvente simplificada de Pi y la interferencia intencional de presión se identifican por pareja. No son una validación física. La revisión nativa verifica guardado/reapertura, cantidad/volumen de cuerpos y poses con solver.

El PCB dispone de10 mm entre su cara de componentes y el dorso de la cara. El PCB está medido, pero faltan la altura y la ubicación exacta del transductor y pines en él. Se conserva la orientación hacia +X y la boca original; **no se certifica alineación acústica exacta ni espacio para componentes no medidos**. El bastidor queda abierto sobre esos componentes para facilitar comprobación. Faltan también estriados/cubos reales, roscas del disco, elección final de tornillos, material e insertos. La fabricación estructural sigue pendiente de esos ajustes.

## Cierre de verificaci?n nativa

SolidWorks2021:15 piezas estructurales y cup?n, cuatro grupos con vol?menes contrastados, seis relaciones reabiertas y diez poses resueltas. El ensamblaje abre con sus cuatroSLDPRT locales y sin STEP externos. Se inspeccionaron las vistas isom?trica, frontal, superior y derecha.

El informe autom?tico conserva `warn`: detecta exactamente tres intersecciones entre grupos de116.615919,86.378090 y49.907341 mm?. Coinciden con los cubos/ejes de referencia sin estriado de yaw, pitch y roll; se contrastaron por pareja y volumen con B-Rep. No se oculta ni se convierte esa advertencia en una liberaci?n de fabricaci?n. Clasificaci?n en `evidencias/solidworks_R3/interferencias_clasificadas.json`.

Adem?s:34 comprobaciones geom?tricas espec?ficas, cuatro regresiones de entrega y15 mallas STL cerradas/orientadas. El barrido de45 combinaciones no detecta interferencias imprevistas, separando los contactos nominales documentados.
