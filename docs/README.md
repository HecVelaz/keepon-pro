# Documentación de Wall-E (proyecto Keepon pro)

Mapa de la carpeta `docs/` para quien llega de afuera. Si tenés poco tiempo, seguí el **recorrido sugerido**; el resto
es el detalle de cada tema.

## Recorrido sugerido

| Paso | Qué leer | Para qué |
|---|---|---|
| 1 | [`../README.md`](../README.md) | Qué es Wall-E, qué hace, fotos y resultados (5 minutos) |
| 2 | [`consigna/2026S2uTP_RoboticaSocial.md`](consigna/2026S2uTP_RoboticaSocial.md) | Lo que pedía la cátedra |
| 3 | [`informe/Informe_técnico_v3.ipynb`](informe/Informe_t%C3%A9cnico_v3.ipynb) | El informe técnico entregado: mecanismo, percepción, control, comportamientos, arbitraje y pruebas |
| 4 | [`consigna/CHECKLIST_TP.md`](consigna/CHECKLIST_TP.md) | Cada punto de la consigna y dónde está resuelto en el código |
| 5 | [`ARQUITECTURA.md`](ARQUITECTURA.md) | Cómo está armado el software, módulo por módulo |
| 6 | [`DECISIONES.md`](DECISIONES.md) | Por qué se eligió cada cosa (y qué se descartó) |
| 7 | [`guia/Guia_Keepon_pro.pdf`](guia/Guia_Keepon_pro.pdf) | La guía completa, con diagramas, para estudiar el proyecto entero |

## Qué hay en cada carpeta

| Carpeta / archivo | Contenido |
|---|---|
| [`consigna/`](consigna/README.md) | Enunciado del µTP (Markdown y PDF) y el checklist de la consigna (Markdown e interactivo) |
| [`informe/`](informe/) | **Informe técnico** en cuaderno Colab (`Informe_técnico_v3.ipynb` es la versión final; `Informe_técnico.ipynb`, la anterior), sus diagramas editables (`diagramas/*.drawio`) y los scripts que lo generan (`fuente/`) |
| [`guia/`](guia/) | Guía completa del proyecto en PDF y su fuente HTML |
| [`img/`](img/) | Imágenes del README: render CAD, arquitectura, estados, escenario simulado y diagrama de componentes |
| [`hardware/`](hardware/README.md) | Fotos de los componentes y del robot armado, diagrama eléctrico interactivo y hojas de datos de los servos probados |
| [`diseno_v6/`](diseno_v6/README.md) | **Diseño mecánico vigente (v6 R4)**: scripts de CAD, planos y piezas para imprimir. Empezar por [`LEEME_GIT.md`](diseno_v6/LEEME_GIT.md) |
| [`cad_anteriores/`](cad_anteriores/README.md) | Versiones mecánicas anteriores (v1 a v4): la historia del diseño |
| [`revisiones/`](revisiones/README.md) | Revisiones externas del plan, del código y del hardware hechas con Codex, y qué se corrigió |

## Documentos técnicos

| Archivo | Tema |
|---|---|
| [`ARQUITECTURA.md`](ARQUITECTURA.md) | Módulos de `keepon/`, flujo de datos, procesos y tasas |
| [`PROTOCOLO.md`](PROTOCOLO.md) | Protocolo serie entre la Raspberry Pi y la ESP32-C3 |
| [`HARDWARE.md`](HARDWARE.md) | Cámara, ESP32, servos (calibración y problemas), alimentación y pines |
| [`PI.md`](PI.md) | Cómo se trabaja con la Raspberry Pi: sincronizar, arrancar, visores, benchmarks |
| [`ESTADO_PI.md`](ESTADO_PI.md) | Sistema de la Pi y rendimiento medido (con los CSV `benchmark_pi_*.csv`) |

## Historia y estado del trabajo

| Archivo | Qué registra |
|---|---|
| [`BITACORA.md`](BITACORA.md) | Lo hecho en cada sesión, del más reciente al más antiguo |
| [`ESTADO.md`](ESTADO.md) | Foto del estado actual: qué funciona, qué está probado y qué no |
| [`PENDIENTES.md`](PENDIENTES.md) | Lo que falta, por prioridad |
| [`DECISIONES.md`](DECISIONES.md) | Decisiones tomadas y su porqué |
| [`HOJA_DE_RUTA.md`](HOJA_DE_RUTA.md) | Plan original por hitos (vista interactiva: `hoja_de_ruta.html`) |

## Fuera de `docs/`

| Carpeta | Contenido |
|---|---|
| [`../keepon/`](../keepon/) | El robot en Python: percepción, eventos, foco, comportamientos, árbitro, actuadores |
| [`../firmware/`](../firmware/README.md) | Firmware de la ESP32-C3 (trayectorias, sonidos, watchdog, protocolo) |
| [`../scripts/`](../scripts/) | Arranque del robot, panel del celular, carga del firmware, benchmarks, simulación y generadores de figuras |
| [`../tests/`](../tests/) | 257 tests con pytest (incluye la comparación paso a paso del firmware con el simulador) |
| [`../pruebas_servos/`](../pruebas_servos/README.md) | Banco de pruebas de los servos y su calibración |
| [`../pruebas_buzzer/`](../pruebas_buzzer/README.md) | Buzzer y sonidos (la polca transcrita de la partitura) |
| [`../pruebas_camisetas/`](../pruebas_camisetas/README.md) | Detector de camisetas: imágenes de referencia, evaluación y resultados |
| [`../config.yaml`](../config.yaml) | **Todos** los parámetros del robot, comentados |
