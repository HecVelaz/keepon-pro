# Diseños mecánicos anteriores

La historia del diseño de la cabeza, de la primera versión a la cuarta. **El diseño vigente es el v6 R4**, en
[`../diseno_v6/`](../diseno_v6/README.md). Estas carpetas quedan como registro de cómo se llegó a él; el v6 reutiliza
código de la v2 y la v3 (`../diseno_v6/generar_v6.py` las importa), así que no se borran.

| Carpeta | Versión | Idea principal |
|---|---|---|
| [`keepon_mg996r_step/`](keepon_mg996r_step/) | v1 | Columna compacta con tres MG996R, sin electrónica (solo STEP) |
| [`keepon_v2_cad/`](keepon_v2_cad/README.md) | v2 | Carcasa estilo Keepon (cabeza esférica, cuerpo elipsoidal) con la Pi y la ESP32 sobre el yaw |
| [`keepon_v3_cad/`](keepon_v3_cad/README.md) | v3 | Cabeza plana con la Pi adentro y la cámara como nariz (la idea que siguió hasta hoy) |
| [`keepon_v4_cad/`](keepon_v4_cad/README.md) | v4 | Cabeza de la v3 + cuello de la v1 + alimentación en la base |

Los pasos intermedios hasta la v6 (desarrollada en SolidWorks) están en `../diseno_v6/HISTORIAL_PRELIMINAR.md`.
