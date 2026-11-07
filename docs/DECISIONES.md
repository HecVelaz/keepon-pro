# Decisiones

Movido desde `CLAUDE.md` el 22/10/2026. No volver a discutirlas sin datos nuevos.

## Decisiones tomadas (no volver a discutir sin datos nuevos)
- Todo corre en la Pi; Python puro; `rclpy` solo para leer la cámara. Codex coincidió (`docs/REVISION_CODEX_PI.md`).
- Alimentación (14/10): fuente de laboratorio a 6 V para los servos y powerbank Xiaomi para la Pi. El enunciado solo pide "Demo: funcional, con alimentación propia" (§6.1); no habla de baterías.
- YOLO26n exportado a NCNN con **entrada de 256 px** (`~/keepon/models/yolo26n_256_ncnn_model`): detectó 2 de 2 personas a 1,5 m, a 30 Hz solo.
- Procesos separados, no hilos: NCNN y MediaPipe no liberan el GIL (medido: 2,11 s en serie vs 2,04 s en hilos).
- Afinidad de núcleos: personas `[0,1]` con NCNN de 2 hilos y `openmp_blocktime=0`; pose `[2,3]`. NCNN y MediaPipe reubican sus hilos en 0-3, por eso `_repin_threads()` los vuelve a fijar cada 50 cuadros.
- Rostros: BlazeFace (6 puntos) sobre un recorte de la cabeza en lugar de Face Landmarker (478 puntos, ~49 ms/cara).
- ME_MIRA = ángulo entre el eje de la cara y la línea cara→cámara < `looking_deg` (15°, **sin validar**).
- Intrínsecos tomados de `~/vision_estereo/config/calibracion/right_corregida.yaml` (fx=948 → **HFOV 37,3°**, no los 66° nominales: camera_ros a 640×480 recorta el sensor). cx=428 queda descentrado, así que el centro óptico no es el centro de la imagen. **Verificar que esa calibración corresponde a esta cámara.**

## Otras decisiones (estaban repartidas en las secciones de hardware y de sesiones)
- **Alimentación (14/10):** fuente de laboratorio para los servos y powerbank para la Pi. La LiPo Zeee y los reguladores salieron del diseño. Son dos fuentes separadas, unidas solo por el GND.
- **Asignación de servos (12/10):** yaw = RDS3218 n.º 2, pitch = HS-7955TG, roll = MG996R (desde el 13/10, decisión del grupo; MG90S de repuesto). Se aceptó la banda muerta del MG996R porque roll hace gestos grandes. **05/11 (grupo):** pitch y roll pasan a ser dos TowerPro MG996R nuevos (el HS-7955TG y el MG996R con zona muerta salen).
- **Descartado: RDS3218 n.º 1** (vibra cerca de 1500 µs; la vibración sigue al servo). Roll pasó de GPIO3 a **GPIO4** (12/10) y quedó así: el GPIO3 está al lado del GPIO2, de strapping.
- **No hay rodamiento de yaw** (no se consigue): desde el 14/10 la v3 apoya el plato solo en el horn del RDS3218.
- **Revisión de arquitectura de Codex (14/10, `docs/REVISION_CODEX_ARQ.md`):** mantener la ESP32 (el enunciado pide microcontrolador + protocolo; watchdog independiente de Linux), Pi en la cabeza por la cinta de 150 mm, cara plana.
- **Modelo mecánico vigente: v6 R4** (`docs/diseno_v6/`, 30/10; empezar por `LEEME_GIT.md`): yaw = RDS3218 en la base, pitch = HS-7955TG sobre la horquilla de yaw, roll = MG996R sobre la cuna de pitch (disco de 25T). Ejes de pitch y roll en (0, 0, 163) mm, con el centro óptico de la cámara a la misma altura. Mismos recorridos que `neck.limits`. Es nominal: se fabrica después de las medidas de `docs/diseno_v6/MEDICIONES_PENDIENTES.md`.
- Antes: **v4** (`docs/keepon_v4_cad/`, 14/10): disposición de la v1 (eje de pitch sobre el de yaw, base en U de 64 × 116 en lugar del plato Ø146: el vuelco sobre el yaw baja a 0,81 kgf·cm). La v3 reemplazó a la v2 para imprimir.
- **Pitch se monta con +30° arriba y −20° abajo** (v3: más de ~22° abajo la cara toca el plato; el v6 R4 mantiene ese recorrido y lo verificó en 45 poses nominales). La Pi se alimenta por el GPIO si la cinta tapa el USB-C.
- **Tracker IoU propio**: el ByteTrack de ultralytics costaba ~68 ms/cuadro en la Pi.
- **Camisetas (15/10):** reglas de color y patrón sobre el torso (la guía las permite expresamente), no una red entrenada. Olimpia = franja horizontal negra con blanco arriba y abajo; Cerro = rojo **y** azul en partes grandes separados por bordes verticales (no exigir rayas, porque la titular 2026 es mitad y mitad). Filtro 6 cuadros para confirmar y 6 para soltar, por persona. Para la NoIR: luz LED en la demo, balance de blancos y exposición fijos; si no alcanza, la Camera Module 3 estándar.
- **Nombres sin espacios (PR #1, rama `compatibilidad-windows`):** Git for Windows no restauraba rutas que terminaban en espacio; se pasaron a guion bajo todas las carpetas y archivos con espacios.
- **Compensación de zona muerta (03/11):** el firmware suma `compensacion_us` [al bajar, al subir el pulso] según el sentido del último movimiento de cada eje, y la conserva quieto. Solo el roll la usa (`[0, 151]`): el MG996R montado se frenaba ~10° antes con el pulso subiendo. Va en el firmware porque el simulador trabaja en grados, no en pulsos.
- **Firmware:** en STOP/watchdog seguir mandando el último pulso a los tres servos (el MG996R sin pulso queda flojo); arrancar en home (el primer pulso salta a velocidad máxima); a roll mandarle el objetivo de un solo movimiento (banda muerta ~10°). Detalle en `firmware/CLAUDE.md`.
- **03/11:** centro óptico provisorio = centro de la imagen hasta calibrar esta cámara (el de la calibración ajena
  corría la mirada ~6,5°). La cámara se rota en `camera_ros` (`orientation_deg`), no en Python.
- **03/11:** buzzer en el **GPIO5** (`buzzer.pin`); en el GPIO10 dejó de sonar con la cabeza armada.
- **03/11:** la polca se queda en el fragmento de 8 compases (la guía pide "un fragmento reconocible"; la completa
  dura más de un minuto y ocuparía el buzzer).
- **03/11:** demo como servicio de usuario (`keepon.service`), **no activado al encender** salvo para la demo
  (`keepon demo-on`): la Pi se usa en otros proyectos y el robot toma la cámara y la ESP32.
- **03/11:** control desde el celular con una página web instalable (PWA, `scripts/panel_web.py`), no una app nativa;
  sólo acepta una lista cerrada de comandos.
- **03/11:** "quieto" para la curiosidad = la dirección de la persona (cuello + error), no el error del control.
- **04/11:** panel del celular como servicio aparte siempre prendido (`keepon-panel`), que enciende y apaga el robot
  con `systemctl --user`: así el celular sirve con el robot apagado. Sigue sin aceptar comandos libres.
- **04/11:** sonidos del operador: el último pedido corta al anterior (antes se descartaba el nuevo).
- **04/11:** volumen del buzzer en tiempo de ejecución con el comando `VOL` (FW_VERSION 2), aceptado aunque haya STOP.
- **04/11:** camisetas: umbrales medidos con la NoIR sobre las prendas reales (`config.yaml`, `camiseta`); el detector
  corre en el proceso de pose; el filtro 6/6 se cuenta en cuadros de pose. La mirada apunta 8° debajo de la cara
  (`gaze.mirar_abajo_deg`) para que entre la camiseta.
- **05/11:** movimientos **rápidos y pocos, no lentos y continuos**: los tres servos vibran moviéndose lento (quietos no).
  Bajar `vmax`/`amax`/`kp` empeoró. Quedan `vmax` 180/120/120 °/s y `amax` 600/400/300 °/s².
- **05/11:** mirada por objetivo (`gaze.modo: objetivo`): la referencia salta adonde está la persona, calculado con la
  posición del cuello al sacar la foto (compensa el atraso de la percepción), y queda quieta hasta que se corra más de
  `umbral_deg` (2,5°). Solo se corrige con fotos sacadas con el cuello quieto. El modo velocidad queda de respaldo.
- **05/11:** Observador por miradas (`observer.modo: miradas`): quieto donde estaba, después de punto en punto con pausas
  de 2 s. El barrido continuo queda de respaldo.
- **07/11:** el repo en GitHub queda **público**, para que la cátedra y el grupo lo lean desde afuera (antes la regla
  era privado, para evitar copias). Por eso no se sube nada personal: `capturas/` y `video/` siguen fuera de git.
