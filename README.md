<div align="center">

# Wall-E

**Proyecto Keepon pro** · **Cabeza robótica social de 3 grados de libertad con visión artificial**

µTP *Robótica Social* · Robótica II · Facultad de Ingeniería, Universidad Nacional de Asunción (FIUNA) · 2026

**Integrantes:** Mathias Aguilar · Héctor Velázquez · Pablo Otazú · Pedro Vera

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Raspberry Pi 5](https://img.shields.io/badge/Raspberry%20Pi%205-Ubuntu%2024.04-C51A4A?logo=raspberrypi&logoColor=white)
![ROS 2 Jazzy](https://img.shields.io/badge/ROS%202-Jazzy-22314E?logo=ros&logoColor=white)
![ESP32-C3](https://img.shields.io/badge/ESP32--C3-Arduino-E7352C?logo=espressif&logoColor=white)
![Tests](https://img.shields.io/badge/tests-257%20pasan-2f6b4f)

<img src="docs/hardware/fotos/Wall-e_frontal.jpeg" alt="Wall-E de frente: cabeza negra impresa en 3D con dos ojos grandes, la cámara como nariz y el buzzer debajo, sobre la horquilla de pitch y la base" width="560">

<img src="docs/hardware/fotos/Wall-e_costado1.jpeg" alt="Wall-E visto de costado, con el powerbank en la base" width="275"> <img src="docs/hardware/fotos/Wall-e_costado2.jpeg" alt="Wall-E visto desde el otro costado, con el cableado de los servos" width="275">

*Wall-E armado: diseño mecánico propio v6 R4, impreso en 3D. La cámara es la nariz; la Raspberry Pi va dentro de la cabeza.*

</div>

Wall-E detecta a las personas, las sigue con la mirada, responde a saludos y a quién lo mira, reconoce las camisetas de
**Olimpia** (toca la polca) y **Cerro** (abuchea), y tiene cuatro personalidades que se cambian desde el celular. Todo
corre en una Raspberry Pi 5 en Python; una ESP32-C3 mueve los tres servos con trayectorias suaves y toca los sonidos en
un buzzer, sin bloquearse nunca.

## Video de la demostración

<div align="center">

[![Video de la demostración de Wall-E: las 8 pruebas en 3 minutos (clic para verlo en YouTube)](docs/img/video_miniatura.jpg)](https://youtu.be/raOJljv1mVU)

**[▶ Ver en YouTube](https://youtu.be/raOJljv1mVU)** · las 8 pruebas del robot en 3 minutos

</div>

## Entregables

| | |
|---|---|
| 🎬 **Video de la demostración** (3 min) | [youtu.be/raOJljv1mVU](https://youtu.be/raOJljv1mVU): las 8 pruebas del robot |
| 📓 **Informe técnico** (cuaderno Colab, ya ejecutado) | [`docs/informe/Informe_técnico_v3.ipynb`](docs/informe/Informe_t%C3%A9cnico_v3.ipynb) · versión anterior: [`Informe_técnico.ipynb`](docs/informe/Informe_t%C3%A9cnico.ipynb) |
| 📘 **Guía completa del proyecto** (PDF con diagramas) | [`docs/guia/Guia_Keepon_pro.pdf`](docs/guia/Guia_Keepon_pro.pdf): construcción, hardware, control, software y decisiones |
| ✅ **Consigna, casilla por casilla** | [`docs/consigna/CHECKLIST_TP.md`](docs/consigna/CHECKLIST_TP.md) (qué pide la consigna y dónde está en el código) |
| 📄 **Consigna** | [`docs/consigna/2026S2uTP_RoboticaSocial.md`](docs/consigna/2026S2uTP_RoboticaSocial.md) |
| 🔌 **Diagrama eléctrico y del sistema** | [`docs/hardware/diagrama_sistema/`](docs/hardware/diagrama_sistema/index.html) |
| 🧩 **Diagramas editables** (draw.io) | [`docs/informe/diagramas/`](docs/informe/diagramas/LEEME.md) |

## Qué hace

| Situación | Respuesta del robot |
|---|---|
| No hay nadie | **Observador**: centra la vista y explora la escena con barridos lentos, sacadas rápidas a puntos de interés y pequeñas inclinaciones de roll |
| Aparece una persona | **Seguimiento**: la mira en un solo movimiento rápido y se queda quieto; prioriza a quien lo mira, con histéresis para no saltar entre personas |
| Alguien saluda con la mano | 3 cabeceos + sonido tipo R2D2 |
| Camiseta de **Olimpia** | Polca de Olimpia **sin dejar de seguir** a la persona (una vez por aparición) |
| Camiseta de **Cerro** | Abucheo. Las prendas lisas rojas o azules no disparan nada |
| Modo **Tímido** y alguien lo mira | Aparta la mirada y vuelve a espiar de a poco |
| Modo **Atrevido** y alguien lo mira | Sostiene la mirada y levanta el mentón |
| Modo **Maleducado** y alguien se va | Le silba un piropo |
| La persona queda quieta | **Curiosidad**: inclina la cabeza de costado |
| Operador (celular) | STOP enclavado, HOME, demostración de los 3 ejes, cambio de modo con su beep, sonidos y volumen |

<div align="center">
<img src="docs/img/estados_modos.png" alt="Diagramas de estados de los modos Tímido, Atrevido y Maleducado" width="720">

*Diagramas de estados de las personalidades.*
</div>

## Panel del celular

El robot se maneja desde el teléfono con una **app web propia** que sirve la Raspberry Pi (`http://<ip-de-la-pi>:8081`)
y se instala con "Agregar a pantalla de inicio": encender y apagar, STOP, los cuatro modos, Home, la demostración de
los ejes, los sonidos con su volumen y el estado del robot en vivo. Código: [`scripts/panel_web.py`](scripts/panel_web.py)
(servidor, con una lista cerrada de comandos) y [`scripts/panel/`](scripts/panel/) (la página).

<div align="center">
<img src="docs/img/panel_celular.png" alt="Panel del celular: captura de la app con los botones Encender, Apagar, STOP, modos de personalidad, Home, Resume, Ejes, sonidos, volumen y estado en vivo" width="900">
</div>

## Cómo funciona

<div align="center">
<img src="docs/img/arquitectura.png" alt="Arquitectura: cámara, dos procesos de percepción, modelo del mundo, foco de atención, comportamientos, árbitro, actuadores y ESP32" width="820">
</div>

1. **Percepción** en dos procesos paralelos: personas con **YOLO26n** (NCNN, 256 px) + tracker propio por IoU + rostros con
   **MediaPipe BlazeFace** y orientación de la cara con solvePnP (12–17 Hz); pose del cuerpo con **MediaPipe Pose** y
   detector de camisetas propio por color y patrón (7–10 Hz).
2. **Modelo del mundo**: personas con ID y eventos con filtros temporales (ME_MIRA, SALUDO, CAMISETA_OLIMPIA,
   CAMISETA_CERRO, SALIENDO).
3. **Foco de atención**: elige a quién mirar (primero a quien mira al robot; si no, la persona más grande y centrada),
   con 1,5 s de histéresis.
4. **Comportamientos** que proponen acciones y un **árbitro propio** que reparte los dos recursos exclusivos
   (cuello y buzzer) por prioridad, con interrupciones, cooldowns y STOP. Nunca hay dos controladores escribiendo al cuello.
5. **ESP32-C3**: perfil trapezoidal con **curva S** a 100 Hz por eje (límites de posición, velocidad, aceleración y jerk),
   sonidos sin `delay()`, watchdog de 500 ms y STOP enclavado. Protocolo serie propio: [`docs/PROTOCOLO.md`](docs/PROTOCOLO.md).

| Prioridad | Comportamiento | Cuello | Buzzer |
|---|---|---|---|
| 0 | Operador: STOP, HOME, Ejes, sonidos | ✔ | ✔ |
| 1 | Saludo | ✔ | ✔ |
| 2 | Camiseta | | ✔ |
| 3 | Reacción de personalidad | ✔ | ✔ |
| 4 | Seguimiento | ✔ | |
| 5 | Observador | ✔ | |

Polca y seguimiento usan recursos distintos, así que conviven: el robot silba mientras sigue a la persona. Si esa
persona saluda, el saludo (prioridad 1) interrumpe a los dos y al terminar el seguimiento retoma el cuello. Así se ve en
el escenario simulado de 30 s del repositorio (`python scripts/sim_scenario.py --plot`), con el árbitro, los
comportamientos y el control reales:

<div align="center">
<img src="docs/img/escenario_simulado.png" alt="Escenario simulado de 30 s: ángulos de los tres ejes, error de la mirada y dueño de cada recurso en el tiempo" width="720">
</div>

Mientras corre, el robot muestra en el navegador un **overlay de monitoreo** sobre el video de la cámara: personas con
su ID, el objetivo, los eventos, el modo, el dueño de cada recurso, los ángulos y la salud del sistema. La figura la
dibuja el mismo código del robot (`keepon/overlay.py`) sobre una escena sintética, sin personas reales:

<div align="center">
<img src="docs/img/overlay_monitoreo.png" alt="Overlay de monitoreo: dos siluetas con sus cajas e ID, el objetivo con ME_MIRA y CAMISETA_OLIMPIA, otra persona con SALUDO, el panel de modo y dueños de los recursos, y la barra de salud" width="900">
</div>

## Resultados medidos

| Métrica | Resultado | Pedido por la consigna |
|---|---|---|
| Detección de personas (Pi 5, robot completo) | **12–17 Hz** | ≥ 10 Hz |
| Lazo de decisión y control | 36–39 Hz | — |
| Latencia evento → respuesta (estimada) | ≈ 130–170 ms | ≤ 300 ms |
| Camiseta de Olimpia / Cerro (cámara del robot, 60 s) | 82 % (99 % desde los 10 s) / 98 % | — |
| Falsos positivos con remeras lisas roja y azul | 0 % | rechazar prendas lisas |
| Firmware en la ESP32 real | 30/30 pruebas; PING → ACK 4,4 ms | — |
| Conflictos de recursos en el escenario simulado | 0 violaciones | un dueño por recurso |

Detalle en el informe (sección 11) y en [`docs/ESTADO_PI.md`](docs/ESTADO_PI.md).

## Hardware

| Parte | Modelo |
|---|---|
| Procesamiento | Raspberry Pi 5 (4 GB), Ubuntu 24.04 + ROS 2 Jazzy (ROS 2 solo para leer la cámara) |
| Cámara | Camera Module 3 NoIR (IMX708), en la nariz, montada invertida |
| Microcontrolador | ESP32-C3-DevKitM-1 por USB serie: pulsos de los servos y tonos del buzzer |
| Servos | yaw: DSSERVO RDS3218 (GPIO0) · pitch: TowerPro MG996R (GPIO1) · roll: TowerPro MG996R (GPIO4) |
| Buzzer | módulo pasivo MH-FMD a 3V3, en GPIO5 (frecuencia variable: melodías) |
| Alimentación | servos: fuente de laboratorio a 6 V · Pi: powerbank Xiaomi PB2020MI · GND común |
| Mecánica | diseño propio v6 R4 impreso en 3D: [`docs/diseno_v6/`](docs/diseno_v6/README.md) |

Conexiones y alimentación: [`docs/HARDWARE.md`](docs/HARDWARE.md).

<div align="center">
<img src="docs/img/diagrama_componentes.png" alt="Componentes reales de Wall-E y sus conexiones: powerbank, Raspberry Pi 5, cámara, ESP32-C3, fuente de 6 V, tres servos y buzzer" width="860">
</div>

<div align="center">
<img src="docs/img/keepon_cad.png" alt="Modelo CAD v6 R4: base con el servo de yaw, horquilla de pitch y cabeza con los ojos y la cámara como nariz" width="380">

*Modelo CAD v6 R4.*
</div>

## Probarlo sin el robot

```bash
uv venv .venv --python 3.12 && . .venv/bin/activate
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu   # solo x86
uv pip install -r requirements.txt

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q   # 257 tests (la variable evita los plugins de ROS 2)
python scripts/sim_scenario.py --plot                   # escenario simulado de 30 s -> logs/sim_scenario.png
```

Algunos tests compilan el núcleo del firmware en C++ y lo comparan paso a paso con el simulador: necesitan `g++`.
El informe también se puede abrir en Colab y ejecutar: descarga este repositorio y lee los parámetros reales.

## Instalación en la Raspberry Pi 5

1. Copiar el repo a `~/keepon` (por ejemplo, con `rsync`; ver [`docs/PI.md`](docs/PI.md)).
2. Entorno `~/keepon_env`: `python3 -m venv --system-site-packages ~/keepon_env` (así ve `rclpy`) e instalar
   `requirements.txt`. La cámara se lee con el nodo `camera_ros` de ROS 2 Jazzy.
3. `sudo usermod -aG dialout $USER` para usar el puerto serie de la ESP32 sin `sudo`.
4. Firmware de la ESP32-C3: `bash scripts/cargar_firmware.sh` ([`firmware/README.md`](firmware/README.md)).
   **Sostener la cabeza** mientras carga: los MG996R quedan flojos sin pulso.
5. `bash ~/keepon/scripts/keepon instalar` instala los servicios de usuario (`keepon` y `keepon-panel`).

## Uso

**Encender:** primero el powerbank (Pi) y después los 6 V de los servos, con la cabeza cerca de HOME. **Apagar:** al revés.
En la Pi, `keepon` es `bash ~/keepon/scripts/keepon`.

| Qué | Cómo |
|---|---|
| Arrancar / parar | panel del celular, o `keepon arrancar` / `keepon parar` (al parar vuelve a HOME) |
| Panel del celular | `http://<ip-de-la-pi>:8081`: Encender / Apagar, modos, STOP, Home, Resume, Ejes, sonidos y volumen |
| Monitoreo (overlay) | `http://<ip-de-la-pi>:8080/stream_viewer?topic=/keepon/overlay` |
| Personalidad | `keepon n` (Neutro) · `keepon t` (Tímido) · `keepon a` (Atrevido) · `keepon m` (Maleducado), cada una con su beep |
| STOP y HOME | `keepon stop` / `keepon home` (quedan enclavados) · `keepon resume` los libera |
| Demostración de los ejes | `keepon ejes`: recorre yaw, pitch y roll en ~15 s y vuelve |
| Sonidos | `keepon sonido POLCA` (también R2D2, ABUCHEO, PIROPO, DESAPROBACION) · `keepon volumen 0-100` |
| Estado y log | `keepon estado` · `keepon log` (CSV con marca de tiempo en `logs/run_*.csv`) |

Desde una notebook con acceso SSH a la Pi, `scripts/k <comando>` hace lo mismo (`KEEPON_PI=usuario@host`).

## Estructura del repositorio

> **¿Primera vez acá?** El mapa de toda la documentación, con un recorrido de lectura sugerido, está en
> [`docs/README.md`](docs/README.md).

```
keepon-pro/
├── keepon/               el robot en Python: percepción, eventos, foco, comportamientos, árbitro, actuadores
├── firmware/             ESP32-C3: trayectorias con curva S, sonidos, watchdog y protocolo serie
├── scripts/              arranque, panel del celular, carga del firmware, simulación, benchmarks, figuras
├── tests/                257 tests con pytest (el firmware se compara paso a paso con el simulador)
├── config.yaml           TODOS los parámetros del robot, comentados
├── pruebas_servos/       banco de pruebas y calibración de los servos
├── pruebas_buzzer/       buzzer y sonidos (la polca transcrita de la partitura)
├── pruebas_camisetas/    detector de camisetas: referencias, evaluación y resultados
└── docs/
    ├── README.md         mapa de la documentación y recorrido sugerido
    ├── consigna/         enunciado del µTP y checklist de la consigna
    ├── informe/          informe técnico (cuaderno Colab) y sus diagramas editables
    ├── guia/             guía completa del proyecto en PDF
    ├── hardware/         fotos de Wall-E y de cada componente, diagrama eléctrico, hojas de datos
    ├── diseno_v6/        diseño mecánico vigente (v6 R4): CAD, planos y piezas para imprimir
    ├── cad_anteriores/   diseños mecánicos v1 a v4 (la historia del diseño)
    ├── revisiones/       revisiones externas del plan, el código y el hardware
    ├── img/              imágenes de este README
    └── *.md              arquitectura, protocolo, hardware, Pi, decisiones, bitácora, estado y pendientes
```

| Módulo | Qué hace |
|---|---|
| `keepon/perception.py`, `tracker.py` | Procesos de percepción y tracker IoU propio |
| `keepon/eventos.py`, `camiseta.py`, `world.py` | Eventos con filtros temporales, detector de camisetas y modelo del mundo |
| `keepon/gaze.py` | Control de mirada por objetivo y foco de atención con histéresis |
| `keepon/behaviors.py` | Observador, Seguimiento, Saludo, Camiseta, Ejes y los cuatro modos |
| `keepon/arbiter.py`, `actuators.py` | Árbitro de recursos y filtro por dueño |
| `keepon/trajectory.py` | Trayectorias con límites y curva S (el firmware porta la misma lógica) |
| `keepon/protocol.py`, `link.py`, `sim_esp32.py` | Protocolo serie, enlace y ESP32 simulada (especificación ejecutable del firmware) |
| `keepon/robot.py`, `overlay.py` | Lazo principal, log CSV y overlay de monitoreo |
| `config.yaml` | **Todos** los parámetros: límites, umbrales, cooldowns, prioridades, sonidos |

Arquitectura en detalle: [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md). Por qué se eligió cada cosa:
[`docs/DECISIONES.md`](docs/DECISIONES.md). Historia del trabajo: [`docs/BITACORA.md`](docs/BITACORA.md).

## Modelos preentrenados y créditos

- **YOLO26n** de [Ultralytics](https://github.com/ultralytics/ultralytics), exportado a [NCNN](https://github.com/Tencent/ncnn): detección de personas.
- **MediaPipe** de Google ([google-ai-edge/mediapipe](https://github.com/google-ai-edge/mediapipe)): BlazeFace (rostros) y Pose lite (saludo y torso).
- [**camera_ros**](https://github.com/christianrauch/camera_ros) (ROS 2) para leer la cámara.

El árbitro, los comportamientos, el control de la cabeza, el tracker, los eventos, el detector de camisetas, el firmware
y el diseño mecánico son **desarrollo propio** del grupo.
