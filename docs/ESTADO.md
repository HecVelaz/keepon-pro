# Estado del proyecto (08/11/2026, noche)

Foto del estado actual. La historia está en `docs/BITACORA.md`; lo que falta, en `docs/PENDIENTES.md`.
Al cerrar una sesión (`/cerrar`) se actualiza este archivo, no `CLAUDE.md`.

## Entrega y repo
- El robot se llama **Wall-E** (proyecto y repo: Keepon pro). Integrantes: Mathias Aguilar, Héctor Velázquez, Pablo
  Otazú, Pedro Vera.
- **Todo en `main`** (PR #3 a #7 integrados). Repo **público**: github.com/HecVelaz/keepon-pro, con README de portada.
  Mapa de la documentación: `docs/README.md`.
- **Release «Entrega final», etiqueta `v1.0-entrega`** = `da1e4d6` (ZIP del código). Copia local para entregar:
  `~/Documentos/Entrega_Wall-E/keepon-pro-v1.0-entrega.zip`. Si se cambia algo de la entrega, mover la etiqueta
  (force-push: pide autorización).
- **Informe**: `docs/informe/Informe_técnico_v3.ipynb` (versión final; `Informe_técnico.ipynb` es la anterior), completo
  y ejecutado. **Falta subirlo al Colab del Drive del usuario** y al aula virtual (archivos: domingo después del parcial).
- **Video**: https://youtu.be/raOJljv1mVU (3 min, las 8 pruebas en el robot real; tiempos en la sección 13 del informe).
- **Guía PDF para la defensa**: `docs/guia/Guia_Keepon_pro.pdf` (32 págs., capítulo 19 con preguntas probables). Se genera
  desde `guia_keepon.html` con WeasyPrint (no está en `.venv`: usar un venv aparte).
- Figuras regenerables: `scripts/diagrama_componentes.py`, `scripts/captura_panel.py` (Playwright), `scripts/figura_overlay.py`,
  `scripts/portadas_video.py` (portadas del video, salen en `video/`, fuera de git).
- Tests: **258** (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`); 36+ comparan el firmware con el simulador.
- **Pi sin sincronizar** desde `135f882`: le falta el arreglo del panel (botón Ejes) y la reorganización de `docs/`.

## Mecánica y hardware
- Modelo vigente: **v6 R4** (`docs/diseno_v6/LEEME_GIT.md`), armado. yaw = RDS3218 en la base; pitch y roll = TowerPro
  MG996R (el del roll, cambiado el 08/11).
- Calibración (`neck.servos`): ceros 1500 / 1500 / 1500 µs; signos −1 / −1 / **+1** (roll verificado montado: roll + =
  derecha vista desde atrás). Cero del roll medido llegando desde la izquierda. Límites yaw ±70°, pitch −20/+30°, roll ±20°.
- Movimiento (`neck`): `vmax` 180/120/250 °/s, `amax` 600/400/900 °/s², **curva S** `suavizado_s` 0,10/0,10/0,15 s
  (los valores del roll son una prueba).
- **Vibración**: el roll vibra solo girando a la derecha en la zona negativa (−20…0), con cualquier perfil: probable servo
  o carga (falta el banco).
- Los MG996R **sin pulso quedan flojos**: sostener la cabeza al cargar el firmware y al cortar los 6 V.
- Cámara NoIR en **`i2c@88000`**, invertida (`orientation_deg: 180`), intrínsecos **provisorios** (sin tablero).
- ESP32-C3 con el firmware del robot (FW_VERSION 2), buzzer en **GPIO5**.

## Software del robot (en la Pi)
- `keepon` (servicio de usuario): cámara + servidor web + `robot_vivo.py`. Medido: lazo 36–39 Hz, personas 12–17 Hz,
  pose 7–10 Hz, edad del cuadro 96–135 ms.
- Probado en el robot (video del 08/11): ejes, Observador «exploracion», seguimiento con mirada por objetivo y dos
  personas, saludo, camisetas Olimpia/Cerro, Tímido/Atrevido/Maleducado con cambio de modo desde el panel, arbitraje
  (saludo durante la polca, polca una vez por aparición), pérdida y recuperación, STOP, HOME, overlay y log.
- Pendiente de validar: umbral de **ME_MIRA** (15°) con la cámara calibrada; remera blanca lisa real; latencia de punta a
  punta (estimada ≈ 130–170 ms).
- Camisetas: videos de prueba **solo en la Pi**, `~/keepon/capturas/camisetas/`; borrarlos al dar el detector por bueno.

## Cómo se usa
- Celular: panel en `http://100.116.96.71:8081` (Tailscale) o la IP del Wi-Fi; **siempre prendido** (`keepon-panel`).
  Encender / Apagar, modos, STOP, Home, Resume, Ejes, sonidos, volumen. Si cambia el panel:
  `systemctl --user restart keepon-panel` en la Pi.
- Notebook: `scripts/k arrancar | parar | estado | log | t | a | m | n | stop | resume | home | ejes | sonido POLCA | volumen N`.
- Overlay: `http://100.116.96.71:8080/stream_viewer?topic=/keepon/overlay`.
- El servicio `keepon` **no arranca al encender** (`scripts/k demo-on` para la demo). Después de sincronizar código, apagar
  y encender el robot para que lo cargue.
- Cambiar `vmax`/`amax`/`suavizado_s`: editar `config.yaml`, `scripts/k parar`, `bash scripts/cargar_firmware.sh` y
  sincronizar la Pi. El Observador y lo demás cambian sin firmware.
- Probar posturas a mano (robot apagado), en la Pi: `scripts/prueba_movimientos.py --pausa 3 --posturas "0 0 0; 0 0 20"`.

## Rendimiento de referencia (30/09, 1 persona)
- Personas + rostros 16,9 Hz (YOLO 34 ms + rostros 10 ms), pose 10 Hz, CPU 239 % de 400 %. Detalle en `docs/ESTADO_PI.md`.
