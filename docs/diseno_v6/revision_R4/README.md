# Keepon V6 · revisión R4

Abrir **`SOLIDWORKS_R4/Keepon_V6_R4.SLDASM`** con sus cuatroSLDPRT en la misma carpeta. Las versiones anteriores se conservan. El conjunto STEP es `STEP_V6/00_ensamble_V6_R4.step` y la vista de cambios es `vistas/01_R4_cambios.png`.

Cambios incorporados:

- Se elimina la operación anterior `Open CASCADE STEP translator 7.9 4.3-1-solid1`, identificada en SolidWorks como retención del brazo simple de pitch, con sus cuatro tornillos, pasos y cajeados. El pivoteM4, que era4.2, se conserva.
- El brazo de pitch se gira180° en su plano y su bolsillo acompaña el cambio. Se conserva el acceso central pasante y el casquillo extraíble del pivote opuesto.
- Los postes de Raspberry Pi sonØ9×8 mm. Pi y cooler acompañan el asiento. La reserva de cinta conserva140 mm libres más10 de inserción mediante una curva recalculada.
- El buzzer se fija directamente al dorso de la cara con un unico M3x5 en poste integrado y piloto ciego. Se retiraron los dos apoyos y la guia del extremo de conexiones para liberar los cables.
- PCB31.8×12.8×1.5; altura total10 desde dorso del PCB; agujeroM3 a14.8 del extremo corto del buzzer. La cota transversal6.3 procede de la medición anterior. El cilindroØ12 y su centro acústico conservan la referencia nominal previa, no una medición nueva.
- Cuerpos, operaciones importadas y archivos de grupos tienen nombres en español: Base_y_electronica, Horquilla_de_giro, Cuna_de_inclinacion y Cabeza_y_cara.

El croquis aportado en el chat define el **disco rojo25T**:

| Cota | Valor, mm |
|---|---:|
| Diámetro exterior | 19.8 |
| Centros de agujeros opuestos | 14 |
| Radio de los cuatro agujeros | 7 |
| Agujeros de instalación | 4×Ø3 |
| Paso central para tornillo | Ø3 |
| Diámetro exterior del cubo | 9 |
| Espesor del disco | 2.45 |
| Altura total con cubo | 4.5 |

Estas cotas del croquis sustituyen las conversiones comerciales redondeadas de pulgadas. Los centros vecinos quedan a9.899 mm. El25T identifica el estriado; no se inventa un perfil de dientes. Se conserva una cavidad nominalØ5.5118 de la información anterior para representar el acoplamiento, diferenciada del **paso centralØ3** del croquis. Su profundidad3 mm es reserva de montaje para el eje simplificado y requiere cotejo con el brazo real.

El cubo se orienta hacia el servo. Se conserva0.5 mm de separación respecto de la envolvente simplificada del motor; para la altura real4.5 se desplaza0.9 mm la cara de asiento del disco. El bolsillo de carcasa, la retención y los alojamientos correspondientes acompañan ese desplazamiento. La retención tiene aberturaØ18.2 y0.8 mm de solape radial sobre el borde del disco.

El M3 del buzzer entra por detrás del PCB, X=58.5, y terminaX=63.5. El pilotoØ2.5 empiezaX=60 y terminaX=64.6; la cara exterior estáX=73. La fijación es ciega. Probar piloto, material y tornillo reales; no se modela una rosca ficticia. El transductor nominal deja1.5 mm antes del dorso de la cara, orientado hacia la boca original.

Para regenerar, conservar las fuentes V2–V6 y usar el Python aislado de CAD:

1. `verificar_R4.py --exportar` genera geometrías y comprobaciones.
2. `crear_solidworks_R4.py --etapa todo --continuar` genera piezas, grupos y ensamblaje nativos.
3. `verificar_mallas_R4.py`, `renderizar_R4.py` y `empaquetar_R4.py` verifican las salidas y preparan la entrega.

Los SLDPRT son cuerpos importados con nombres legibles; la fuente paramétrica es Python/config.yaml. La fabricación sigue condicionada al cotejo físico del estriado, transductor, cableado, material y encastres.

## Verificaci?n de entrega

-30 comprobaciones geom?tricas espec?ficas aprobadas.
-45 combinaciones nominales muestreadas sin interferencias imprevistas.
-12 STL cerrados, orientados hacia afuera y apoyados enZ=0.
-SolidWorks2021: cuatro grupos, seis relaciones, diez poses resueltas, guardado y reapertura. Sin dependencias STEP externas.
-Cuerpos y operaciones importadas de los cuatro grupos auditados: nombres ?nicos y sin ?Open CASCADE?. Las secciones del flex tienen sufijos identificables en espa?ol.
-El informe autom?tico conserva tres avisos de intersecci?n de ejes/cubos comerciales sin estriado exacto. Se contrastaron por pareja y volumen con B-Rep; no se ocultan ni se presentan como fabricaci?n validada. Evidencia en `evidencias/solidworks_R4/interferencias_clasificadas.json`.

La tabla `interfaces_R4.csv` registra las interfaces activas para distinguirlas de los par?metros heredados de revisiones anteriores.
