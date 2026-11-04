# Interfaces nominales V6

Origen en el eje yaw, piso Z=0. +X hacia la cara, +Y izquierda del robot.
El eje pitch/roll queda en (0,0,163) mm. Elevación del conjunto respecto
a V5: 13 mm. La base conserva su geometría.

- Adaptador: 70 × 68 × 6, R4, centro XY=(10,10), Z=38…44.
- Brida yaw: cara superior Z=46,5; cuerpo girado +90° alrededor de Z.
- Horquilla: geometría V5 trasladada y nuevo collar HS; bolsillo doble nominal
  de 38 mm, cubo Ø9, rama de 2,5, anchos 6,5/4, con 0,25 mm por lado.
- Cuna: hub pitch Ø49 con paso Ø8,4; tapa Ø53. El bolsillo simple es un estudio
  de una rama, no la medición del brazo. Plano de orejas MG: X=−61.
- Cuba: boss de roll 54 × 36 × 4,8; bolsillo doble nominal y paso Ø8,4.
- R2: dos pasos posteriores iguales de 36 × 26, esquinas R3; centros Y=±35,
  Z=127. La tapa14 y sus cuatro M3/postes ya no forman parte del modelo.
  Refuerzos interiores de 1,6, margen perimetral de4. Cotas de diseño,
  conectores sin medir; reserva USB evaluada del lado Y negativo.
- Traviesa roll R1: alivios R26 en Y=−49 y R20 en Y=57, ambos en
  Z=147; suplemento superior de26 hasta Z=205. Eje y fijaciones
  MG996R conservados; ver REVISION_USB_R1.md y ranuras_USB_R1.csv.
- Cámara: cuatro pasos Ø2,2; centro óptico Y=0,Z=163; ventana Ø17 existente.
  Refuerzo de postes Ø6. El paso elimina el autorroscado anterior: requiere
  M2 pasante con tuerca o una retención alternativa comprobada.
- PCB RLBZ23 medido: 13 × 31,8 × 1,5; X=48,5…50, Y=35…48,
  Z=124…155.8. Buzzer en extremo inferior; pines en superior.
  Agujero Ø3, centro Y=41.3, Z=140.4; desde bordes: ancho6,3, largo16,4
  desde extremo del buzzer. Montaje M3×5, inserto L3 y arandela impresa0,8.
  Bastidor abierto con3 mm de reserva bajo PCB: capacidad de diseño, no
  altura atribuida a los componentes. Faltan alturas/pines y zona libre Ø8.
- Ojos WALL-E: carcasas16/17 espejadas, dorso plano X=73, base2 y marco0,8;
  centros Y=±30, Z=185. Lentes19/20 Ø27,8, asientoØ28,4, profundidad0,8;
  relieve2,2. Contorno y detalles en config.yaml. MarcasØ2,2 decorativas,
  no requieren tornillos ni perforar la cara.
- Cupón: 65 × 16 × 7, R2, agujeros de izquierda a derecha 3,7/3,8/3,9/4,0/4,1;
  centros X=−26,−13,0,13,26, Y=0; profundidad5,6; usar inserto de5 mm.

Las tablas CSV complementan los STEP y el código, en mm. Los valores de
alojamiento y cabeza deben medirse/calibrarse antes de fabricar. Las cotas
heredadas de las piezas reutilizadas siguen en la documentación V5.
