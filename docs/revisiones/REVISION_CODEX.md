# Revisión del proyecto por Codex

> Generada con codex-cli 0.158.0 el 30/09/2026 sobre `2026S2uTP_RoboticaSocial.md` y la hoja de ruta v1.

## 1) Opinión general del proyecto y su dificultad real

**Es viable en un mes para cinco integrantes con dedicación sostenida, componentes disponibles y experiencia básica. El plan actual tiene poco margen y concentra demasiado riesgo al final.** La dificultad real es alta por la integración: cámara móvil, mecánica con holgura, varios detectores, seguimiento de personas y comportamientos que deben convivir sin bloquearse.

El stack **notebook + webcam USB + ESP32** es adecuado. Mantendría esa elección durante todo el mes.

La hoja de ruta entiende bien el enunciado, pero todavía es más una lista de funcionalidades que un plan de validación. **El éxito debe medirse con el robot completo funcionando**, no con módulos que funcionan por separado.

Dos precisiones sobre evaluación:

- **Sin demo física funcional no hay puntaje.** La estabilidad mecánica, eléctrica y del seguimiento tiene prioridad sobre apariencia y extras.
- El enunciado llama “referenciales” a las reacciones, pero también presenta comportamientos requeridos y mínimos explícitos de arbitraje. **No asumiría que pueden eliminar modos o detecciones sin perder puntos.** Tampoco hay un desglose que permita garantizar una nota para un MVP parcial.

## 2) Revisión crítica de la hoja de ruta

### Qué está bien

- Separación entre percepción, modelo del mundo, comportamientos, árbitro y ejecución.
- Cámara solidaria, cuello de tres ejes y fuente independiente para servos.
- Inclusión de histéresis, cooldowns, watchdog, movimientos y sonido no bloqueantes.
- Clase `OTRA` para camisetas, monitoreo y medición de latencia.
- Uso de modelos preentrenados: entrenar un detector general desde cero sería injustificable para este plazo.

### Qué falta o está mal estimado

| Hallazgo | Corrección concreta |
|---|---|
| **Integración física recién en semana 2; seguimiento completo hacia el 18/10.** | Tener cámara montada provisionalmente y seguimiento físico elemental el **7–8/10**. |
| “4 semanas + buffer” no representa el calendario. | Del 26 al 30 hay ajuste, video e informe: **no es un buffer libre**. Reservar al menos los últimos tres días para contingencias y ensayo. |
| Camisetas empiezan demasiado tarde. | Conseguir prendas y probar clasificación desde el **1–4/10**. Es una incertidumbre que debe resolverse temprano. |
| No aparecen masa, centro de gravedad, torque ni consumo medidos. | Añadir una ficha mecánica y eléctrica antes de cerrar actuadores y fuente. |
| No se explica cómo unir rostro, mano y camiseta con un ID. | Definir asociación espacial y temporal por persona. Sin eso pueden reaccionar a la camiseta de alguien mientras miran a otro. |
| No hay criterio de aceptación por requisito. | Crear una matriz T1–T7 con prueba, resultado esperado y evidencia. |
| Documentación concentrada al final. | Escribir Colab, parámetros y resultados desde el primer ensayo. |
| Persona 5 acumula árbitro, modos, control, interfaz e integración. | Redistribuir. Es el principal cuello de botella organizativo. |

**Calendario que propondría:**

| Fechas | Resultado verificable |
|---|---|
| **30/9–4/10** | Compras, pruebas de servos/fuente, benchmark en notebook, prendas disponibles, protocolo y árbitro mínimo con eventos sintéticos. |
| **5–8/10** | Tres ejes operativos, cámara en la cabeza y seguimiento físico básico; STOP y pérdida de comunicación probados. |
| **9–15/10** | IDs, selección entre dos personas, ME_MIRA, SALUDO y concurrencia seguimiento + buzzer. Clasificación de camisetas ya evaluada. |
| **16–22/10** | Todos los modos y comportamientos integrados, cooldowns y recuperación. Congelar funcionalidades el 22. |
| **23–27/10** | Pruebas negativas, iluminación, latencia, funcionamiento prolongado, video e informe. |
| **28–30/10** | Ensayo completo, repuestos y correcciones pequeñas. |

Hay además una **contradicción de entrega**: el reglamento exige documentación antes de la demo; §6.1 permite archivos hasta el domingo posterior. Conviene resolverla con la cátedra; mientras tanto, planificar todo listo antes de la demostración.

## 3) Revisión de la división Hardware / Software

**La frontera técnica es razonable, pero H3 es software embebido.** Lo importante es separar decisiones de comportamiento de ejecución física.

| Responsabilidad | Ubicación recomendada |
|---|---|
| Mecánica, alimentación, cableado y calibración física | Hardware |
| PWM, límites, velocidad/aceleración, secuenciador de sonido, watchdog | ESP32 |
| Percepción, asociación por ID y modelo del mundo | PC |
| Foco de atención, modos, prioridades, cooldowns y propiedad de recursos | PC |
| Control visual y composición de gestos | PC, siempre bajo autorización del árbitro |
| Protocolo, signos de ejes, HOME y pruebas de integración | Contrato compartido |

Correcciones específicas:

- **`MODE x` debe gestionarse en el PC.** El ESP32 recibe el sonido de confirmación y las acciones resultantes; no necesita otra máquina de personalidad.
- **S3 no debe escribir directamente al puerto serie.** Calcula propuestas; el árbitro decide cuáles llegan al ejecutor.
- **SALIENDO está mal aislado como tarea puramente visual.** Necesita detecciones, objetivo actual, movimiento del robot y límites articulares. Su definición pertenece al modelo del mundo con integración/control.
- **HOME no es una referencia medida automáticamente.** Con servos convencionales será una postura calibrada. No confundir ángulo comandado con posición física observada.

Para cinco personas:

1. Mecánica, electrónica y validación de alimentación.
2. Firmware, protocolo, sonidos y herramienta de prueba serie.
3. Personas, rostros, gestos y asociación de detecciones.
4. Camisetas, pruebas negativas, overlay y métricas.
5. Árbitro, control visual, modos e integración.

La documentación se reparte por módulo y todos deben hacer al menos una defensa cruzada de otra parte del sistema.

## 4) Recomendaciones técnicas concretas

### Componentes y mecánica

- **Priorizar cabeza liviana y equilibrada.** Cartón pluma o carcasa impresa delgada son suficientes; los ojos deben hacer evidente la orientación.
- El apoyo en yaw está bien, pero **pitch suele ser más exigente por gravedad**. Debe mover también los componentes montados después de él.
- Dimensionar con `τ ≈ Σ(m·g·d)` en la postura desfavorable. Por ejemplo, 0,30 kg a 5 cm producen aproximadamente **1,5 kgf·cm estáticos**, antes de aceleración, fricción y cableado. Buscar margen amplio y validar térmicamente; el torque de bloqueo no es torque continuo de trabajo.
- MG996R/DS3218 son candidatos, no una selección cerrada sin conocer carga. MG90S en roll sólo con cabeza ligera y centro de gravedad próximo al eje.
- **“SG90 metálico” debe corregirse:** el SG90 estándar usa engranajes plásticos; el MG90S es una alternativa metálica. [Ficha de TowerPro](https://towerpro.com.tw/product/sg90-7/).
- Fuente regulada dentro del rango admitido por **todos** los servos. Los 3–5 A propuestos son una estimación por verificar con movimientos simultáneos; 1000 µF no compensan una fuente insuficiente.
- Distribuir potencia con borneras y cables adecuados, evitar protoboard para corriente de servos y mantener masa común. Añadir alivio de tensión y holgura al USB de la cámara.
- Mantener el NPN para el buzzer, con resistencia de base y componentes dimensionados según el transductor.
- **Separar temporizadores de servos y buzzer.** Cambiar la frecuencia del sonido no debe alterar el PWM de los servos. Usar canales distintos no garantiza temporizadores independientes. El PCA9685 sólo merece añadirse si resuelve un problema concreto. [Documentación LEDC de Espressif](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/ledc.html).

### Librerías y percepción

**Stack inicial:** Python, OpenCV, NumPy, `pyserial`, Ultralytics y MediaPipe Tasks. Fijar versiones y descargar los modelos para funcionar sin Internet.

- **PERSONA:** conservar YOLOv8n si ya funciona. ByteTrack es una base sencilla, pero no compensa movimiento de cámara. Si los IDs cambian al girar la cabeza, evaluar BoT-SORT con compensación global, midiendo el costo adicional. [Documentación de tracking](https://docs.ultralytics.com/modes/track/).
- **Asociación:** asignar cada rostro a una caja de persona; vincular pose y torso al mismo ID. Ante solapamiento ambiguo, abstenerse de generar eventos.
- **ME_MIRA:** Face Landmarker + `solvePnP`, con intrínsecos y correspondencias faciales documentadas. Es una aproximación por orientación de cabeza, **no una medición de dirección ocular**. Es suficiente como definición operativa si se valida. La estimación debe revisar también a candidatos no seleccionados para cumplir T4. [MediaPipe](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker/python), [OpenCV](https://docs.opencv.org/4.13.0/d5/d1f/calib3d_solvePnP.html).
- **SALUDO:** comenzar sólo con pose; muñeca y hombro bastan para una definición sencilla. Medir movimiento de muñeca respecto del torso y normalizar por ancho de hombros. **Dos cruces no equivalen necesariamente a dos ciclos completos**: definir amplitud, alternancias y duración.
- **Camisetas:** la regla fija de “franjas horizontales rojo/azul” no está justificada por el enunciado. Diseñar a partir de las prendas reales, considerando orientación y distribución de franjas. Color solo no identifica un club.
- Mantener `OTRA` y `DESCONOCIDA`: torso tapado, demasiado pequeño o sin evidencia suficiente no debe clasificarse. Probar remeras lisas blancas, rojas y azules, además de prendas parecidas. Si entrenan, separar sesiones/personas entre entrenamiento y validación; dividir cuadros consecutivos da resultados engañosos.
- **SALIENDO:** exigir objetivo válido y borde + tendencia exterior sostenida, o saturación articular + error visual persistente hacia afuera. Saturación por sí sola no basta. Inhibirlo durante desvíos tímidos, saludos y cambios de foco para no interpretar el movimiento propio como salida.

### Control visual y tiempos

**Empezaría con proporcional, sin integral.** La integral añade problemas cuando un gesto toma el cuello o el eje llega al límite.

Una opción clara es convertir error angular en velocidad:

```text
error_angular = atan((u - cx) / fx)
velocidad_yaw = limitar(Kp · error_angular)
referencia_yaw += velocidad_yaw · dt
```

Aplicar el equivalente a pitch, verificar signos físicamente y añadir zona muerta y filtrado moderado. Como valores iniciales de ensayo, no garantías:

- Zona muerta: 3–5 % de la dimensión de imagen.
- Control/árbitro: 30–50 Hz.
- Trayectoria embebida: 50–100 Hz; frecuencia PWM según el servo.
- Durante pérdida menor a 1 s: mantener postura antes de introducir predicción.
- Con roll distinto de cero: corregir la rotación del error de imagen o mantener roll pequeño durante seguimiento.

Procesar siempre **el cuadro más reciente**, con cola acotada; acumular cuadros viejos produce una mirada atrasada aunque el contador de FPS parezca aceptable.

Medir por separado:

1. Captura → resultado perceptivo.
2. Evento confirmado → comando.
3. Comando → comienzo observable de respuesta.

Los 0,5 s de confirmación de ME_MIRA y la duración del saludo son ventanas de evidencia; deben distinguirse de la latencia posterior del sistema. Un ACK no demuestra movimiento físico.

### Arquitectura del árbitro

Mantendría **dos recursos exclusivos: cuello completo y buzzer**. Una propuesta debería incluir:

```text
id_accion, comportamiento, persona_id, prioridad, recursos,
inicio, vencimiento, interrumpible, parámetros
```

Reglas esenciales:

- Adquisición **atómica**: un saludo consigue cuello y buzzer juntos o no comienza.
- STOP interrumpe todo, incluso acciones declaradas no interrumpibles.
- Las propuestas vencidas se descartan: no saludar a alguien que ya se fue.
- Cooldown al iniciar efectivamente la respuesta; no al generar una propuesta rechazada.
- Separar evento nuevo de predicado sostenido: una camiseta visible durante veinte segundos no son veinte eventos.
- Al interrumpir, cancelar la acción en ejecución y recuperar suavemente la referencia.
- Mantener continuidad de IDs durante pérdidas breves para evitar que renumerar a una persona reinicie sus cooldowns.

**Atrevido requiere composición explícita:** un único comportamiento dueño del cuello combina seguimiento en yaw y elevación del mentón en pitch. No deben existir dos escritores independientes. Tímido también debe controlar explícitamente desvío, espera y regreso.

### Protocolo serie

ASCII por líneas, 115200 baudios, unidades en grados y mensajes cortos son suficientes:

```text
HELLO 1
J 101 12.0 -4.0 0.0
S 102 POLCA
CANCEL 103 SOUND
PING 104
STOP 105
RESUME 106
HOME 107

ACK 101
DONE 102
ERR 107 STOP_ACTIVE
STATE 108 STOPPED 12.0 -4.0 0.0 NONE
```

Definir por escrito:

- `ACK` significa aceptado; `DONE`, secuencia terminada según el ejecutor.
- Para `J`, conservar la referencia más reciente; no encolar segundos de movimiento.
- Validar longitud, números finitos, límites y comandos incompletos sin bloquear.
- Evitar duplicar un sonido cuando se reenvía el mismo número de secuencia.
- STOP cancela sonido y movimiento pendiente, y queda enclavado hasta `RESUME`; **no debe significar ir a HOME**.
- Watchdog, por ejemplo de 500 ms como punto inicial: detener secuencias y mantener una postura segura. Volver a HOME automáticamente puede ser una mala reacción ante un fallo.
- Tras reinicio del ESP32, informar nuevo arranque y exigir resincronización.
- La telemetría indica referencias comandadas, no ángulos medidos si no tienen sensores.

## 5) Top 5 riesgos y mitigación

| Riesgo | Mitigación prioritaria | Prueba de aceptación |
|---|---|---|
| **1. Integración tardía y sobrecarga del integrador.** | Contratos desde el inicio, redistribución e integración física antes del 8/10. | Demo corta del sistema completo varias veces por semana. |
| **2. Torque insuficiente, holgura o caída de tensión.** | Equilibrar cabeza, dimensionar cargas, apoyar ejes y medir alimentación. | Movimiento simultáneo + buzzer durante 20 min sin resets, calentamiento excesivo ni degradación. |
| **3. Latencia y seguimiento inestable por cámara móvil.** | Benchmark temprano, cola de último cuadro, ganancias conservadoras y asociación robusta. | Seguimiento quieto/móvil y dos personas; verificar ≥10 Hz y medir latencia incluyendo casos desfavorables. |
| **4. Falsos positivos de camiseta, mirada o saludo.** | Clase desconocida, filtros temporales y ensayos negativos desde semana 0. | Matriz de resultados con prendas lisas, brazos levantados sin saludo y rostro de perfil. |
| **5. Conflictos de recursos, repeticiones y recuperación defectuosa.** | Árbitro único, adquisición atómica, caducidad, cooldowns y cancelación explícita. | Saludo durante polca, cambio de modo, STOP y desconexión serie; nunca dos dueños del mismo recurso. |

## 6) Qué recortar o simplificar si el tiempo aprieta vs. qué añadir para destacar

### MVP que mejor conserva cobertura

**Simplificar la implementación de todos los requisitos antes de eliminar requisitos completos:**

- Cabeza sencilla con ojos fijos, tres ejes reales y cámara montada.
- Seguimiento proporcional, zona muerta y trayectoria suave; sin predicción sofisticada.
- Mantener mirada durante pérdidas breves; sin desaprobación opcional.
- Observador con un barrido lento sencillo; sin sacadas ni búsqueda elaborada.
- Pose para saludo; quitar Hands si no aporta.
- Reglas conservadoras de camisetas antes de entrenar un clasificador; mantener ambas clases y rechazo de prendas lisas.
- Modos tímido, atrevido y maleducado con secuencias cortas y claras.
- Fragmento breve reconocible de polca y sonidos simples.
- Interfaz por teclado y overlay OpenCV; sin GUI elaborada.
- Documentar el rango de distancia e iluminación validado.

**No recortaría:** tres GDL, buzzer pasivo, arbitraje propio, límites y suavizado, IDs y selección entre personas, modos en ejecución, cooldowns, monitoreo y entregables.

Si sólo llegan a seguimiento + saludo + árbitro, eso constituye una base funcional de emergencia, pero **no cubre todo el trabajo ni permite asegurar que no perderán puntos**.

### Qué añadir para destacar

Sólo después de pasar todas las pruebas:

1. **Robustez visible:** cruces entre personas, pérdida y recuperación del objetivo, prendas distractoras y eventos simultáneos.
2. **Resultados cuantitativos:** latencia, estabilidad de centrado, falsos positivos y continuidad de IDs.
3. **Expresividad bien ajustada:** pausas, inclinación de cabeza y movimientos suaves que hagan legible cada personalidad.
4. **Reproducibilidad:** arranque con un comando, parámetros guardados, modelos locales y demo sin Internet.
5. **Acabado físico y LEDs**, al final.

La mejora de mayor valor para este plan es **adelantar dos semanas la evidencia de que mecánica, visión y arbitraje funcionan juntos**.