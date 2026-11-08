# Estado del proyecto (08/11/2026)

Foto del estado actual. La historia está en `docs/BITACORA.md`; lo que falta, en `docs/PENDIENTES.md`.
Al cerrar una sesión (`/cerrar`) se actualiza este archivo, no `CLAUDE.md`.

## Ramas y repo
- **Todo integrado a `main`** (08/11): PR #3 (diseño v6) → #4 (panel) → #5 (camisetas) → #6 (`movimiento-suave`:
  curva S, roll, Observador de la guía, HOME, Ejes, polca una vez, informe y README de presentación). Se trabaja desde `main`.
- GitHub: descripción y temas puestos; README con portada (imágenes en `docs/img/`).
- El repo en GitHub es **público** (decisión del 07/11).
- Documentación para un lector externo: `README.md`, `docs/consigna/CHECKLIST_TP.md` (al día el 08/11) y
  `docs/consigna/checklist_robotica_social.html`. Entrega: guía PDF `docs/guia/Guia_Keepon_pro.pdf`, informe
  `docs/informe/Informe_técnico.ipynb` (y `_v3`, la del usuario, con `docs/informe/diagramas/*.drawio`). El informe (las dos
  versiones) está al día con el 08/11; la guía PDF todavía describe solo el perfil **trapezoidal** y el Observador por miradas.
- La Pi está sincronizada con `movimiento-suave` en `135f882` (`~/keepon/.commit`).
- Tests: **257** (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q`); 36+ comparan el firmware con el simulador.

## Mecánica y hardware
- Modelo vigente: **v6 R4** (`docs/diseno_v6/LEEME_GIT.md`), armado. yaw = RDS3218 en la base; pitch y roll = TowerPro
  MG996R (el del roll se cambió el 08/11 por otro igual).
- Calibración (`neck.servos`): ceros yaw 1500 / pitch 1500 / roll 1500 µs; signos −1 / −1 / **+1** (roll verificado
  montado el 08/11: roll + = derecha vista desde atrás). El cero del roll se midió llegando desde la izquierda; falta
  desde la derecha (`compensacion_us`). Límites yaw ±70°, pitch −20/+30°, roll ±20° (±20 del roll recorrido sin tocar).
- Movimiento (`neck`): `vmax` 180/120/**250** °/s, `amax` 600/400/**900** °/s², **curva S** `suavizado_s`
  0,10/0,10/0,15 s (el roll rápido es una prueba sin resultado). Firmware cargado = config de `135f882`.
- **Vibración**: el yaw vibraba barriendo a 20 °/s de media (a 25, sin probar). El **roll vibra solo girando a la
  derecha en la zona negativa** (−20…0), con cualquier perfil probado: probable servo o carga (falta el banco).
- Los MG996R **sin pulso quedan flojos**: sostener la cabeza al cargar el firmware y al cortar los 6 V.
- Cámara NoIR en **`i2c@88000`**, montada invertida (`orientation_deg: 180`). Intrínsecos **provisorios** (sin tablero).
  Campo ≈ 37° × 28°.
- ESP32-C3 en la Pi con el **firmware del robot, FW_VERSION 2** (comando `VOL`), buzzer en **GPIO5** (anda; volumen
  desde el panel, guardado en `~/keepon/run/volumen`).

## Software del robot (en la Pi)
- `keepon` (servicio de usuario): cámara + servidor web + `robot_vivo.py` (percepción → eventos → robot → ESP32).
  Medido: lazo 36–39 Hz, personas 12–17 Hz, pose 7–10 Hz, edad del cuadro 96–135 ms.
- **Observador "exploracion"** (08/11, Tabla 1): centra, barre ±45° sin pararse (25 °/s de media, mínimo jerk), sacada
  rápida a un punto de interés cada 2 barridos con roll ±5°; al perder a alguien, primero mira donde estaba. Respaldo:
  `observer.modo: miradas | barrido`.
- **Mirada por objetivo** (`gaze.modo: objetivo`): salta adonde está la persona si se corrió más de 2,5° y queda quieta.
- **Comandos del operador** (prioridad 0): STOP (enclavado), **HOME** (va a 0 0 0 y queda hasta RESUME; probado),
  **Ejes** (yaw, pitch y roll en ~15 s y vuelve; sin probar en real), modos con su beep (corta cualquier sonido),
  sonidos, volumen.
- **Polca / abucheo: una vez por aparición** de cada persona (`cooldowns.CAMISETA_por_persona: null`); un saludo la corta.
- Funciona en real: seguimiento con foco e histéresis (la cara queda 8° arriba del centro), SALUDO + R2D2, curiosidad,
  modos, camisetas Olimpia/Cerro (roja y azul lisas: nada), overlay T7, log CSV.
- Dudoso: **ME_MIRA casi no se activa** en real (de él dependen la prioridad a quien mira, Tímido y Atrevido).
- Sin probar en real: SALIENDO + piropo (Maleducado), Ejes, la polca una vez, remera blanca lisa.
- Camisetas: videos de prueba **solo en la Pi**, `~/keepon/capturas/camisetas/`; borrarlos al dar el detector por bueno.

## Cómo se usa
- Celular: panel en `http://100.116.96.71:8081` (Tailscale) o la IP del Wi-Fi; **siempre prendido** (servicio
  `keepon-panel`). Botones Encender / Apagar, modos, STOP, Home, Resume, **Ejes**, sonidos, volumen. Si cambia
  `scripts/panel_web.py`: `systemctl --user restart keepon-panel` en la Pi.
- Notebook: `scripts/k arrancar | parar | estado | log | t | a | m | n | stop | resume | home | ejes | sonido POLCA | volumen N`.
- Overlay: `http://100.116.96.71:8080/stream_viewer?topic=/keepon/overlay`.
- El servicio `keepon` **no arranca al encender** (`scripts/k demo-on` para la demo). Con el robot corriendo, la cámara y
  la ESP32 están ocupadas. Después de sincronizar código, apagar y encender el robot para que lo cargue.
- Probar posturas a mano (robot apagado), en la Pi: `cd ~/keepon && ~/keepon_env/bin/python scripts/prueba_movimientos.py
  --pausa 3 --posturas "0 0 0; 0 0 20; 0 0 -20"` (un Enter por postura).
- Cambiar `vmax`/`amax`/`suavizado_s`: editar `config.yaml`, `scripts/k parar`, `bash scripts/cargar_firmware.sh` (regenera
  `generado.h`) y sincronizar la Pi (el espejo usa los mismos valores). El Observador y lo demás cambian sin firmware.
- Grabar prendas: `bash ~/keepon/pruebas_camisetas/grabar.sh camara`, luego `grabar.sh <nombre>` (60 s), luego `stop`.

## Rendimiento de referencia (30/09, 1 persona)
- Personas + rostros 16,9 Hz (YOLO 34 ms + rostros 10 ms), pose 10 Hz, CPU 239 % de 400 %. Detalle en `docs/ESTADO_PI.md`.
