# Mediciones físicas para terminar V6

Anotar milímetros y agregar fotos perpendiculares con regla; usar calibre
cuando sea posible. Tomar las cotas desde superficies y ejes indicados, no
desde el borde de una perspectiva fotográfica.

| Pieza | Medida necesaria |
|---|---|
| Brazo simple de pitch | Del centro del estriado a la punta; ancho cerca del cubo y en la punta; espesor; diámetro y altura del cubo; distancia desde el centro del estriado al centro de **cada** agujero y diámetro de cada agujero; forma y lado de apoyo. Fotografía de ambas caras. |
| Brazos dobles yaw y roll | Para cada brazo: longitud punta a punta (38 mm aproximados), ancho en el centro y extremos, espesor, diámetro y altura del cubo, distancias desde el eje a cada agujero y diámetro de estos. Comprobar en qué servo calza cada estriado. |
| RDS3218 y base impresa | Desde eje del servo hasta centro de cada agujero de brida; distancia entre agujeros del pedestal en X e Y, diámetro y profundidad, cota Z de apoyo; espacio existente bajo su cuerpo. Para el cable: centro de salida medido desde la cara inferior y la pared lateral; ancho y altura de su cubierta, dirección y longitud rígida. Identificar superficie exacta que lo comprime. |
| MG996R | Largo, ancho y alto del cuerpo; desde centro del eje hasta extremo más cercano; distancia de la cara superior de brida al extremo del eje; separación de agujeros entre centros y diámetro; espesor de brida; salida y diámetro de cable. Medir también masa con cable si es posible. |
| USB de Pi | Identificar puerto y medir ancho, alto y largo del conector desde la cara de la Pi hasta el extremo rígido, diámetro del cable y radio mínimo indicado por su fabricante. Medir desde el eje de roll hasta centro del puerto y hasta la abertura trasera, con la Pi montada. |
| Interferencia cabeza/pitch | Marcar en ambas piezas las zonas de contacto; fotografiar HOME y pose de choque. Indicar ángulo y sentido; medir salientes de tornillos desde la cara plástica, deformación y holgura en HOME. |
| Cámara | Confirmar si el problema son los cuatro agujeros de montaje o la apertura óptica. Medir diámetro de agujeros en placa y en cara, diámetro exterior y longitud de rosca de los tornillos; desde centro de lente a centros de agujeros; grosor de placa, conector y FFC. No confundir la NoIR estándar con la Wide. |
| RLBZ23 | Ya confirmados: PCB13 ×31,8 ×1,5, agujeroØ3; distancias al borde4,8 y14,9 desde extremo del buzzer, centros6,3/16,4. Falta medir altura desde cada cara del PCB a cada componente, diámetro/centro y altura del cilindro, soldaduras bajo placa, patas y enchufe GND/I-O/VCC insertado con cable. Confirmar zona libre Ø8 alrededor del agujero y desde qué borde longitudinal se midieron los4,8. Comprobar que M3 pasa porØ3 sin forzar. Confirmar activo/pasivo y señal sin inferirlos sólo de la foto. |
| Insertos | Para cada largo: diámetro exterior medido sobre crestas, longitud efectiva, diámetro recomendado por fabricante y tipo de plástico. Medir cabezas y longitudes bajo cabeza de los M3. La longitud del tornillo debe quedar corta respecto al fondo ciego en el montaje real. |
| Impresión | Material, boquilla, cama útil real y tolerancia medida con cupón. Para cada ajuste, medir largo y ancho del alojamiento impreso y del componente antes de fijar holgura. |

Las medidas y el material alimentan `config.yaml`, que corresponde a la
integración actual. `config_prototipo.yaml` pertenece al estudio preliminar.
El perfil completo del brazo simple se introduce en
`pitch.perfil_brazo_simple_local_xy_mm`, con el eje en (0,0), incluyendo el
cubo; comprobar además alturas y espesores del brazo real.

R2 retira el cierre anterior y deja dos pasos traseros iguales de36 ×26 mm,
esquinas R3, centros Y=±35. Comprobar el enchufe conectado en la Pi y el bucle
de cable. No se ha demostrado el radio ni el espacio del enchufe real.

Los alivios de la cuna se conservan. La reserva USB evaluada corresponde a
Y negativo; la abertura opuesta no equivale a un recorrido flexible probado.
La reserva rectangular de estudio tiene32 ×22 mm de sección y termina en
X=−82; no es la dimensión del enchufe comprado. La holgura mínima calculada
con la cuna es0,69 mm al muestrear roll cada grado. Medir también el cable
curvado y su funda en el extremo de roll que más lo acerca a la traviesa;
no liberar el ajuste únicamente porque la reserva CAD pase.

El soporte de PCB deja3 mm nominales bajo placa en las zonas respaldadas:
es una reserva, no altura medida de soldaduras. Medir la altura hacia la
cara y el enchufe por encima del extremo de pines con la placa presentada
en su posición lateral, antes de imprimir definitivamente soporte15/21.
