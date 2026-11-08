# Diseño v6 en el repo

El diseño mecánico vigente es el **v6, revisión R4** (30/10/2026). Se empieza por `README.md` de esta carpeta
y por `revision_R4/README.md`. El modelo para abrir es `revision_R4/SOLIDWORKS_R4/Keepon_V6_R4.SLDASM`, con sus
SLDPRT en la misma carpeta. El ensamble en STEP es `revision_R4/STEP_V6/00_ensamble_V6_R4.step`.

## Qué servo mueve cada eje

| Eje | Servo | Dónde va en el v6 | Qué mueve |
|---|---|---|---|
| yaw | RDS3218 n.º 2 | En la base, en `10_soporte_centrado_servo_base`, con el eje de giro en X = Y = 0 | La horquilla (`02_horquilla_de_giro`), con el brazo doble |
| pitch | HS-7955TG | Atornillado a la horquilla de yaw | La cuna (`03_cuna_de_inclinacion`), con el brazo simple (girado 180° en R4); del otro lado, pivote M4 con casquillo extraíble |
| roll | MG996R | Atornillado a la cuna de pitch | La cabeza, con el disco rojo de 25T |

Los ejes de pitch y roll se cruzan en (0, 0, 163) mm. El centro óptico de la cámara está a la misma altura
(Y = 0, Z = 163), en la cara. Los recorridos que verifica el CAD (yaw ±70°, pitch −20/+30°, roll ±20°) son los
mismos de `neck.limits` en `config.yaml`.

La frase "MG996R pertenece ahora a pitch" de `revision_R4/config.yaml` (en `cableado.nota`) quiere decir que
el MG996R está **montado sobre la cuna**, que se mueve con el pitch. El MG996R hace el roll.

## Qué está en git y qué no

Están en git las fuentes (`*.py` y `config.yaml`), la documentación (`*.md`, `documentacion/`), el cupón de
insertos en `IMPRESION_STL/` y, de la R4, los SLDPRT/SLDASM, los STEP y las vistas: unos 20 MB.

**Quedan fuera** (`.gitignore`) los ZIP de entrega (`Keepon_V6_*.zip`), `HISTORIAL/`, `evidencias/`,
`PRELIMINAR/`, las carpetas SOLIDWORKS/STEP/STL de las revisiones anteriores a R4, las STL de revisión
("no imprimir") y `mallas_v6.json`: unos 210 MB. El paquete completo de la R4 es `Keepon_V6_R4.zip`:
se comparte por Drive, no por git.

## Para regenerar el CAD

`generar_v6.py` importa `docs/diseno_v5/generar_v5.py`, que **no está en el repo**, además de
`docs/keepon_v2_cad/fuente/` y `docs/keepon_v3_cad/fuente/`. Sin la v5 solo se puede abrir y revisar el
modelo, no regenerarlo. Los SLDPRT son cuerpos importados: la fuente paramétrica es `config.yaml` más el Python.

## Antes de fabricar

El diseño es nominal: falta medir lo que dice `MEDICIONES_PENDIENTES.md` (estriados y brazos reales, MG996R,
cámara, buzzer, insertos, material). Los tres avisos de interferencia que quedan son los ejes y cubos sin
estriado de los modelos comerciales (ver `revision_R4/README.md`).
