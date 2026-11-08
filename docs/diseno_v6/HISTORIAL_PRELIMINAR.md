# Keepon V6: desarrollo parcial

La referencia para este trabajo es `../diseno_v5/`, la última versión de la
familia `Robot_Social_Mathias`. Es distinta de `../../docs/keepon_v4_cad/`,
que `CLAUDE.md` señala como diseño vigente del proyecto. Se conservaron ambas
familias y todos sus archivos. Esta carpeta **no es una V6 completa ni una
entrega del conjunto lista para fabricar**.

## Resultado disponible

`generar_ojos.py` produce una pieza reutilizable para ambos ojos, con la misma
elipse de 36 × 40 mm que los gráficos de V5 y una cara plana para pegado.
Su espesor de 1,2 mm es una decisión de diseño, no una medida de componente.
La cara V5 es plana y no requiere modificación para pegar los ojos. Imprimir
dos copias de `IMPRESION_STL/ojo_adhesivo.stl`, con la superficie plana sobre
la cama. `STEP/ojo_adhesivo.step` es el sólido editable por importación; el
script es la fuente paramétrica. Los brillos de V5 se pueden pintar.

`SOLIDWORKS/ojo_adhesivo.SLDPRT` se guardó en SolidWorks 2021 desde el STEP.
El árbol muestra un sólido con referencia 3D Interconnect a `STEP/ojo_adhesivo.step`:
conservar ambos archivos en la estructura de carpetas. No contiene croquis ni
cotas nativas editables; los parámetros se modifican en `generar_ojos.py`.
El diagnóstico de importación mostró cero caras defectuosas y cero separaciones.
La reapertura quedó pendiente porque SolidWorks avisó de memoria insuficiente
y había un ensamblaje V5 con cambios sin guardar en la sesión.

Centros nominales en coordenadas de montaje V5: X=73 mm sobre la cara,
Y=±30 mm y Z=172 mm. Orientar el eje mayor vertical, comprobar visualmente
la simetría y probar el adhesivo con el material real antes de fijarlos.
No hay tetones que obliguen a reimprimir la cara. El modelo de posicionamiento
no incluye espesor de adhesivo; el montaje real queda por probar.

Generación: `C:/Users/mathi/.codex/environments/solidworks-automation/Scripts/python.exe generar_ojos.py`.
El archivo `evidencias/ojos.json` registra sólido válido, STEP reimportado,
volumen y malla con dos incidencias por arista. Esta comprobación no certifica
ausencia de autointersecciones en general, adhesión ni impresión física.

## Comparación y diagnóstico

| Tema | V5 | V6 en esta carpeta |
|---|---|---|
| Base | Base fija 210 × 210 con pedestales integrados | Sin cambios; falta adaptador independiente para servo yaw |
| Pitch y roll | Cuna de pitch; MG996R invertido con cuerpo dentro de cabeza y horn fijo a la cuna | Prototipo nominal de cuna y cuba con MG996R exterior; faltan horn y comprobaciones físicas |
| Brazos | Tres envolventes rectangulares de brazo doble, con ranuras | Pendiente medir brazos reales; el brazo de pitch no se tratará como doble |
| Cabeza | Paso posterior 22 × 14 y ranuras de brida nominales | Falta comprobar con el conector y la zona de contacto reales |
| Cámara | Camera Module 3 NoIR estándar; cuatro pilotos Ø1,6 nominales y ventana de lente Ø17 | Falta localizar el problema físico de agujeros; no se agrandan sin identificar si son montaje o ventana óptica |
| Buzzer | Manguito para buzzer individual en la boca | Falta soporte para placa RLBZ23 completa y revisión de conexión eléctrica |
| Ojos | Gráficos y adhesivos, sin piezas imprimibles | Dos piezas adhesivas iguales, generadas aquí |

La V5 sitúa el eje de pitch y roll en (0, 0, 150) mm y usa rangos nominales
yaw ±70°, pitch −20/+30° y roll ±20°. El informe previo
`../diseno_v5/evidencias/holguras_continuas.json` calcula una separación
conservadora de **1,0 mm** entre la envolvente de cabeza y la traviesa de cuna,
y de 2,77 mm hacia los brazos de cuna. Es evidencia histórica para geometría
nominal, no una nueva simulación de V6: excluye tornillos y cables. La V5
informa además un barrido discreto de 495 poses, sin representar las medidas
reales de brazos ni la flexibilidad de cables. El contacto físico reportado
prevalece sobre la ausencia de colisión nominal en ese modelo.

La documentación y el plano oficial de la cámara están en
`../diseno_v2/referencias_componentes/camera_module_3_standard_plano_oficial.pdf`.
El posicionamiento de V5 y el montaje real deben contrastarse con dicho plano,
incluyendo diámetro de agujeros, lente, conector y FFC. El modelo de V5
utiliza una envolvente simplificada; no demuestra el campo de visión.

## Prototipo de roll exterior

En `PRELIMINAR/` hay STEP de la cuna y cuba modificadas, una envolvente
nominal del MG996R, un conjunto de estudio y una vista. Se generan con
`generar_roll_exterior.py` y `config_prototipo.yaml`, usando los STEP de V5.
El eje roll conserva el centro nominal (0, 0, 150) y el motor se sitúa detrás
de la traviesa en el grupo pitch; la placa añadida en la cuba gira con la cabeza.
El sentido eléctrico de roll deberá recalibrarse, pues cambia el montaje invertido.

Las piezas son sólidos válidos individuales. En HOME los pares cuna/cuba,
cuna/motor y cuba/motor no presentan intersección volumétrica. La regresión
`test_roll_exterior.py` cubre el choque encontrado inicialmente entre ventana
de soporte y cuerpo nominal. `verificar_roll_exterior.py` comprobó nueve poses
(pitch −20/0/+30°, roll −20/0/+20°, yaw 0°) frente a las envolventes V5,
sin intersecciones reportadas en los pares con piezas modificadas. Ver
`PRELIMINAR/barrido.json`. No se comprobó yaw extremo, movimiento continuo,
cargas, tornillos, brazo, flexión ni cables. El apoyo y la ventana todavía son
provisionales y requieren comprobar resistencia y dimensiones reales.

**No imprimir el prototipo:** las ranuras de la placa no son aún un encastre
del brazo; tampoco se ha verificado que el horn acople al eje con el espacio
axial disponible. No se ha corregido el brazo simple del pitch. La cuba conserva
los antiguos soportes internos del motor; aún no se ha optimizado el mínimo de
reimpresiones. El conjunto STEP no incluye el horn roll ni todo el robot y no
es una entrega funcional. `PRELIMINAR/robot_estudio_incompleto.step` integra
las piezas V5 y la propuesta en HOME, pero omite ambos brazos de pitch y roll;
sirve para examinar la disposición, no para el montaje o la fabricación.
No se generaron SLDPRT de estas piezas: la sesión
de SolidWorks tenía V5 con cambios sin guardar y avisó memoria insuficiente;
se pueden abrir los STEP para revisión, sin confundirlos con validación nativa.

Los tres `horn_*.step` de `docs/keepon_v4_cad/` se midieron: cada uno modela
un brazo doble de 38 mm; los taladros de radio nominal 0,75 mm están a 7, 10,
13 y 16 mm del eje por cada lado. Es un modelo común estimado, no la forma del
brazo simple físico del HS. Datos y cilindros en `evidencias/referencias_step.json`.
Las ranuras V5 son una solución previa nominal, no prueba del patrón real.
La guía [MEDICIONES_PENDIENTES.md](MEDICIONES_PENDIENTES.md) indica exactamente
qué dimensiones y puntos de referencia se necesitan.

### Datos confirmados posteriormente

El usuario confirmó RDS3218 en yaw, HS-7955TG en pitch y MG996R en roll;
los brazos dobles tienen aproximadamente 38 mm de largo y el de pitch es
simple. El largo aproximado no define ancho, espesor, perfil ni perforaciones.
Los CAD de V3–V5 representan pitch como doble, por lo que no permiten derivar
la geometría real del brazo simple. El módulo RLBZ23 descrito por el usuario
tiene placa rectangular, un agujero de montaje y tres pines GND, I/O y VCC;
las dimensiones de la placa y conectores aún no están medidas. La imagen
mencionada no estaba disponible en el contexto de esta sesión.

La búsqueda por `RLBZ23` no identificó una ficha del módulo concreto. Hay
módulos de apariencia y conexión similares con medidas distintas: por ejemplo,
[Microscale](https://www.microscale.net/products/passive-buzzer-module) lista
32,2 × 13 mm y [Synacorp](https://synacorp.my/v3/en/index.php?controller=attachment&id_attachment=740)
lista 18,5 × 15 mm. No son evidencia de las cotas del módulo del usuario.
La condición de activo o pasivo y la polaridad de activación siguen sin confirmar.

`diagnostico_holgura_v5.py` mide los STEP nominales de cuna y cuba en pasos de
5° de roll entre −20° y +20°. La cuna y la cuba comparten yaw y pitch, por
lo que esos dos giros no modifican la distancia relativa. El informe está en
`evidencias/holgura_cuna_cuba_v5.json`; sus limitaciones son el muestreo
discreto y la ausencia de tornillos, cables, tolerancias y deformaciones.
El mínimo obtenido es **5,0 mm** para ese par de piezas en las nueve poses.
No contradice directamente la cota conservadora anterior de 1 mm, calculada
para una envolvente más amplia de la cabeza; tampoco explica el contacto real,
que podría involucrar otra pieza, un saliente o diferencias de montaje.

## Datos necesarios antes de continuar

1. Confirmar que la base y cabeza físicas corresponden a `diseno_v5`, con
   fotos y medidas de los puntos de fijación, espesor y posición del servo;
   medir ubicación, diámetro y dirección de salida de su cable. Un adaptador
   que eleve o desplace el eje puede alterar el acople y el recorrido de yaw.
2. Indicar superficies que chocan en pitch, sentido y ángulo aproximado, y
   medir posición de tornillos y salientes. Verificar deformación y holguras.
3. Medir el brazo real del HS-7955TG (contorno, cubo, espesor, patrón y
   tornillos), y separadamente los brazos de yaw y roll. La V5 contiene una
   representación genérica que contradice el brazo de pitch indicado.
4. Medir el MG996R real, orejas, eje y salida de cable; contrastar el espacio
   detrás de la cabeza y acceso a herramientas para mover el motor a la cuna.
   La masa y el brazo respecto al pitch deben revisarse con el montaje nuevo.
5. Medir el conector USB, diámetro y curvatura permitida del cable, localización
   del puerto, recorrido y holguras en extremos. Identificar además el método
   real de alimentación de Pi y las rutas de CSI y buzzer.
6. Identificar qué agujeros de cámara resultan pequeños y medirlos junto con
   los tornillos y placa; revisar el módulo y la orientación del conector FFC.
7. Medir la placa RLBZ23, agujeros, componentes y conectores completos; obtener
   su esquema o identificar entrada y tipo de buzzer, antes de asignar conexión
   GPIO o reutilizar el circuito de buzzer pasivo de V5.
8. Identificar material, impresora, diámetro real de los insertos y ficha del
   fabricante. Calibrar un cupón de alojamiento: Ø4,2 nominal no define por
   sí solo el diámetro de instalación. Faltan las longitudes efectivas de
   agarre, cabezas, arandelas y acceso para seleccionar tornillos e insertos.

No se generaron archivos de fabricación para las interfaces pendientes: una
ranura o encastre supuesto no demostraría ajuste ni evitaría daños. La solución
de roll, la corrección de pitch, el adaptador, el soporte del módulo, los
cables, las fijaciones y los refuerzos aún requieren diseño, integración,
comprobación de colisiones y ensayo físico. Las listas de tornillos M2/M2,5/M4
heredadas de V5 incluyen elementos que no aparecen en el inventario nuevo y
deben revisarse antes de seleccionar las uniones definitivas. La base existente
no debe modificarse ni reimprimirse.
