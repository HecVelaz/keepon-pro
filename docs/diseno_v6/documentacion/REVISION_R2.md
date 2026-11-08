# R2 · PCB RLBZ23, pared trasera y ojos

La imagen del usuario identifica tapa14 y la disposición relativa de buzzer
y pines. La referencia de WALL-E define el estilo de carcasas y lentes,
sin cambiar la cámara real ni la cara existente. Las cotas oculares son
decisiones de diseño; las cotas del PCB siguientes fueron aportadas y
aclaradas por el usuario.

## PCB y fijación

| Dato | Valor, mm |
|---|---:|
| Ancho / largo / espesor | 13 / 31,8 / 1,5 |
| Agujero real | Ø3 |
| Borde del agujero al borde longitudinal de referencia | 4,8 |
| Borde del agujero al extremo de placa del lado del buzzer | 14,9 |
| Centro desde los mismos bordes | 6,3 / 16,4 |
| Asiento de placa X | 48,5 |
| Borde de ancho Y / extremo del buzzer Z | 35 / 124 |
| Centro del agujero global Y,Z | 41,3 / 140,4 |
| Reserva detrás de placa respaldada | 3, sin altura física verificada |
| Arandela impresa | Ø7 exterior / Ø3,4 interior / 0,8 de espesor |
| Tornillo a PCB / inserto | M3×5 / M3 L3 |
| Enganche / margen al fondo nominal | 2,7 / 0,9 |

El PCB ocupa X=48,5…50, Y=35…48, Z=124…155,8. Está en un lateral libre de
Pi y cámara, buzzer en el extremo inferior, pines en el superior. El soporte
se fija con dos M3×6 e insertos L4 ya previstos en la cara06: no se cambia
su geometría. El extremo de componentes apunta hacia la cara del robot.

El bastidor tiene ventana trasera, guías en bordes y un apoyo Ø8 para el
agujero. Ese apoyo necesita una zona sin componentes: comprobar ambas
caras y las alturas de soldadura, cilindro, pines y enchufe. Sólo el PCB
medido aparece como referencia CAD; no se representaron envolventes físicas
inventadas para los demás elementos. El M3 nominal debe pasar por el agujero
real sin forzarlo ni ampliar el PCB. Instalar el inserto antes de presentar
la electrónica. No confundir el paso del PCB Ø3 con el taladro térmico
provisional Ø4 del plástico.

El soporte15 debe imprimirse con apoyos bajo su ala frontal. Comprobar
tolerancias del bastidor y arandela, sin doblar la placa al apretar. No se
afirma que la unión esté validada con los componentes reales ni acústicamente.

## Pared trasera

Se retiran tapa14, cuatro M3 y cuatro postes. Se reconstruye la pequeña
zona de pared ocupada por ranuras anteriores y se abre el mismo contorno
redondeado en ambos lados:36 ×26, R3, centros Y=±35 y Z=127.
Hay margen de refuerzo4 e incremento interior1,6 alrededor de ambos huecos.
La cuna03 R1 conserva sus dos recortes y altura; no se cambian ejes ni base.

El estudio de reserva USB del lado Y negativo cubre41 posiciones de roll,
con mínimo0,69 mm contra la cuna. No valida un conector medido, cable flexible
ni la trayectoria por el paso nuevo opuesto. Revisar funda y bucle en extremos.

## Ojos

Carcasas16/17 de contorno redondeado inclinado, espejadas respecto de Y=0.
Plano de adhesión X=73; centros Y=±30,Z=185. Base2, marco elevado0,8 y
contorno configurable en `ojos.contorno_local_uv_mm`, redondeosR4. Las
marcas circulares pequeñas son decorativas y ciegas; no usan tornillería.

Lentes19/20 decorativas Ø27,8, asientoØ28,4 y profundidad0,8, relieve2,2.
Imprimir con dorso plano en cama, comprobar la holgura nominal radial0,3 y
pegar en sus asientos antes de pegar carcasas a la cara. El marco elevado
permite pintura negra, panel gris y lente azul oscuro. Son cuatro piezas
oculares en total; las lentes pueden reutilizar la misma geometría local.
La cámara óptica real continúa en la abertura central existente.

Desde R1 se sustituyen04,15,16/17; se añaden19/20 y21, retirando14. Cara06,
cuna03, tapa05, bandeja08, retención09 y base01 se conservan por este cambio.
Las validaciones son nominales y no sustituyen una prueba física.
