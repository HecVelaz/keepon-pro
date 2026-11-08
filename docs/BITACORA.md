# Bitácora

Lo hecho en cada sesión, lo más reciente arriba. El estado actual está en `docs/ESTADO.md`; lo que falta, en
`docs/PENDIENTES.md`. Creada el 03/11/2026 con la historia que estaba en `ESTADO.md`.

## 08/11/2026
**Movimiento suave, calibración del roll, Observador de la guía y funciones para el video** (rama `movimiento-suave`,
sale de `camisetas`; empezó el 07/11 a la noche)
- **Curva S en todos los movimientos** (`e038dfc`): la posición del servo es el promedio del trapecio en una ventana
  (`neck.suavizado_s`, 0,1 s = 10 pasos). Igual en `keepon/trajectory.py` y `firmware/keepon_fw/nucleo.cpp`. Jerk de
  yaw de 60000–104000 a 12000 °/s³ (≤ 2·amax/ventana: el trapecio discreto pasa de +amax a −amax al frenar), sin pasar
  vmax/amax ni el objetivo; cada movimiento dura 0,1 s más. El espejo de `SerialLink` avanza en pasos fijos de 10 ms.
- **Roll** (medido montado, `scripts/prueba_movimientos.py` y secuencias por SSH):
  - El signo estaba al revés: roll + inclinaba a la izquierda vista desde atrás. Ahora `signo: 1` (`1f62e62`).
  - Se cambió el MG996R por otro igual; cero en **1500 µs**, llegando desde la izquierda (`13169ae`). Banda muerta grande:
    pasos de 3–5° no lo mueven y después salta.
  - **Vibra solo girando a la derecha en la zona negativa** (−10, −15, −20 → 0 por igual; −20 → +20 también), con
    cualquier perfil (trapecio, curva S de 0,1 y 0,3 s). +20 → −20 y 0 → +20 no vibran. **Sin curva S vibró peor**:
    dato nuevo sobre la decisión del 05/11. Probable servo o carga; falta el banco.
  - En prueba: roll `vmax` 250 °/s, `amax` 900 °/s², curva S 0,15 s (`93a0d07`, cargado en la ESP32). Sin resultado aún.
- **Observador**: primero quieto → centro → miradas con roll ±5° y transición de mínimo jerk (`93a0d07`, `7799e2a`). Se
  veía "para y gira": se pasó a **"exploracion"** (`c041452`), lo de la Tabla 1: centra, barre ±45° sin pararse, sacada
  rápida a un punto de interés cada 2 barridos (con roll ±5°). Con 20 °/s de media el yaw vibraba: **25 °/s** (`881b98a`).
- **HOME del operador** (`9a65dda`): el botón mandaba `HOME` por fuera del árbitro y el Observador o el seguimiento lo
  pisaban en el ciclo siguiente (con STOP, la ESP32 lo rechazaba). Ahora es como STOP: va a 0 0 0 y queda hasta RESUME.
  **Probado en el robot: funciona.**
- **Botón "Ejes"** para la escena 0:00–0:15 del video (`135f882`): comportamiento `EJES` (prioridad 0, cuello), ~15 s
  (`ejes.secuencia`). **Polca una vez por aparición** (`cooldowns.CAMISETA_por_persona: null`; antes, 4 polcas en 90 s).
  El beep del modo ya cortaba cualquier sonido desde el 04/11 (`3a9e07c`): tests nuevos con la polca y el saludo.
- Guion del video del usuario revisado escena por escena (ver PENDIENTES). Arbitraje explicado (`keepon/arbiter.py`).
- Firmware cargado varias veces en la Pi (`bash scripts/cargar_firmware.sh`). Secuencias rápidas sin terminal: un script
  temporal en `/tmp/secuencia_keepon.py` de la Pi (se borra al reiniciar); `prueba_movimientos.py` espera un Enter.

Commits: `e038dfc`, `1f62e62`, `13169ae`, `93a0d07`, `7799e2a`, `c041452`, `881b98a`, `9a65dda`, `135f882` (sin push).
Tests: 257. Pi sincronizada en `135f882`.

## 07/11/2026
**Repaso de la consigna y documentación para leer desde afuera** (rama `camisetas`)
- Checklist de la consigna revisado casilla por casilla contra el código: `docs/consigna/CHECKLIST_TP.md` (antes suelto en la
  raíz como `CHECKLIST_TP_ROBOTICA_SOCIAL.md`). Robot (T1–T7, 55 casillas): 31 probadas, 21 hechas sin probar en real,
  3 faltan (latencia evento → respuesta, secuencia de demo, iluminación). Entrega (22): casi todo por hacer (Colab, ZIP, video).
- `docs/consigna/checklist_robotica_social.html` (lo armó Mathias revisando `main` en `cd63108`, del 26/10, por eso marcaba
  como pendientes los modos, SALIENDO y las camisetas): la columna de Hector se precarga con lo hecho y probado
  (34/82 obligatorias), con nota y evidencia por casilla; enlaces a `main`; una nueva `revision` recarga solo las
  marcas de Hector y conserva las de Mathias guardadas en el navegador.
- `README.md` reescrito para un lector externo: hardware real (ESP32-C3, 2 × MG996R, buzzer GPIO5), arquitectura,
  modelos con su fuente (YOLO26n de Ultralytics, MediaPipe BlazeFace y Pose), instalación, ejecución, modos y STOP.
- Push de `camisetas` (los 3 commits locales y los de hoy). **Integrar los PR #3 → #4 → #5 a `main` quedó sin hacer**:
  el clasificador de permisos lo bloqueó por ser un merge sin revisión; lo tiene que hacer el usuario o autorizarlo.
- Se vio que el repo en GitHub es **público** (`gh repo view`), aunque `CLAUDE.md` decía privado (se resolvió a la tarde).

Commits: `c929971`, `ffdf9e1`. Tests: 219.

**Tarde: repo público, guía PDF, informe técnico y diagramas editables**
- El repo queda **público** (decisión y regla en `CLAUDE.md`: nada de datos personales, claves ni imágenes de personas).
- **Guía completa en PDF** `docs/guia/Guia_Keepon_pro.pdf` (18 capítulos, 23 páginas, 19 diagramas SVG): construcción,
  hardware, pines, PWM y perfil trapezoidal, firmware, software, decisiones y resultados. Fuente `docs/guia/guia_keepon.html`,
  generada con WeasyPrint.
- **Informe técnico** `docs/informe/Informe_técnico.ipynb`: la plantilla del grupo completada (portada, integrantes,
  hardware, arquitectura, eventos, modos, parámetros desde `config.yaml`, resultados), con las celdas de código
  ejecutadas sin errores y las figuras embebidas (sube tal cual a Colab). Se agregó la figura de las camisetas de
  referencia. Quedan `[Completar]`: video, ZIP, foto del robot, captura del overlay, aportes, uso de IA, latencia.
- `docs/informe/Informe_técnico_v2.ipynb` (versión del usuario; entró sin querer en `e79b5e1`): cada diagrama tiene
  ahora su **`.drawio` editable** en `docs/informe/diagramas/` (19 archivos: 12 del v2 y 7 más de la guía, con
  `LEEME.md`). Conversor `docs/informe/fuente/svg_a_drawio.py` (SVG → mxGraph; textos fusionados en su caja).
- `docs/hardware/diagrama_sistema/index.html`: **buzzer en el GPIO5** (cable I/O desde la fila de arriba; nota de por qué no el
  GPIO10) y foto de los **MG996R nuevos** en pitch y roll (`fotos/mg996r_nuevo.jpg`). `pruebas_buzzer/` también al GPIO5.
- Merge de los PR #3 → #4 → #5: sigue bloqueado por el clasificador; lo hace el usuario.

Commits: `c5c3e2e`, `e70da8a`, `2f98712`, `db6f77e`, `cfac015`, `e79b5e1`, `f85a0de`, `9b103fb` (todos subidos).

## 05/11/2026
**Servos nuevos de pitch y roll** (rama `camisetas`, sin commitear hasta el cierre)
- El grupo consiguió dos **TowerPro MG996R** nuevos: reemplazan al HS-7955TG (pitch) y al MG996R con zona muerta (roll).
  Mismos pines (GPIO1 y GPIO4).
- Cero sin horn con `prueba_servo.ino` (horn calzado en 1500 µs) y extremos montados. **Pitch**: +30° = 1174 µs,
  −20° = 1717 µs, llega bien a los dos; pulso mayor = la cara BAJA → `signo: −1`; centro 1500; límites 1100/1800 µs.
  **Roll** sin carga: +217 µs = +20° justos (antihorario visto de frente al eje), −217 µs casi 20°; centro 1500, signo −1
  (el del anterior en el mismo montaje, **sin verificar montado**), `compensacion_us: [0, 0]` (no tiene la zona muerta).
- Herramientas: `pruebas_servos/mover_servos.py` (en la Pi, ángulos en grados con los tres ejes, límites de seguridad
  en la ESP32; para `prueba_servo.ino`). En la notebook se usó un puente por FIFO (fuera del repo).
- Los MG996R **sin pulso quedan flojos**: al cargar el firmware (la ESP32 se reinicia) la cabeza cae en pitch.

**Suavidad de los movimientos** (videos del usuario en `video/`, ignorado por git: tienen personas)
- 1.ª corrida: "golpetea". Se probó bajar `gaze.kp` 4 → 2,5, `ema` 0,5 → 0,3 y `amax` de pitch/roll a 250/200 °/s²:
  el **yaw quedó peor** y después **los tres vibraban más**. Diagnóstico con el usuario: **quietos no vibran; vibran
  moviéndose lento** (avanzan a saltitos por la banda muerta). `deadzone` 0,04–0,05 dejaba la cara a 1,5–3° del centro.
- Causa: en modo velocidad la referencia avanzaba un poco en cada ciclo (40 J/s) y el Observador barría con una senoide
  lenta: los servos se arrastraban.
- **Mirada por objetivo** (`gaze.modo: objetivo`): dirección = posición del cuello AL SACAR LA FOTO (historia en
  `Robot._historia`, del espejo del firmware) + error en la imagen; la referencia salta ahí si se corrió más de 2,5° y
  queda quieta. Solo se corrige con fotos sacadas con el cuello quieto (`quieto_deg` 1°). En el simulador, cambios de
  referencia: persona quieta 25 → 8 (después 0), camina a 8 °/s 300 → 29, va y viene 264 → 40; salto a 25° con 150 ms
  de atraso: se pasaba a 29,2° → 25,0°.
- **Observador por miradas** (`observer.modo: miradas`): quieto donde estaba 2 s, después de punto en punto
  (±40°, ±15°) con pausas de 2 s.
- Velocidades de vuelta arriba: `vmax` 180/120/120 °/s, `amax` 600/400/300 °/s². `kp`/`ema` aceptan un valor por eje.
- El simulador le pasaba al robot `world_age=0` con 60 ms de latencia en la cámara sintética: ahora la edad real.
- Firmware cargado tres veces en la ESP32 por la Pi (`bash scripts/cargar_firmware.sh`), con la cabeza sostenida.
  **La versión final (mirada por objetivo y miradas) no se probó todavía en el robot.**
- Panel sin Tailscale: `http://172.16.240.92:8081` (IP del Wi-Fi de la Pi, la da el router).

Tests: 207 → 219 (`tests/test_gaze_por_eje.py`, `tests/test_mirada_objetivo.py`).

## 04/11/2026
**Panel del celular y arranque** (rama `panel-arranque`, PR #4 sobre `diseno-v6-vigente`)
- El servicio moría ~10 s después de cerrar el SSH: faltaba **linger** (`loginctl enable-linger r2d2`, lo corrió el usuario).
- Panel siempre prendido como servicio aparte (`scripts/keepon-panel.service`, puerto 8081; `keepon panel-on/off`) con
  botones **Encender / Apagar** (`systemctl --user --no-block start/stop keepon`, sin shell). `robot_vivo.sh` no lo duplica.
- **Sonidos del operador: el último pedido gana** (antes se descartaban los superpuestos y "a veces no sonaba").
- **Apagar vuelve a HOME**: el STOP enclavado hacía que la ESP32 rechazara el HOME. Ahora RESUME + HOME y espera a que
  el STATE llegue (`ir_a_home_y_esperar`, 5 s, log `FIN: en HOME`). Test de regresión.
- **Buzzer intermitente: era un cable jumper con falso contacto** (lo encontró el usuario). Se probó el GPIO7 (`c1759c2`)
  y se revirtió: sigue en el **GPIO5**. Sonaba con los 6 V apagados y no con los servos andando → era el cable, no ruido.
- **Volumen del buzzer desde el panel** (0–100 %): comando `VOL` nuevo en el protocolo (FW_VERSION 2, aceptado con STOP),
  firmware, simulador y tests de conformidad; se guarda en `~/keepon/run/volumen` y se manda al reconectar.
- ME_MIRA: el modo Tímido "igual me sigue la mirada". Se agregó el ángulo cara→cámara al overlay (`angulo N`) y a la
  línea ESTADO (`mira mín/mediana (<15°: a/b)`). Ya con la mirada corrida hacia abajo dio mediana 8° y 30/42 bajo 15°:
  falta volver a probar el Tímido.

**Camisetas** (rama `camisetas`, PR #5 sobre `panel-arranque`)
- `pruebas_camisetas/grabar.sh` (cámara con el robot apagado, pitido del buzzer cada 20 s) y `evaluar.py`. Tomas de 60 s
  a 1,2 / 1,8 / 2,5 m, de frente, luz del laboratorio: Olimpia titular, Cerro 2026 mitad y mitad, roja lisa, azul marino
  lisa. Quedan **solo en la Pi** (`~/keepon/capturas/camisetas/`), con consentimiento; borrarlas al cerrar el detector.
- Colores con la NoIR: azul marino **violeta** (H 116–145), igual en Cerro y en la lisa; rojo igual en Cerro y en la lisa;
  la franja de Olimpia marrón violácea (V 38–54) con el logo blanco adentro.
- `keepon/camiseta.py`: torso desde los hombros de Pose; Cerro = columnas rojas y azules con borde vertical; Olimpia =
  claro → franja oscura → claro (brillos relativos, blanco poco saturado). Filtro 6/6 cuadros por persona en `Eventos`.
  Corre en el proceso de pose (pose 7–10 Hz, igual que antes).
- Videos: Olimpia 82 % (99 % desde los 10 s; antes estaba muy cerca), Cerro 98 %, **lisas 0 % de falsos positivos**.
- La cámara (±14° vertical) no veía la camiseta con la cara centrada → `gaze.mirar_abajo_deg: 8`.
- **En vivo:** Olimpia → polca, Cerro → abucheo, roja y azul lisas → nada.

Commits: `67806d8` … `ba452ea`. Tests: 164 → 207.

## 03/11/2026
**Diseño v6 y calibración con la cabeza montada**
- El modelo vigente pasa a ser el **v6 R4** (`docs/diseno_v6/`, ver `LEEME_GIT.md`). Se versionan ≈ 20 MB de 228 (fuentes,
  documentación, SLDPRT/STEP/vistas de la R4); ZIP, historial y evidencias en el `.gitignore`. Rama `diseno-v6-vigente`, PR #3.
- Calibración en `neck.servos`: yaw cero 1500 / signo −1 (horn reubicado: estaba corrido ~130°), pitch 1400 / +1, roll 1450 / −1
  (disco reubicado: en 1500 la cabeza topaba). Roll limitado a ±20° (a +25 al límite de la pared, a +30 toca).
- **Compensación de zona muerta** en el firmware (`compensacion_us`, roll `[0, 151]`): de +25 a 0 el MG996R quedaba en +10.
  Se probó 110 → faltaban ~5°; 165 y 159 se pasaban; 151 vuelve bien a 0.
- Herramientas de calibración en la Pi (fuera del repo, `~/keepon/calibracion/`): `puente_serie.py` (reconecta solo),
  `consola` (+N/−N/pulso) y `m`, para `prueba_servo.ino`. Al primer pulso de 1500 el yaw saltó ~180° y tiró del cable:
  el primer pulso de un eje sin pulso es un salto; llevar la cabeza cerca antes.
- `scripts/prueba_movimientos.py`: posturas en grados con Enter (`--posturas "0 0 15; 0 0 0"`), manda RESUME al arrancar.

**Robot real con cámara**
- `SerialLink(espejo_cfg=…)`: un `SimESP32` espejo da la posición del cuello a 100 Hz; compara con cada STATE (desvío 0,00° en
  uso real). `sim_scenario.py --serial`: el escenario de 30 s contra la ESP32 de verdad.
- Cámara: ahora en `i2c@88000` y montada invertida → `camera.ros_camera` y `orientation_deg: 180` (lo hace `camera_ros`).
  Centro óptico provisorio = centro de la imagen: con el de la calibración ajena el robot centraba la nariz ~6,5° corrido.
- `scripts/robot_vivo.py` / `.sh`: percepción (personas + pose) → eventos → robot → ESP32, a 39–40 Hz; personas 13–20 Hz,
  pose 9–13 Hz, edad del cuadro 64–255 ms. Overlay T7 (`keepon/overlay.py`) en `/keepon/overlay`.
- `keepon/eventos.py`: ME_MIRA sostenido (0,5 s / suelta 0,3 s), SALUDO (muñeca sobre el hombro, 3 cambios de sentido en
  2,5 s, amplitud en anchos de hombros; un gesto = un evento) y SALIENDO (borde y alejándose, o en el límite de yaw).
- Curiosidad (T3 d): con la persona quieta 3 s, roll ±15° 2 s. Primero no se disparaba nunca (el error del control oscilaba);
  "quieto" pasó a ser la dirección de la persona (ángulo del cuello + error).
- Modos (T5): `Robot.set_modo`, beep de confirmación (OPERADOR, sólo buzzer), Tímido / Atrevido / Maleducado (`Mode`, prioridad 3).
- **Bug del firmware**: watchdog y fin de sonido falsos por restar tiempos sin signo (la línea llega con `millis()` y el paso
  usa su instante programado). Con `dif_ms` con signo: 60 s a 40 Hz sin ningún WATCHDOG; 6 min del robot real, tampoco.
- Demo: servicio de usuario `keepon.service` + `scripts/keepon` (Pi) + `scripts/k` (notebook, por SSH); FIFO
  `~/keepon/run/comandos`; parar vuelve a HOME. Panel del celular (PWA) `scripts/panel_web.py` en el puerto 8081.

**Buzzer**
- En el GPIO10 no sonaba con la cabeza armada (el firmware confirmaba DONE) → I/O al **GPIO5**, configurable (`buzzer.pin`).
  Volumen 0,25 → 0,12 a pedido. Comando `sonido NOMBRE` para probarlo.
- Al final: **suena con los servos quietos y se corta cuando se mueven** (prueba A/B directa por serie: la ESP32 toca las dos
  polcas completas). Sospecha: contacto flojo del cable por el cuello, o ruido de los servos en GND/3V3. Sin resolver.
- Se pidió la polca completa (≈ 80 compases) y después se descartó: sigue el fragmento de 8 compases.

Commits: `5406806` … `297b8af` (rama `diseno-v6-vigente`, PR #3). Tests: 121 → 164.

## 15/10/2026 · estado del hardware en ese momento
- La ESP32-C3 **desde el 14/10 está conectada a la Pi y tiene cargado el firmware del robot** (`firmware/keepon_fw/`).
- **La cámara no está conectada a la Pi** (14/10): no lanzar nada de percepción sin confirmarlo.
- Los tres servos juntos andan bien a velocidad alta (12/10, fuente de laboratorio a 6 V).
- Conectado directo por USB-C, el powerbank alimenta bien a la Pi (14/10, en el banco): 5,08 V, `throttled=0x0`.

## 14/10/2026 (noche) y 15/10/2026
- **Firmware del robot hecho y cargado** en la ESP32-C3, conectada a la Pi (`firmware/`, ver su README). El núcleo da exactamente las mismas respuestas y posiciones que `SimESP32` (34 tests, con fuzzing). En la ESP32 real, `prueba_firmware_real.py`: **30 de 30 OK**, latencia PING→ACK de 4,4 ms y el movimiento llega en el mismo tiempo que en el simulador. Sin servos ni buzzer conectados: falta probarlo con la fuente de 6 V (y definir `signo` al montar) y con el buzzer.
- `sim_esp32.py`: el watchdog y el fin del sonido comparan con un margen de 1e-9 (el tiempo acumulado en float saltaba un paso según el redondeo; el firmware cuenta ms enteros).
- `docs/PROTOCOLO.md` pasado a la ESP32-C3 con CH340; `config.yaml` → `serial.port` es el by-id del CH340.
- Alimentación: fuente de laboratorio para los servos y powerbank para la Pi (ver Hardware). La Pi por USB-C desde el powerbank: 5,08 V, `throttled=0x0`.
- Buzzer: simulador de sonidos en `pruebas_buzzer/` (publicado en https://claude.ai/artifact/7wyNPrzj6QqcPJQvrpaPwB), POLCA de Olimpia transcrita de la partitura (compases 1–8, 7,104 s), POLCA_CERRO es un marcador. Comprar el buzzer **pasivo** de electronica.com.py.
- **La cámara no está conectada a la Pi** (14/10): no lanzar nada de percepción.
- **Compatibilidad con Windows:** Git for Windows no restauraba `docs/micro servo mg90s ` ni `docs/micro servo sg90 ` (terminaban en espacio). Se arregló en el **PR #1** (rama `compatibilidad-windows`, integrado en `main`) y después se pasaron a guion bajo **todas** las carpetas y archivos con espacios (`docs/hardware/hojas_de_datos/micro_servo_mg90s/`, `docs/hardware/hojas_de_datos/servo_HS-7955TG_titanium_gear/`, `docs/hardware/fotos/camera_Noir_module_3/`, `pruebas_buzzer/notas_polca_de_olimpia/`, `Captura_desde_...png`, etc.). Ya no hay rutas con espacios en el repo ni en la Pi. La carpeta del proyecto en la notebook (`Keepon pro `) sí termina en espacio, pero está fuera del repo.
- **Camisetas (15/10):** plan decidido: **reglas de color y patrón sobre el torso** (la guía las permite expresamente), no una red entrenada. Torso debajo de la cara (BlazeFace) o en el centro del recuadro de YOLO, reducido a ~48×48; cada píxel → blanco/negro/rojo/azul/otro; **Olimpia** = franja horizontal negra con blanco arriba y abajo; **Cerro** = rojo **y** azul en partes grandes del torso separados por bordes verticales (no exigir rayas); filtro 6 cuadros para confirmar y 6 para soltar, por persona. Para la NoIR: luz LED en la demo, balance de blancos y exposición fijos; si no alcanza, la Camera Module 3 estándar (mismo tamaño y cinta). **El detector todavía no está escrito.**
  - Imágenes de referencia en `pruebas_camisetas/imagenes_referencia/` (`olimpia/`, `cerro/`, `suplentes/`, `trampas/`, sin personas, con `fuentes.txt`; ver su README). Mostraron: la **titular 2026 de Cerro es mitad roja y mitad azul, sin rayas**; el azul de Cerro es **marino oscuro** (con la NoIR puede parecer negro) y el rojo casi bordó; **el Barcelona es casi igual a Cerro** (limitación a explicar en la defensa); las suplentes no tienen el patrón titular. Falta una remera blanca lisa.
  - Para probar con la cámara: el usuario tiene una **remera negra** (prueba negativa; con tiras rojas y azules pegadas sirve de "Cerro" casero, y con una franja blanca de "Olimpia al revés", que no tiene que detectar).
- **La Pi no respondió por SSH el 15/10** (timeout por Tailscale): falta sincronizarle las imágenes de las camisetas.
- Próximo: el detector de camisetas (probado con las imágenes de referencia), integrar `SerialLink` con el robot sobre la ESP32 real (`scripts/sim_scenario.py` usa SimLink), reconexión automática de `SerialLink`, y la prueba con los servos.

## 30/09/2026 · rendimiento medido en la Pi (1 persona)
- Personas + rostros: **16,9 Hz** (YOLO 34 ms + rostros 10 ms), edad del resultado 74 ms.
- Pose: **10,0 Hz**, edad 149 ms. CPU total: 239 % de 400 %.
- Rostro encontrado en el 80 % de las detecciones; ID estable. Detalle completo en `docs/ESTADO_PI.md`.

## 14/10/2026 (tarde)
- **Revisión de arquitectura de Codex** en `docs/revisiones/REVISION_CODEX_ARQ.md`: mantener la ESP32 (el enunciado pide microcontrolador + protocolo; watchdog independiente de Linux), Pi en la cabeza por la cinta de 150 mm, cara plana. **Sus 4 fallos de código se corrigieron el 14/10** (tests 7–10 de `tests/test_regresiones_codex.py`): el control de mirada y el foco usan cx/cy (`World.from_cfg`, `World.K`); una cola por proceso de tamaño 2 con `_put_latest` (descarta lo viejo, nunca bloquea); `nod_period_s` 1,0 s (≈ 237 °/s²); `Robot.stop()` enclava primero y reintenta el STOP si el enlace falla. **Falta medir en la Pi la cola nueva** (`perception_bench.py`): la Pi no respondía por SSH. Quedan sin hacer los puntos 3 (asociar pose y persona por timestamp) y 6 (watchdog/reanudación) de la misma lista. `docs/hardware/diagrama_sistema/index.html` ya está en la v3.
- **Modelo mecánico v4** en `docs/cad_anteriores/keepon_v4_cad/` (14/10, el vigente): cabeza, servos, soportes y horquilla de la v3 sin cambios, con la disposición de la v1 (eje de pitch sobre el de yaw, base en U de 64 × 116 en lugar del plato Ø146: el vuelco sobre el yaw baja a 0,81 kgf·cm). Caja base de 182 × 133 × 74 con el **powerbank Xiaomi PB2020MI** (128 × 73 × 32, 5 V/3 A a la Pi por el GPIO), los **bornes de la fuente de laboratorio** y el interruptor en la pared de atrás, y la bornera de 6 V con el capacitor, la ESP32 y el buzzer en una bahía adelante. El lugar de la LiPo quedó libre (se podría achicar la caja ~50 mm en Y; ver el README). Script `fuente/keepon_v4_cad.py` (importa la v3), macro de relaciones y `componentes_v4.txt`. `docs/hardware/diagrama_sistema/index.html` ya está en la v4 con la alimentación nueva.
- **Modelo mecánico v3** en `docs/cad_anteriores/keepon_v3_cad/` (reemplaza al v2 para imprimir; el cuello se importa del v2): cabeza de 75 × 104 × 40 mm con la **Pi parada adentro** sobre la placa de roll y **la cámara como nariz**, en el centro de la cara (a 38 mm sobre el eje de roll), con los ojos decorativos arriba. En la Pi 5, los conectores CAM/DISP son perpendiculares al borde de los HDMI: la cinta sale a lo largo del lado largo, corrida 19 mm del centro. Cinta fija con una U de radio 6,5 mm y un doblez en Z (dos pliegues a 45°) que la lleva al centro (147 de 150 mm). Sin interferencias en 15 poses.
  - Consecuencias: **la Pi se alimenta por el GPIO** (el USB-C queda tapado por la cinta), los USB-A quedan arriba (cable acodado a la ESP32), y **el pitch se monta con +30° arriba y −20° abajo** (más de ~22° abajo la cara toca el plato).
  - **Falta verificar en la Pi:** hacia qué extremo sale la cinta del conector (`PI_CSI_SALIDA`, se asumió el USB-C), el largo exacto de la cinta y la altura del Active Cooler.
- Los intrínsecos de `config.yaml` (fx = 948 → 37°) probablemente no son de esta cámara a 640 × 480 (la estándar tiene 66°): hay que calibrar con un tablero.
- La Pi no respondió por SSH en toda la sesión (timeout por Tailscale).
- CadQuery 2.8 en `~/cq_env` (con VTK para las vistas: `docs/cad_anteriores/keepon_v3_cad/fuente/vistas.py`).

## 13/10/2026
- **Roll pasó al MG996R** (decisión del grupo; MG90S de repuesto). Se caracterizó en el banco: ver la sección "MG996R (13/10)" de `pruebas_servos/README.md`. Falta anotar su sentido de giro.
- **El banco ya quedó conectado como en el robot:** RDS3218 n.º 2 en GPIO0 (yaw), HS-7955TG en GPIO1 (pitch), MG996R en GPIO4 (roll). Barrido 0 ↔ 45° los tres juntos a ≈ 180 °/s, sincronizados con `w`: bien. `prueba_servo.ino` sigue en la ESP32-C3, conectada a la notebook.
- Manejo por serie sin reiniciar la ESP32: un proceso Python deja el puerto abierto y reenvía los comandos de un FIFO. Para mandar varios ejes **a la vez**, escribir todas las líneas juntas (`printf 'e 0\nb 1500 1843\ne 1\nb 1500 1000\n' > fifo`). Abrir el puerto de cero reinicia la ESP32 una vez (todos los ejes quedan sin pulso).
- **Próxima sesión: empezar el firmware del robot** (`firmware/`, hoy vacío; Arduino con arduino-cli, como `prueba_servo`). Puntos de partida:
  - **Especificación:** `docs/PROTOCOLO.md` + `keepon/sim_esp32.py` (sesión HELLO, `J S CANCEL PING STOP RESUME HOME`, ACK/DONE/ERR/STATE, STOP enclavado, watchdog de 500 ms, dedupe de sonidos por seq) + `keepon/trajectory.py` (copiar la fórmula cerrada `_v_max_to_stop`, rampa a 100 Hz).
  - **Grados → µs** con `neck.servos` de `config.yaml` (centro, `grados_por_us` simple o `[lado <1500, lado >1500]`, min/max, `signo`). Pines: yaw GPIO0, pitch GPIO1, roll GPIO4, buzzer GPIO10, en timers LEDC separados (servos 50 Hz / 14 bits, buzzer aparte). Se puede reusar `escribir()` y `ledcAttach` de `prueba_servo.ino`.
  - **Por servo:** el HS (y el RDS) sin pulso **se quedan firmes**, el MG996R **queda flojo** → en STOP/watchdog seguir mandando el último pulso a los tres. El primer pulso después de encender salta a velocidad máxima → arrancar en una postura conocida (home). **Roll (MG996R):** banda muerta de ~10° → mandarle el objetivo de un solo movimiento en vez de acercarse de a poco.
  - **Pruebas de conformidad:** correr los mismos escenarios contra `SimESP32` y contra la ESP32 real por `SerialLink`.
  - Antes de empezar: anotar el sentido de giro del MG996R (pulso mayor = ¿horario o antihorario?, de frente al eje) y corregir `serial.port` de `config.yaml`, que todavía dice `/dev/ttyACM0` (ESP32-S3): es `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` (CH340).
  - La ESP32 sigue en la notebook; para la integración hay que pasarla a la Pi.

## 07/10/2026
- Al cambiar servos, apagar antes la fuente: enchufar uno con la fuente prendida desconectó la ESP32 del USB (y otra vez se reinició por pérdida de alimentación, `rst:0x1 (POWERON)` en el log).
- Si el puerto está ocupado, es casi siempre un `serial-monitor` abierto por el usuario (`fuser -v /dev/ttyUSB0`): pedir que lo cierre, no matarlo.
- Todo commiteado y subido. Los dos visores eligen la cámara por nombre (la segunda NoIR había corrido los índices); ambos probados con la cámara real.
- **`ver_personas.sh` quedó corriendo en la Pi** y ocupa la cámara. Detenerlo con `~/keepon/ver_personas.sh stop`.
- Pendiente: revisar el flex de la segunda NoIR (`i2c@88000`) o desconectarla.
- Se les pidió a los usuarios probar el visor (mirar / no mirar, girar la cabeza, levantar la mano, cruzarse) y anotar los grados de desvío para calibrar el umbral de ME_MIRA.
