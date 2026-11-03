# Verificación de la entrega CAD V6 R2

Estado: integración nominal revisada; fabricación del conjunto condicionada
a las medidas de `MEDICIONES_PENDIENTES.md`. No se hizo una prueba física.

| Comprobación ejecutada | Resultado y alcance |
|---|---|
| Conservación de base | Geometría V5 reutilizada; originales sin modificar |
| Barrido B-Rep | 495 combinaciones nominales, sin intersecciones no previstas; umbral 0,1 mm³, con las exclusiones explícitas del informe |
| Tornillos finales | El barrido R1 usa directamente los M3×6 y las piezas nuevas |
| Reserva USB R1 | 41 posiciones de roll cada grado, sin intersección con la cuna; mínimo muestreado 0,69 mm, con reserva de diseño sin medir |
| STEP/STL de revisión | Diecisiete piezas con B-Rep válido, un sólido, volumen de STEP reimportado consistente; STL con dos incidencias por arista, sin triángulos degenerados, volumen positivo y apoyo Z≈0 |
| Regresiones | Trece pruebas de `test_regresiones_v6.py` aprobadas; resultado automático en regresiones_v6.json |
| Piezas SolidWorks | Dieciocho SLDPRT individuales guardados y reabiertos, incluido el cupón |
| RLBZ23 | PCB13 ×31,8 ×1,5 y agujeroØ3 contrastados; centro6,3/16,4 desde bordes; componentes y pines sin modelar |
| Ojos | Carcasas espejadas con diferencia de volumen0, dorso plano >900 mm² por ojo y abertura central de cámara libre en modelo |
| Pared trasera | Dos pasos pasantes iguales, tapa14 y sus cuatro M3 ausentes del ensamblaje |
| Grupos SolidWorks | Cuatro SLDPRT, 68 cuerpos en total; envolventes y volúmenes contrastados con las fuentes |
| Articulaciones | Tres relaciones concéntricas con giro libre y tres coincidentes axiales; diez poses resueltas y matrices contrastadas |
| Ensamblaje | SLDASM guardado y reabierto; cuatro referencias nativas locales presentes |
| Dependencias | Lectura COM: los cuatro grupos carecen de referencias externas; el ensamblaje sólo requiere esos cuatro SLDPRT |
| Interferencias nativas | Tres acoples eje/brazo de referencia, identificados por pareja y volumen; ninguna otra interferencia reportada entre grupos |
| Revisión visual | Comparación R2 de carcasas/lentes, dos pasos y soporte PCB; vistas nativas del ensamblaje incluidas en evidencia |
| Cableado | Comprobación de longitud recta necesaria en 495 poses por tramo; no es simulación de cable flexible |

El informe automático de la skill conserva estado `warn`: no reconoce por sí
mismo los acoples de los modelos nominales sin estriado. La clasificación
posterior contrasta específicamente 116,615919 mm³ en yaw y pitch, y
62,894685 mm³ en roll. No se descartaron otras interferencias entre esas
parejas. Ver `evidencias/solidworks_v6/interferencias_clasificadas.json`.

La revisión nativa es entre los cuatro grupos rígidos. Las interferencias
internas de sus cuerpos se verificaron por separado en la auditoría B-Rep.
El barrido es discreto; no demuestra ausencia de contacto entre muestras.
No hay estudio dinámico de SolidWorks Motion, análisis FEA ni simulación de
deformación, carga, temperatura, cable, óptica o acceso de una mano/herramienta
real. Las envolventes no incluyen los conectores reales ni la PCB del RLBZ23.

Los SLDPRT contienen cuerpos importados editables mediante operaciones
directas de SolidWorks. No contienen un historial reconstruido de croquis
paramétricos. La fuente paramétrica es `config.yaml` y `generar_v6.py`.
Conservar los cuatro grupos junto al SLDASM al mover el conjunto.

La comparación de volúmenes nativos usa precisión máxima de la API y un
límite relativo de0,0001 %. La integración predeterminada de superficies
elípticas había producido una discrepancia mayor. Los diagnósticos crudos
conservados localmente incluyen comparaciones por nombres repetidos; esas
filas no son un criterio de aceptación de piezas individuales.

Se pueden probar las dos carcasas, dos lentes y el cupón de insertos. Las piezas
estructurales, el encastre de pitch y las interfaces de cable/módulo deben
medirse y regenerarse antes de usarse en el robot físico.
