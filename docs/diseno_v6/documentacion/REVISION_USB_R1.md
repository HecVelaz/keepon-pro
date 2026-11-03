# Revisión USB R1

Cambio solicitado mediante las capturas: abertura inferior de la pared
trasera y dos recortes semicirculares en la traviesa del roll, compensados
con más altura por arriba. Las únicas geometrías de impresión cambiadas son
`03_cuna_pitch` y `04_cuba_cabeza`.

Origen y orientación conservados: eje yaw X=Y=0, piso Z=0; +X hacia la cara,
+Y hacia la izquierda del robot. Eje de roll en (0,0,163) mm. Al observar
desde atrás, el paso nuevo queda a la derecha, hacia Y negativo.

| Elemento | Cotas nominales, mm |
|---|---|
| Nuevo paso trasero | Ancho Y=36, alto Z=26, esquinas R3 |
| Centro del paso | Y=−35, Z=127 (36 por debajo del eje roll) |
| Extremos del paso | Y=−53…−17, Z=114…140; corte pasante en pared X≈−42…−39,6 |
| Refuerzo interior | Margen de 4 alrededor del paso; 1,6 de espesor adicional hacia dentro, sin saliente exterior |
| Alivio del lado del USB | R26; centro Y=−49, Z=147; corte a lo largo de X, abierto desde abajo |
| Alivio opuesto | R20; centro Y=57, Z=147; respeta las fijaciones MG996R asimétricas |
| Suplemento superior | +26 en Z; borde superior en Z=205 en HOME |
| Material sobre el alivio R26 | 32 de altura nominal en su sección central; no es cálculo de resistencia |
| Reserva USB de estudio | X=−82…−27, Y=−51…−19, Z=116…138; corredor rectangular, sin conector físico atribuido |

El suplemento incluye un rebaje en su cara interior para que la retención
del horn y sus M3 no choquen al girar. No se trasladaron motor, eje, horn,
agujeros del servo, pivotes ni fijaciones de las otras piezas.

La reserva propuesta reproduce un choque de hasta unos 2405 mm³ con la
traviesa anterior. En 41 poses de roll, de −20° a +20° cada grado, pasa sin
intersección con la cuna R1; distancia mínima muestreada **0,69 mm**. Pitch y
yaw transforman conjuntamente cuna y cabeza, por lo que no cambian esa
holgura relativa. Esta prueba no demuestra un radio de curvatura ni que el
enchufe comprado entre: deben medirse enchufe, funda y cable.

Se repitió además el barrido de 495 combinaciones del robot nominal con los
tornillos finales. Ver `evidencias/auditoria_v6.json` y `USB_R1.json`.
El STEP de reserva, separado del ensamblaje, está en
`evidencias/RESERVA_USB_R1_NO_MEDIDA.step`.

Para montar: pasar el enchufe por el nuevo hueco antes de conectarlo a la
Pi; asegurar el cable a la cabeza con holgura y revisar extremos de roll
con alimentación de servo desconectada. Confirmar que la funda y el bucle
no llegan a la traviesa, al cuerpo del MG ni al pivote. Si el conector no
cabe o la holgura real es insuficiente, ajustar los parámetros USB antes
de imprimir. Comprobar protección del borde y alivio de tensión del cable.

La base y el resto de la primera V6 se conservan. Sólo estas dos piezas
necesitan sustitución por el cambio R1, una vez cerradas las medidas y
condiciones pendientes de fabricación. No se hizo ensayo de carga ni FEA.
