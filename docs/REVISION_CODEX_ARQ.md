Revisé los archivos solicitados y ejecuté los tests sin caché ni escritura de bytecode: **81 aprobados en 4,86 s**. No modifiqué archivos ni hice mediciones nuevas en la Pi o en el hardware.

Distingo **[Repo]** evidencia del repositorio, **[General]** propiedades técnicas, **[Propuesta]** decisiones o estimaciones y **[Medir]** comprobaciones pendientes. Tu actualización del **14/10** prevalece sobre documentos anteriores.

## 1. ESP32 frente a todo en la Pi

**Recomendación: conservar la ESP32-C3 y terminar su firmware. El PWM hardware de la Pi 5 es técnicamente suficiente, pero cambiar ahora aumenta el trabajo de integración y debilita la independencia del watchdog.**

### PWM hardware del RP1: sí alcanza

**[General/documentado]** El controlador **PWM0 del RP1 tiene 4 canales independientes**, con registros de período y duty por canal. Una asignación posible es:

| Uso | Canal RP1 | GPIO BCM | Pin físico |
|---|---:|---:|---:|
| Yaw | PWM0[0] | 12 | 32 |
| Pitch | PWM0[1] | 13 | 33 |
| Roll | PWM0[2] | 18 | 12 |
| Buzzer | PWM0[3] | 19 | 35 |

GPIO12/13 usan **Alt0**; GPIO18/19, **Alt3**. Alternativamente, los canales 2/3 salen por GPIO14/15, pero pueden interferir con UART.

**Sí pueden coexistir 3 servos a 50 Hz y un buzzer a frecuencia variable.** Comparten reloj fuente, pero cada canal tiene su propio período. No corresponde aplicar a la Pi 5 la limitación de dos canales de modelos anteriores. [Manual del RP1](https://datasheets.raspberrypi.com/rp1/rp1-peripherals.pdf).

El driver de referencia configura período y duty individualmente. Su árbol de dispositivos asigna **50 MHz** al PWM: resolución nominal de **20 ns**, más que suficiente para estos servos; eso no garantiza precisión física del eje. [Driver PWM](https://raw.githubusercontent.com/raspberrypi/linux/rpi-6.8.y/drivers/pwm/pwm-rp1.c), [configuración del RP1](https://raw.githubusercontent.com/raspberrypi/linux/rpi-6.8.y/arch/arm/boot/dts/broadcom/rp1.dtsi).

**Ubuntu 24.04: falta verificar la instalación concreta.**

- **[Repo]** Último kernel documentado: `6.8.0-1064-raspi`.
- Haría falta habilitar `rp1_pwm0` y seleccionar los **4 pines** mediante Device Tree.
- El overlay clásico `pwm-2chan` configura **dos pines**; no constituye por sí solo una solución de cuatro salidas.
- Para cuatro salidas usaría un overlay específico compatible con el kernel instalado, verificando driver, reloj y multiplexación. No daría por instalado un supuesto `pwm-4chan`.
- En Ubuntu, el punto habitual es `/boot/firmware/config.txt`. Es configuración **global de arranque**: afecta a los demás proyectos que usen esos GPIO, SPI/I²S/UART o PWM y normalmente requiere reiniciar. Un `venv` no aísla esto. [Overlay de referencia](https://raw.githubusercontent.com/raspberrypi/linux/rpi-6.8.y/arch/arm/boot/dts/overlays/pwm-2chan-overlay.dts), [documentación de Ubuntu](https://ubuntu.com/hardware/docs/boards/how-to/special_hardware/rpi-config-txt/).

**[Medir]** Antes de aprobar esa alternativa: identificar el `pwmchip` correcto —sin asumir su número—, comprobar cuatro salidas y barrer el buzzer mientras se observan los tres pulsos con osciloscopio.

### PWM por software: descartarlo para los servos

**[General]** Generar flancos desde Python bajo Linux normal no garantiza anchos de pulso con precisión de microsegundos. Afinidad de CPU tampoco garantiza plazos.

**[Repo + cálculo]** Sensibilidad de sus servos:

| Error hipotético de ancho de pulso | RDS3218, 0,13 °/µs | HS-7955TG, 0,090 °/µs |
|---|---:|---:|
| 2 µs | 0,26° | 0,18° |
| 10 µs | 1,30° | 0,90° |
| 50 µs | 6,50° | 4,50° |

Son conversiones, **no jitter medido**. El RDS responde a ≤2 µs en un sentido y a 4–6 µs en el otro; el HS también responde a ≤2 µs. Variaciones repetidas pueden producir correcciones, zumbido, consumo y vibración.

Hay que distinguir:

- **Jitter del pulso:** crítico para posición; lo resuelve PWM hardware.
- **Retraso al actualizar la consigna:** afecta suavidad y latencia; sigue existiendo aunque el pulso sea perfecto.

### PCA9685: viable, pero aporta poco aquí

**[General/documentado]** Tiene **16 canales, 12 bits y una frecuencia común** para todos. A 50 Hz:

\[
\Delta t=20\,000/4096=4,883\ \mu s
\]

Equivale aproximadamente a **0,63–0,66° en yaw** y **0,44° en pitch**. Es estable, pero más grueso que LEDC a 14 bits.

No permite servos a 50 Hz y melodías de frecuencia variable simultáneamente en el mismo chip. Necesitarían otra salida para el buzzer; además, su frecuencia máxima nominal ronda **1.526 Hz**. Tampoco incorpora el watchdog de movimientos que necesitan. [Ficha NXP](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf).

En I²C: lógica y pull-ups compatibles con **3,3 V**, potencia de servos separada a **6 V**. No confundir `VCC` lógico con `V+` de servos.

### Seguridad y trayectoria

**[Repo]** Comportamiento observado, con alimentación presente:

| Servo | Al retirar pulsos |
|---|---|
| RDS3218 n.º 2 | Mantiene posición |
| HS-7955TG | Mantiene posición con fuerza |
| MG996R | Queda flojo |

Por eso **STOP debe frenar y después mantener pulsos**, especialmente en roll. Retirar PWM no equivale a una parada segura universal.

Con PWM hardware en la Pi, si Python muere, **puede quedar activo el último PWM**, dependiendo del backend y de cómo libere recursos. El servo puede seguir avanzando hasta la última referencia y el buzzer puede quedar sonando. Un watchdog escrito en el mismo proceso deja de ejecutarse con él.

La ESP32 permite detectar ausencia de órdenes independientemente de Linux:

- Trayectoria: **100 Hz**, paso de **10 ms**.
- Pulsos de servo: **50 Hz**, período de **20 ms**.
- Keepalive: **200 ms**.
- Watchdog: **500 ms**.

**[Cálculo]** A los máximos actuales, `vmax/amax = 0,3 s` en los tres ejes. Por tanto, **500 ms de watchdog no significan estar detenido a los 500 ms**: puede haber otros ≈300 ms de frenado. También hace falta contemplar fallo del propio firmware y corte físico de los **6 V**, con la cabeza sostenida o equilibrada para que no caiga.

**[Repo]** El primer pulso del HS puede provocar movimiento a máxima velocidad. Inicializar la variable a HOME **no demuestra que el eje esté físicamente en HOME**. Definir postura de encendido controlada; no prometer arranque suave desde una posición desconocida sin realimentación.

**[General]** Python puede calcular tres trayectorias a 100 Hz; el problema no es el costo aritmético. El problema es garantizar cada plazo de 10 ms bajo carga, pausas y E/S. Los **239 % de CPU** documentados dejan capacidad media, pero ambos grupos de afinidad abarcan los cuatro núcleos: no hay un núcleo reservado ni garantía temporal.

### Electricidad

**[Repo]** Los tres servos ya funcionaron con señales de **3,3 V** de la ESP32 y alimentación de **6 V**. Eso es evidencia favorable para esas unidades, no una especificación universal del umbral lógico.

**[Propuesta]**

- Fuente de servos separada; retorno de potencia directo a bornera, **GND común** con control.
- No circular corriente de motores por la Pi ni por su USB.
- **1.000–2.200 µF + 100 nF** cerca de distribución.
- Si falta margen lógico: buffer **74AHCT125 a 5 V**, nunca a 6 V.
- Buzzer mediante transistor, dimensionado según el transductor.
- Medir tensión en conectores durante movimientos simultáneos; “módulo de 20 A” no acredita 20 A continuos.

La ESP32 **no aísla eléctricamente** la Pi: el USB comparte masa. La distribución y el desacople siguen siendo necesarios.

### Arquitectura recomendada y reutilización

```text
Camera Module 3 → camera_ros
                         ↓
Pi: percepción → World → foco/comportamientos → árbitro
                         ↓
                 Actuators → SerialLink
                         ↓ USB/UART, 115200
ESP32-C3: límites + trayectoria 100 Hz + sonidos + watchdog
                         ↓
              servos 50 Hz / buzzer variable
```

| Archivo/módulo | Acción |
|---|---|
| `protocol.py`, `arbiter.py` | Reutilizar el contrato y el arbitraje |
| `trajectory.py` | Portar la matemática al firmware; conservar como referencia |
| `sim_esp32.py` | Mantener como oráculo de conformidad, revisando arranque y recuperación |
| `link.py` | Añadir desconexión/reconexión, errores y buffers acotados |
| `actuators.py`, `robot.py` | Invalidar sesión al perder transporte; conservar STOP y descartar órdenes viejas |
| `world.py`, `perception.py` | Integrar resultados reales, asociación y tiempos por evidencia |
| `gaze.py` | Usar intrínsecos reales y compensar roll |
| `behaviors.py` | Completar modos/SALIENDO y ajustar saludo |
| `config.yaml` | Puerto CH340 estable, signos montados, parámetros conservadores |
| `firmware/` | Implementación nueva, reutilizando generación PWM del banco |

La calibración debe generarse o transferirse desde YAML: **la ESP32 no lee automáticamente `config.yaml`**.

LEDC a **50 Hz/14 bits** ofrece **1,221 µs por paso**; separar explícitamente temporizadores de servos y buzzer. [Documentación Espressif](https://docs.espressif.com/projects/esp-idf/en/v5.3.2/esp32c3/api-reference/peripherals/ledc.html).

**No descartaría trabajo funcional.** Descartaría para esta entrega la migración a PWM Pi/PCA9685. Si igualmente eliminaran la ESP32, necesitarían un ejecutor local que sustituya `SerialLink` y toda la ejecución embebida; `sim_esp32.py` solo simula duraciones de sonidos, no genera melodías reales.

Además, **[Repo]** §4.1 y T1 mencionan microcontrolador y protocolo, aunque las observaciones permiten elección tecnológica libre. Mantener ESP32 evita también esa ambigüedad de evaluación.

## 2. Cinta de 150 mm y ubicación de la Pi

**Recomendación: con la restricción estricta de no torsionar el FFC, montar Pi y cámara solidarias sobre roll. No aprobaría el recorrido actual sin una maqueta física de cinta y conectores.**

### Comparación

| Ubicación de Pi | Movimiento relativo en el FFC | Costo mecánico |
|---|---|---|
| Plato de yaw | Pitch **50° totales** y roll **40° totales** | Menor carga en pitch/roll, pero recorrido largo y flexión en dos ejes |
| Etapa móvil de pitch | Solo roll **40°** | Carga adicional en pitch; todavía necesita resolver flexión de roll |
| Misma estructura de roll que la cámara | **0° en los tres ejes** | Pi y cooler cargan pitch y roll; cruzan cables redondos |

La Pi debe ir en la **parte móvil** de la horquilla para acompañar pitch; colocarla en su soporte fijo no elimina ese movimiento relativo.

**[Repo]** El CAD no representa el FFC ni sus conectores con suficiente detalle. Las afirmaciones del [diagrama](</home/hecvelaz/Documentos/Keepon pro /docs/diagrama_sistema/index.html:276>) “solo se dobla” y “15–20 cm alcanza” **no están verificadas**. Orientar el ancho paralelo a pitch resuelve una dirección de flexión; no demuestra compatibilidad simultánea con roll.

**[Estimación]** El recorrido actual combina desplazamiento frontal, rodeo de placa de **64 mm**, desvío alrededor del servo, bajada de **42 mm** y llegada a la Pi. No corresponde sumar esas cotas como una longitud exacta, pero **150 mm deja muy poco margen para curvas y movimiento**.

### Disposición concreta propuesta

Para una primera maqueta:

- Mantener el cuello y la placa de roll de **64 × 64 mm**.
- Agregar un portador solidario a roll de aproximadamente **100 × 85 mm**.
- Pi vertical, paralela a la cara: **85 mm horizontales × 56 mm verticales**, sobre separadores de **6–8 mm** delante de la placa.
- Componentes y cooler hacia la cara abierta; puertos accesibles por los laterales.
- Cámara en un puente delantero, aproximadamente **35–45 mm delante del PCB de la Pi**, entre los ojos.
- Profundidad inicial de la cabeza: **50–65 mm**, pendiente de cooler, conectores y recorrido del FFC.

Estas cotas son **de propuesta, no un CAD validado**. La orientación final de la Pi debe elegirse con los conectores reales para que el cable haga curvas sobre su espesor, sin giro helicoidal ni pliegue diagonal.

**Recorrido del FFC:**

1. Cámara → salida libre del conector.
2. Curva amplia por un lateral abierto del portador.
3. Bucle estático en U → conector CSI de la Pi.
4. Dos sujeciones suaves a la **misma estructura de roll**, antes de los conectores, sin aplastar pistas ni usar el conector como anclaje.

**[Propuesta]** Reservar **15–20 mm de radio** y **10–15 mm rectos junto a cada terminación**, si el cable lo permite. Una semicircunferencia consume **47–63 mm**. Buscar un recorrido guiado de aproximadamente **110–130 mm**, dejando el resto como holgura distribuida.

**No conozco el radio mínimo certificado de ese FFC concreto.** Los 15–20 mm son una reserva de diseño, no una especificación de fabricante. Si no entra así, cambiar la disposición; no reducir el radio a fuerza.

**Tramo de torsión del FFC: ninguno, 0 mm.** La holgura dinámica debe quedar en cables redondos.

### Inercia, potencia y ventilación

**[Estimación ilustrativa]** Si Pi + cooler + soporte pesan **120 g**:

- A **6 cm** del eje de pitch: agregan **0,72 kgf·cm** gravitatorios.
- Término de inercia por desplazamiento:  
  \(I=0,12·0,06²=4,32·10^{-4}\ \mathrm{kg\,m²}\).
- A **400 °/s²**: aproximadamente **0,031 kgf·cm** dinámicos, sin incluir la inercia propia del conjunto.

La gravedad domina ese ejemplo. Centrar la Pi respecto de roll reduce el desequilibrio; adelantarla aumenta la carga de pitch. **Hay que pesar el conjunto completo**, incluyendo conectores y cables.

Con ESP32 y buzzer sobre yaw:

| Cruce | Cableado principal |
|---|---|
| Base → yaw | Alimentación Pi, potencia de servos superiores, señal yaw con referencia de masa |
| Yaw → pitch | Alimentación Pi, USB hacia ESP32 y cable del servo roll |
| Pitch → roll | Alimentación Pi y USB; el motor de roll permanece en la horquilla |
| Dentro de roll | FFC estático Pi–cámara |

El buzzer puede quedarse sobre yaw: **no necesita ir en la cabeza**.

Usar bucles de servicio independientes cerca de cada eje. Para alimentación, mantener un cable realmente apto para **5 V/5 A**: una resistencia total de apenas **0,1 Ω** produciría **0,5 V** de caída a 5 A.

Dejar admisión y descarga del cooler despejadas, con una reserva inicial de **10–15 mm** frente a su entrada. La cara debe desmontarse sin desconectar repetidamente el FFC.

**[Medir]** Recorrer las **8 combinaciones extremas** de yaw/pitch/roll y trayectorias intermedias, primero manualmente. Después, al menos **100 ciclos lentos** verificando roces, tracción y continuidad de vídeo. Esto es aceptación de prototipo, no certificación de fatiga.

## 3. Tamaño y forma de la cabeza

**Recomendación: cara plana desmontable de aproximadamente 100 × 85 mm, con ojos fijos y cámara como nariz. Posponer la esfera y el cuerpo ornamental.**

**[Repo]** El enunciado permite cartón, MDF o impresión 3D. Exige ojos, orientación evidente y cámara solidaria; **no exige esfera**.

**[Propuesta]**

| Elemento | Medida inicial |
|---|---:|
| Cara | **100 × 85 mm** |
| Espesor impreso | **2–2,5 mm**, con nervios locales |
| Ojos | **Ø18–22 mm** |
| Separación entre centros de ojos | **42–48 mm** |
| Profundidad con Pi embarcada | **50–65 mm** |
| Fijación | **4 tornillos**, acceso lateral/posterior |

La cámara central facilita relacionar mirada física e imagen. Mantener la lente al ras o ligeramente adelantada y evitar un túnel estrecho.

**[Cálculo geométrico]** Una placa maciza de 100 × 85 × 2 mm tiene **17 cm³**. El CAD documenta **128 cm³** para las dos mitades de cabeza y **100 cm³** para el cuerpo: retirar ambos elimina **228 cm³** del diseño sólido, antes de agregar soportes nuevos.

No inventaría horas de impresión: dependen del slicer. La cara se imprime plana y permite rehacer rápidamente agujeros o posiciones.

Una esfera de **Ø110–120 mm** sería una alternativa estética posterior, preferentemente como cubierta parcial desmontable. **No se puede escalar uniformemente el CAD actual**: servos, horns, Pi y separaciones no escalan.

También hay que revisar el volumen barrido: una cara de **100 × 85 mm** girada 20° ocupa aproximadamente **123 × 114 mm** en su proyección frontal.

No reduciría la base solo por estética. La batería modelada mide **166 mm** de largo y el rodamiento **100 mm** de diámetro; condicionan tamaño y estabilidad. Quitar el cuerpo Ø200 es más sencillo que rediseñar toda la base.

## 4. Riesgos generales y plan hasta el 30/10

**Recomendación: tener seguimiento físico integrado antes del 19/10, completar funcionalidades el 22/10 y reservar del 23 al 29 para validación, correcciones y entrega.**

### Riesgos encontrados

| Prioridad | Evidencia | Consecuencia / acción |
|---|---|---|
| **P0** | `firmware/` vacío | Es el bloqueo principal de control físico |
| **P0** | Percepción produce `DetResult`; falta integración completa con `World` | Tener detectores funcionando no equivale a tener robot reactivo |
| **P0** | MG996R: **3 fallos en 10 retornos** de +10° a 0° | No aprobar su repetibilidad con cabeza montada |
| **P0** | FFC sin modelar ni validar | Riesgo de perder la única cámara |
| **P1** | Pose: **10,0 Hz con una persona** | Cero margen demostrado respecto del mínimo |
| **P1** | Mirada, saludo, camisetas y asociación incompletos | Faltan eventos reales filtrados, no solamente comportamientos |
| **P1** | `SerialLink` sin reconexión | Una desconexión puede abortar la aplicación |
| **P1** | Modos y SALIENDO ausentes | Cobertura incompleta de T2/T5 |
| **P1** | Monitoreo final incompleto | Falta evidencia integrada de T7 |

**MG996R:** “mandar directamente el objetivo” puede conseguir movimiento, pero **anula la limitación de velocidad/aceleración de la referencia de roll**. Tampoco garantiza que llegue al ángulo. No lo presentaría como solución conforme a T1.

Intentaría conseguir **otra unidad posicional sana del mismo tamaño** inmediatamente. El MG90S puede servir con cabeza liviana y equilibrada, pero con Pi embarcada necesita una nueva prueba de carga. La decisión debe cerrarse antes del **16/10**.

### Correcciones concretas del software

1. **Centro óptico ignorado.**  
   [gaze.py:45](</home/hecvelaz/Documentos/Keepon pro /keepon/gaze.py:45>) usa `(320,240)` y una focal derivada del HFOV. Configuración: `(428,50;225,42)`. La diferencia horizontal de **108,5 px** corresponde a aproximadamente **6,5°** con `fx=948,16`, si esa calibración es válida. Llevar `fx,fy,cx,cy` al control y corregir distorsión/roll coherentemente.

2. **Cola perceptiva acumulativa.**  
   [perception.py:290](</home/hecvelaz/Documentos/Keepon pro /keepon/perception.py:290>) crea una cola de **64 resultados** y los productores usan `put()` bloqueante. A **26,9 resultados/s** combinados puede acumular aproximadamente **2,4 s**. Usar entrega del último resultado por tipo y caducar evidencia.

3. **Asociación entre procesos.**  
   Sus contadores `frame` son locales a suscriptores independientes. Asociar pose y persona mediante timestamp y geometría; no asumir que igual número implica igual imagen.

4. **Saludo demasiado exigente.**  
   La referencia actual, amplitud **12°** y período **0,5 s**, pide aproximadamente **75,4 °/s** y **947 °/s²**, frente a `amax_pitch=400`. Probar **1,0–1,2 s por cabeceo** y comprobar el movimiento real.

5. **STOP y errores de transporte.**  
   `Robot.stop()` intenta transmitir antes de enclavar el árbitro. Si la escritura falla, debe quedar igualmente detenido el estado local. Añadir regresión junto con la recuperación serie.

6. **Watchdog y reanudación.**  
   El simulador sale de `WATCHDOG` al recibir un comando parseable. Verificar que la recuperación no reactive movimientos viejos y que STOP del operador sobreviva a reconexiones.

Estos hallazgos requieren tests al implementar correcciones; los **81 actuales no cubren toda esta integración**.

### Percepción, NoIR y latencia

**[Repo]** Hay evidencia de **16,9 Hz personas/rostros** y **10,0 Hz pose**, con **una persona**. No hay aceptación final con 2–3 personas, cámara móvil, camisetas, control y overlay.

**[Propuesta]** Medir por detector:

- Observaciones nuevas/s.
- Edad p50/p95/máxima.
- Caídas de ID y asociaciones ambiguas.
- CPU, temperatura y frecuencia durante **20–30 min**.
- Latencia hasta **inicio físico**, no hasta ACK.

Presupuesto inicial de ingeniería, **no medición**:

| Etapa | Reserva |
|---|---:|
| Captura, entrega e inferencia | 150 ms |
| Integración y árbitro | 25 ms |
| Serie | 4 ms |
| Espera del planificador | 10 ms |
| Espera de trama PWM | 20 ms |
| Inicio observable del servo | 50 ms |
| **Total** | **259 ms** |

Quedan **41 ms** de margen; hay que medir la cadena completa. Las ventanas de confirmación —por ejemplo **0,5 s de ME_MIRA**— se deben informar separadas. No pueden ocultarse dentro de una afirmación de “menos de 300 ms desde que empieza a mirar”.

**NoIR:** probar las prendas reales a **0,8 / 1,5 / 2,5 m**, con LED previsto y luz de ventana. Incluir lisas blanca, roja, azul y negra. Color más patrón, clase desconocida y rechazo ante torso pequeño u oculto. El balance de blancos no elimina información infrarroja mezclada con visible. [Documentación de cámaras](https://www.raspberrypi.com/documentation/accessories/camera.html).

No planificar una webcam inexistente como contingencia inmediata. Un IR-cut externo solo sirve si se consigue y valida pronto.

### Simplificaciones útiles

- Cabeza abierta, ojos fijos, sin LEDs ni párpados.
- Mantener YOLO26n/NCNN y BlazeFace; no migrar arquitectura ROS ni reabrir modelos sin un fallo medido.
- Pose para saludo, sin agregar Hands.
- Modos con máquinas de estado cortas.
- Sonidos breves; polca reconocible.
- Interfaz de teclado y overlay sencillo.
- Si la batería/reguladores no están listos, fuentes propias comprobadas: el enunciado no exige explícitamente autonomía con batería.

No eliminar tres GDL, buzzer pasivo, arbitraje, modos, camisetas, filtros o monitoreo y presentar después el resultado como completo.

### Plan propuesto

| Fecha | Resultado exigible |
|---|---|
| **14/10** | Congelar ESP32; maqueta Pi/cámara/FFC; identificar cámara; empezar firmware y pruebas de camisetas |
| **15/10** | HELLO/J/STOP/RESUME/PING, límites y PWM de tres servos; primer `DetResult → World` |
| **16/10** | Trayectoria, watchdog y buzzer concurrente; resolver servo roll; signos y postura de arranque |
| **17/10** | Montaje mínimo con cinta protegida; control visual usando intrínsecos correctos |
| **18/10** | Seguimiento físico yaw/pitch; roll operativo; prueba STOP, pérdida de proceso y enlace |
| **19/10** | Dos personas, foco, asociación y ME_MIRA filtrado; benchmark completo |
| **20/10** | SALUDO real y camisetas con negativos; seguimiento + sonido simultáneos |
| **21/10** | Tímido, Atrevido, Maleducado y SALIENDO; cambio de modo con beep |
| **22/10** | Congelar funcionalidades; overlay T7, logs y matriz T1–T7 completos |
| **23–24/10** | Latencias, tasas, cruces, falsos positivos y fallos de cámara/USB |
| **25–26/10** | Ensayos de 20–30 min; alimentación, temperatura, cables y repetibilidad |
| **27/10** | Video ≤3 min, informe Colab, código y procedimiento de arranque |
| **28/10** | Ensayo completo sin Internet y defensa cruzada |
| **29/10** | Solo correcciones pequeñas, respaldo y repuestos |
| **30/10** | Demo física |

Distribuirlo entre integrantes: mecánica/electricidad, firmware, percepción, camisetas/métricas e integración/modos. **Si el 18/10 no hay seguimiento físico, suspender trabajo estético y concentrarse en integración.**

## 5. Si la cámara es Wide

**Recomendación: confirmar la variante y calibrar el modo real de captura; no reemplazar `hfov_deg` por 120°.**

**[General/documentado]**

| Camera Module 3 | HFOV nominal | FOV diagonal |
|---|---:|---:|
| Normal | **66°** | **75°** |
| Wide | **102°** | **120°** |

Los **120° son diagonales**. Además, el campo del stream depende del recorte y modo de lectura. `IMX708` por sí solo no identifica la lente. [Descripción oficial](https://www.raspberrypi.com/news/new-autofocus-camera-modules/), [especificaciones](https://www.raspberrypi.com/products/camera-module-3/).

### Configuración e intrínsecos

**[Repo]** `fx=948,16`, `cx=428,50` y HFOV de **37,3°** proceden de una calibración ajena pendiente de comprobar. El supuesto recorte de `camera_ros` **no queda demostrado por una calibración cuya correspondencia todavía se desconoce**.

Actualizar juntos:

- `fx`, `fy`, `cx`, `cy`.
- Distorsión y modelo utilizado.
- Resolución, recorte y enfoque.
- `hfov_deg`, derivado del campo efectivo.
- Control visual y simulación.

Con punto principal descentrado, sin distorsión:

\[
HFOV=\arctan(c_x/f_x)+\arctan((W-c_x)/f_x)
\]

No usar automáticamente \(2\arctan(W/2f_x)\). Para Wide, obtener los rayos de borde con la calibración de distorsión cuando se necesite mayor precisión.

### Personas más pequeñas a 256 px

**[Estimación pinhole, mismo ancho procesado y campo completo]**

\[
\frac{f_\text{Wide}}{f_\text{Normal}}
=\frac{\tan33°}{\tan51°}\approx0,53
\]

Una persona cerca del centro tendría aproximadamente **53 % del tamaño lineal** y **28 % del área** respecto de la cámara normal a igual distancia.

Ejemplo ilustrativo: objeto de **0,5 m de ancho a 1,5 m**, con imagen de 256 px de ancho:

| HFOV | Ancho aproximado |
|---|---:|
| 66° | 66 px |
| 102° | 35 px |
| 37,3° | 126 px |

No son resultados de YOLO. Muestran por qué **256 px debe reevaluarse**: detectar personas puede seguir funcionando mientras rostros y patrones de camiseta dejan de tener detalle suficiente. Ampliar después el recorte a 192 px no recupera información perdida.

Orden de prueba:

1. Mantener 256 y medir distancias reales.
2. Si falla, probar recorte central conservando resolución útil.
3. Comparar modelo NCNN exportado a **320 px**.
4. Repetir benchmark completo: 320 tiene **1,56 veces** el área de 256; no implica exactamente 1,56 veces el tiempo.

### Mecánica y lente

**[Repo]** El CAD usa profundidad de cámara **11,5 mm** y un avellanado de **40° de semiángulo**. La Wide ronda **12,4 mm** de profundidad. Revisar soporte y ventana. [Especificaciones mecánicas](https://www.raspberrypi.com/documentation/accessories/camera.html).

Con HFOV de 102°, el semiángulo horizontal es **51°**. Como referencia geométrica, una pared situada **5 mm delante de la lente** necesita aproximadamente:

\[
5\tan51°=6,2\ \mathrm{mm}
\]

de apertura adicional **por lado**, además del tamaño útil de la lente. Por eso conviene lente al ras y una abertura amplia. Verificar que ojos, borde facial, cable y soportes no aparezcan en las esquinas.

| Decisión | Recomendado | Alternativa | Por qué |
|---|---|---|---|
| Control de actuadores | **ESP32-C3 existente** | RP1 con cuatro PWM hardware | Reutiliza contrato y separa watchdog de Linux |
| Generación PWM | **LEDC hardware** | RP1 / PCA9685 | Evita flancos temporizados desde Python |
| Cinta de 150 mm | **Pi y cámara solidarias sobre roll** | Pi en pitch/yaw con recorrido validado | Elimina flexión dinámica del FFC |
| Cabeza | **Cara 100 × 85 mm desmontable** | Cubierta parcial Ø110–120 mm | Menos impresión y mejor acceso |
| Roll | **Unidad con repetibilidad comprobada** | MG90S si pasa carga | El MG996R actual tiene fallos medidos |
| Cámara | **Calibrar variante y modo reales** | Recorte central validado | Los intrínsecos actuales son inciertos |
| Alimentación de demo | **Fuentes comprobadas y separadas** | Batería con regulación ya validada | Evita agregar otro frente crítico |
| Prioridad inmediata | **Firmware + integración física + FFC** | Acabado después del 22/10 | La demo física del 30/10 es obligatoria |