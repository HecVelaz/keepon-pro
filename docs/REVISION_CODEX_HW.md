**Veredicto: sí con condiciones, pero hoy faltan un servo y el firmware físico.**

| Elemento | Veredicto | Elección |
|---|---|---|
| Yaw | **Sí con condiciones** | MG90S, con rodamiento que soporte peso y flexión; cable CSI sin tensión |
| Pitch | **Sí con condiciones** | MG90S para cabeza **≤150 g y CG ≤2 cm**, incluyendo las cargas adicionales indicadas abajo |
| Roll | **Sí con condiciones** | SG90 si la cabeza está equilibrada respecto de roll |
| ESP32-C3-DevKitM-1 | **Sí** | Suficiente para trayectoria, serie y sonido; usar inicialmente el micro-USB con puente UART |
| Solo los 2 servos disponibles | **No** | No cumplen los 3 GDL |

No modifiqué archivos. **Dato documental** significa especificación publicada, no medición de sus unidades; **estimación** significa cálculo con hipótesis explícitas.

## A. Par y viabilidad por eje

### Base de cálculo

Usaría **5 V regulados** y calcularía con el par publicado a **4,8 V**, sin aprovechar un supuesto aumento a 6 V.

| Servo | Par de bloqueo usado | Presupuesto al 30 % | Techo al 50 % |
|---|---:|---:|---:|
| SG90 | 1,2 kgf·cm | 0,36 kgf·cm | 0,60 kgf·cm |
| MG90S | 1,8 kgf·cm | 0,54 kgf·cm | 0,90 kgf·cm |

**El 30–50 % es un criterio de dimensionamiento, no un régimen continuo garantizado por fabricante.** Apuntaría al 30 %; aceptaría acercarse al 50 % únicamente después de ensayos térmicos y de movimiento.

Hay inconsistencias entre versiones: el PDF local del MG90S indica 5 µs y 2,2 kgf·cm a 6 V; la página actual de TowerPro publica otros valores. El SG90 digital actual tampoco coincide con la ficha de su tienda. Por eso no asumiría que sus unidades tienen mejores prestaciones que las suministradas. [MG90S de TowerPro](https://towerpro.com.tw/product/mg90s-3/), [SG90 digital de TowerPro](https://towerpro.com.tw/product/sg90-7/).

### Par estático de la cabeza

\[
\tau=m g d_\perp,\qquad
\tau[\mathrm{kgf\,cm}]=m[\mathrm{kg}]\,d_\perp[\mathrm{cm}]
\]

**Importante:** \(d_\perp\) es el brazo perpendicular a la gravedad. Si conocen solamente la distancia entre eje y CG, usarla completa da una estimación conservadora. Evaluar la peor postura del rango, no solamente HOME.

**Estimación, cabeza sola:**

| Masa | CG a 1 cm | CG a 2 cm | CG a 3 cm |
|---|---:|---:|---:|
| 80 g | 0,080 kgf·cm | 0,160 kgf·cm | 0,240 kgf·cm |
| 150 g | 0,150 kgf·cm | 0,300 kgf·cm | 0,450 kgf·cm |
| 250 g | 0,250 kgf·cm | 0,500 kgf·cm | 0,750 kgf·cm |

Conversión: **1 kgf·cm = 0,0981 N·m**.

La masa de cabeza debe incluir cámara, carcasa, ojos, tornillería y cable que realmente se mueve. Los ~4 g de cámara son poco; la rigidez del CSI puede ser más importante que su peso.

### Carga en serie y dinámica

\[
\tau_\text{requerido}\approx
\sum m_i g d_{\perp i}+I_\text{eje}\alpha+
\tau_\text{fricción}+\tau_\text{cable}
\]

Las aceleraciones actuales equivalen a:

| Eje | Configuración | En rad/s² |
|---|---:|---:|
| Yaw | 600 °/s² | 10,47 |
| Pitch | 400 °/s² | 6,98 |
| Roll | 300 °/s² | 5,24 |

**Modelo estimado para pitch:** radio de giro de la cabeza respecto de su CG \(k=3\) cm, de modo que \(I=m(k^2+d^2)\). Reservo además **0,10 kgf·cm** para servo de roll, soportes, cable, fricción y dinámica de esos elementos.

Ejemplo de esa reserva: SG90 de 9 g a 2 cm aporta **0,018 kgf·cm**; soporte de 20 g a 2 cm aporta **0,040 kgf·cm**. Quedan ~0,042 para el resto. **Hay que medirla: no es una propiedad del montaje.**

| Cabeza y CG | Estático cabeza | Dinámico cabeza, 400 °/s² | Total con reserva | % bloqueo SG90 | % bloqueo MG90S |
|---|---:|---:|---:|---:|---:|
| 80 g, 1 cm | 0,080 | 0,006 | **0,186** | 15 % | 10 % |
| 150 g, 2 cm | 0,300 | 0,014 | **0,414** | 34 % | 23 % |
| 250 g, 3 cm | 0,750 | 0,032 | **0,882** | 74 % | 49 % |

Pares en kgf·cm. Para **150 g a 2 cm**, el MG90S tiene relación bloqueo/carga de **4,35**; el SG90, **2,90**.

La gravedad domina estos ejemplos. Bajar aceleración mejora golpes y vibración, pero **no resuelve una cabeza pesada y desbalanceada**.

### Evaluación por eje

| Eje | Carga y criterio |
|---|---|
| **Yaw: MG90S** | Carga cabeza + mecanismos de pitch y roll. Con eje vertical, la gravedad idealmente aporta **0 par alrededor de yaw**, aunque produce carga axial y flexión. Para 200–300 g móviles y radio de giro de 3–5 cm, el par inercial a 600 °/s² es aproximadamente **0,019–0,080 kgf·cm**. El cable y el rozamiento pueden dominar. |
| **Pitch: MG90S** | Carga cabeza + servo/mecanismo de roll. Es el eje más exigente por gravedad y cabeceos repetidos. Preferir soporte a ambos lados del eje. |
| **Roll: SG90** | Carga la cabeza. Para 150 g y brazo gravitatorio máximo de 1 cm: **0,15 kgf·cm**, antes de dinámica y cable. Viable. Para 250 g a 3 cm: **0,75 kgf·cm**, inviable con este criterio. |

**Estar centrado lateralmente en HOME no garantiza roll equilibrado:** un CG situado 3 cm por encima del eje genera brazo \(3\sin20°=1,03\) cm al inclinarse 20°. Con 150 g, son **0,154 kgf·cm**.

El rodamiento de yaw debe absorber también el momento de vuelco mediante una estructura adecuada; un apoyo axial aislado puede no hacerlo.

### Masa máxima estimada en pitch

Aplicando el modelo anterior:

\[
m_\max=
\frac{f\,\tau_\text{bloqueo}-0,10}
{d+0,00712(9+d^2)}
\]

Con masa en kg, \(d\) en cm y \(f=0,30\) o \(0,50\).

| Distancia CG | SG90: objetivo 30 % / techo 50 % | MG90S: objetivo 30 % / techo 50 % |
|---|---:|---:|
| 1 cm | 243 / 467 g | 411 / 747 g |
| 2 cm | 124 / 239 g | 210 / 382 g |
| 3 cm | 83 / 160 g | 141 / 256 g |

**Estos son límites del modelo de par, no capacidades certificadas del cuello.** Los valores grandes pueden resultar inviables por flexión, tamaño, juego o inercia real.

Mi envolvente práctica inicial:

- **SG90 en pitch:** ≤100 g a ≤2 cm; 150 g solamente cerca de ≤1 cm y después de probar.
- **MG90S en pitch:** ≤150 g a ≤2 cm. Para 250 g, buscar **≤1 cm** o pasar a un servo mayor.
- **250 g a 3 cm:** no elegiría MG90S para una demo robusta; queda prácticamente en el techo del 50 %.

## B. Precisión y suavidad

### Banda muerta y resolución

Si efectivamente **1.000–2.000 µs corresponden a 180°**:

\[
180°/1000\,\mu s=0,18°/\mu s
\]

| Concepto | Resultado |
|---|---:|
| Banda muerta MG90S: 5 µs | **0,90°** |
| Banda muerta SG90: 7 µs | **1,26°** |
| LEDC de 14 bits, 50 Hz | **1,221 µs/paso ≈0,220°/paso** |

La banda muerta no equivale a exactitud absoluta ni incluye holgura. Calibrar la pendiente real grados/µs: **“180°” y “1–2 ms” no garantizan ese recorrido en cada unidad**. Esto es especialmente importante para los **140° totales de yaw**.

- **SG90:** engranajes plásticos, mayor susceptibilidad a deformación y daño por golpes.
- **MG90S:** mejor resistencia mecánica; **metal no garantiza menor juego**.
- No hay un valor fiable de backlash para sus ejemplares. Medir el ángulo perdido al invertir dirección.
- Un PWM estable elimina jitter eléctrico de generación, pero no el temblor por juego, carga, alimentación o control interno del servo.

Con \(f_x≈948\) px del repo, **1° corresponde a unos 16,5 px** cerca del centro. Las bandas muertas anteriores equivalen aproximadamente a **15 y 21 px**: relevantes para seguimiento. La zona muerta actual de yaw, 3 % de 640, es **19,2 px ≈1,16°**.

### Sí, bajaría vmax/amax inicialmente

**Propuesta de puesta en marcha, no límite definitivo:**

| Parámetro | Actual yaw/pitch/roll | Propuesto |
|---|---|---|
| `neck.vmax`, °/s | 180 / 120 / 90 | **90 / 60 / 45** |
| `neck.amax`, °/s² | 600 / 400 / 300 | **300 / 200 / 150** |
| `gaze.vmax`, °/s | 150 / 90 | **75 / 45** |

Mantener **trayectoria a 100 Hz** y PWM de servos a **50 Hz**. Son frecuencias distintas: el servo recibe un pulso nuevo cada 20 ms. Al máximo actual, los incrementos por trama pueden ser **3,6° / 2,4° / 1,8°**; con la propuesta, la mitad.

La velocidad de hoja de 500–600 °/s es **sin carga**. No prueba que esos movimientos sean suaves con la cabeza instalada. Además, la trayectoria limita referencias; no mide ni garantiza aceleración física del eje.

**Hallazgo concreto del saludo:** [keepon/behaviors.py, línea 139](</home/hecvelaz/Documentos/Keepon pro /keepon/behaviors.py:139>) usa \(12\sin^2(\pi t/0,5)\). Eso pide aproximadamente:

- Velocidad máxima: **75,4 °/s**.
- Aceleración máxima: **947 °/s²**.

Ya supera `amax_pitch=400`. Con **período 1,2 s**, baja a **31,4 °/s y 164,5 °/s²**. Mantendría los **3 cabeceos**, ahora en 3,6 s, comprobando su coordinación con R2D2. El mentón de Atrevido necesita el mismo ajuste de amplitud/período.

## C. ESP32-C3 frente al S3

### Recursos y pines

**Sí alcanza.** El C3 dispone de **6 canales LEDC, 4 timers y resolución máxima de 14 bits**, en modo low-speed. “Low-speed” no significa insuficiente para servos. [Documentación LEDC de Espressif](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/api-reference/peripherals/ledc.html).

Asignación recomendada mediante configuración explícita de LEDC:

| Función | GPIO | Canal | Timer |
|---|---:|---:|---|
| Yaw | 0 | 0 | 0, 50 Hz |
| Pitch | 1 | 1 | 0, 50 Hz |
| Roll | 3 | 2 | 0, 50 Hz |
| Buzzer, hacia transistor | 10 | 3 | 1, frecuencia variable |

Los tres servos comparten frecuencia, pero tienen duty independiente. Para buzzer usar, por ejemplo, **10 bits y 50 % de duty**. Verificar la asignación si emplean librerías Arduino: no asumir que canales distintos implican timers distintos.

Evitar GPIO **2/8/9** —strapping—, **18/19** —USB— y **20/21** —UART0—. GPIO8 además maneja el RGB. La placa expone **15 GPIO**, aunque el chip se describa con 22. [Guía de DevKitM-1](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32c3/esp32-c3-devkitm-1/user_guide.html).

**Estimación de capacidad:** tres ejes a 100 Hz representan 300 actualizaciones/s; a 160 MHz hay 1,6 millones de ciclos por período de 10 ms. Un núcleo y 400 KB SRAM son suficientes para parser, trayectoria y secuenciador. No hace falta Wi-Fi/BLE ni almacenar audio: guardar tablas de notas y duraciones. [Ficha del C3](https://documentation.espressif.com/esp32-c3_datasheet_en.html).

Condiciones:

- Parser acotado, sin esperas por líneas completas.
- Sin `delay()` ni bucles que esperen terminar sonidos.
- Paso periódico de 10 ms, con medición de retrasos.
- Evitar que logs o escrituras serie bloqueen el lazo.

### Señal de 3,3 V

Muchos servos aceptan 3,3 V como nivel alto, pero **sus hojas no garantizan el umbral de entrada**.

Probar primero con masa común y cable corto. Si falla o quieren asegurar margen lógico, usar **74AHCT125 alimentado a 5 V**, con desacople de 100 nF. No alimentar ese buffer con 6 V ni poner 5 V sobre GPIO del C3.

### Puerto serie y reinicio

| Conexión | Dispositivo Linux habitual | Recomendación |
|---|---|---|
| Micro-USB de DevKitM-1 → puente UART | `/dev/ttyUSB0` | **Usarlo para M1** |
| USB nativo en GPIO18 D− / GPIO19 D+ | `/dev/ttyACM0` | Posible, pero agrega cableado y validación |

El número final puede cambiar; preferir **`/dev/serial/by-id/...`**, si existe. USB nativo requiere conexión física correcta, GND y consola/firmware configurados para USB Serial/JTAG; no basta cambiar el nombre de puerto. [USB Serial/JTAG del C3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/api-guides/usb-serial-jtag-console.html).

**El protocolo ASCII v1 puede conservarse.** Mantener UART a 115200 baud; una línea de 40 bytes tarda aproximadamente **3,5 ms** en 8N1.

El puente puede actuar sobre EN/BOOT mediante **DTR/RTS**. Abrir el puerto puede provocar transitorios y reinicio; no ocurre necesariamente en cada apertura. `rtscts=False` no garantiza que esas líneas permanezcan inactivas. [Auto-reset de Espressif](https://docs.espressif.com/projects/esptool/en/latest/esp32c3/advanced-topics/boot-mode-selection.html), [API de pySerial](https://pyserial.readthedocs.io/en/latest/pyserial_api.html).

**Revisión del repo:**

- [SerialLink, línea 102](</home/hecvelaz/Documentos/Keepon pro /keepon/link.py:102>): abre inmediatamente; no configura DTR/RTS previamente.
- Líneas **109–120**: no capturan desconexiones ni reabren el dispositivo. El buffer tampoco tiene un límite explícito.
- `timeout=0` hace no bloqueante la lectura; `write_timeout=0.05` permite bloquear **hasta 50 ms** en escritura.
- [Actuators, línea 59](</home/hecvelaz/Documentos/Keepon pro /keepon/actuators.py:59>) reconoce sesión aceptada y reinicio.
- [Robot, línea 69](</home/hecvelaz/Documentos/Keepon pro /keepon/robot.py:69>) cancela acciones y conserva STOP; línea **85** reintenta HELLO cada 500 ms.

**Falta recuperación del transporte**, aunque existe recuperación lógica ante `HELLO 0`.

Cambios necesarios: controlar DTR/RTS antes de abrir, tolerar igualmente un reset, capturar errores, cerrar/reintentar sin bloquear, invalidar sesión al perder conexión, descartar comandos antiguos y exigir nuevo `HELLO 1 fw proto`. Reenviar STOP si estaba activo, incluso si la reconexión ocurre **sin reinicio del micro**.

**Riesgo de arranque:** el simulador inicializa HOME en [sim_esp32.py, línea 38](</home/hecvelaz/Documentos/Keepon pro /keepon/sim_esp32.py:38>). Un servo real puede estar en otra posición: mandar HOME produce un salto. Sin sensor de posición, una rampa desde un HOME supuesto no resuelve esto. Para M1, establecer una postura inicial controlada y probar reinicios con la cabeza sostenida.

## D. Alimentación

**Estimaciones para microservos; verificar los ejemplares:**

| Estado | Por servo | Tres servos |
|---|---:|---:|
| Quieto, prácticamente descargado | 5–20 mA | 15–60 mA |
| Movimiento con carga moderada | 100–300 mA | 0,3–0,9 A |
| Arranque/bloqueo, supuesto suministrado | 650–750 mA | **1,95–2,25 A** |

Quieto **sosteniendo carga** puede consumir mucho más que el reposo descargado. Los 750 mA tampoco son un máximo universal para cualquier clon.

**Recomiendo fuente regulada de 5 V, 4 A; 3 A sería el mínimo razonable para estos tres microservos ensayados.** Una de 2 A queda corta frente al pico simultáneo supuesto de 2,25 A.

- No alimentar servos desde el pin 5 V de la DevKit: no es una salida de potencia regulada para motores. Con USB conectado, podrían consumir a través del cable, pistas y puerto anfitrión.
- No alimentarlos desde la Pi: sus transitorios pueden causar caídas de tensión, reinicios y fallos de cámara.
- Pi con fuente propia; C3 puede recibir alimentación por su USB desde la Pi.
- Fuente de servos directamente a una distribución con borneras. **GND común**, con retorno de motores hacia esa distribución.
- No unir positivos de ambas fuentes ni inyectar 6 V al riel USB.
- **1.000–2.200 µF, ≥10 V**, cerca de la distribución; **100 nF** cerca de cada derivación.
- Cable principal corto, aproximadamente **AWG20–22**, conectores firmes y corte de potencia de servos accesible.

El capacitor no reemplaza la fuente: 2.200 µF entregando 1 A durante 1 ms ya cae aproximadamente **0,45 V**.

**Buzzer:** NPN 2N2222 como interruptor de lado bajo, resistencia de base **1 kΩ**, resistencia base-emisor **10 kΩ**; verificar corriente del buzzer. Si es electromagnético, agregar protección para carga inductiva; si es piezoeléctrico, no necesita diodo de rueda libre.

“Alimentación propia” aparece en el enunciado, pero **no exige explícitamente batería**. Llevar fuentes y distribución propias cumple esa lectura; autonomía sin enchufe requeriría dimensionamiento adicional.

## E. Compras y cambios priorizados

### Para M1 — 8/10

1. **Comprar 1 MG90S como mínimo; 2 si hay disponibilidad.** Quedan yaw/pitch MG90S, roll SG90 y, comprando dos, un MG90S de repuesto.
2. **Fuente 5 V/4 A**, capacitor, borneras, cableado y corte de potencia.
3. **Rodamiento/soporte de yaw**, apoyo de pitch, tornillos y horns adecuados.
4. Cable **micro-USB de datos** y CSI **22→15 pines**, 30–50 cm, con alivio de tensión.
5. Buzzer pasivo + transistor y resistencias para avanzar hacia M2.
6. Pesar y equilibrar antes de cerrar la carcasa.

**Bloqueo principal:** `firmware/` está vacío. M1 exige tres ejes físicos, no solamente comprar el tercero. La prioridad inmediata es portar trayectoria/protocolo y mover la cabeza real.

### Para M2 y demo — 15/10 y 30/10

- Integrar sonido concurrente y verificar que cambiar notas no altera servos.
- Incorporar repuesto probado, no solamente embalado.
- Resolver reconexión y encendido.
- Si pitch supera el presupuesto o falla el ensayo: servo mayor y soporte adaptado.
- Ensayar **20–30 minutos continuos** con seguimiento, saludo y mentón.

### Archivos a actualizar si adoptan C3/microservos

| Archivo y líneas actuales | Cambio |
|---|---|
| [config.yaml:3](</home/hecvelaz/Documentos/Keepon pro /config.yaml:3>), 3–17 | Conservar rangos; ajustar vmax/amax; puerto estable del puente UART; mantener watchdog/keepalive |
| [config.yaml:81](</home/hecvelaz/Documentos/Keepon pro /config.yaml:81>), 81–86 y 100–103 | Reducir velocidad visual; saludo a ~1,2 s por cabeceo |
| [keepon/link.py:95](</home/hecvelaz/Documentos/Keepon pro /keepon/link.py:95>), 95–121 | DTR/RTS, reconexión, errores, buffers acotados y descarte de transmisiones antiguas |
| [keepon/actuators.py:51](</home/hecvelaz/Documentos/Keepon pro /keepon/actuators.py:51>), 51–74 | Invalidar sesión también ante pérdida de transporte; limpiar pendientes |
| [keepon/robot.py:69](</home/hecvelaz/Documentos/Keepon pro /keepon/robot.py:69>), 69–89 | Resincronizar tras reconexión; conservar STOP |
| [keepon/sim_esp32.py:38](</home/hecvelaz/Documentos/Keepon pro /keepon/sim_esp32.py:38>), 38–118 | Fuente para portar sesión, STOP, watchdog y sonido; revisar contrato de arranque |
| [keepon/trajectory.py:44](</home/hecvelaz/Documentos/Keepon pro /keepon/trajectory.py:44>), 44–67 y 74–96 | Portar fórmula y frenado; no sustituirlos por saltos directos de ángulo |
| [docs/PROTOCOLO.md:1](</home/hecvelaz/Documentos/Keepon pro /docs/PROTOCOLO.md:1>), 1–7, 38–55 | C3/UART, apertura, reconexión y comportamiento real de arranque |
| [docs/HOJA_DE_RUTA.md:4](</home/hecvelaz/Documentos/Keepon pro /docs/HOJA_DE_RUTA.md:4>), 4–5 y 46–68 | Inventario real, ficha de carga, servos, fuente, pines y trayectoria a 100 Hz |
| [README.md:57](</home/hecvelaz/Documentos/Keepon pro /README.md:57>), además 3 y 65–67 | Hardware, conexión y estado del firmware/reconexión |
| [CLAUDE.md:16](</home/hecvelaz/Documentos/Keepon pro /CLAUDE.md:16>), además 32 y 99 | Quitar supuestos operativos de S3 |
| [scripts/check_pi.sh:30](</home/hecvelaz/Documentos/Keepon pro /scripts/check_pi.sh:30>), 30–31 | Identificación del C3 y mensaje de diagnóstico |
| [docs/hoja_de_ruta.html:400](</home/hecvelaz/Documentos/Keepon pro /docs/hoja_de_ruta.html:400>), 400–403 | Sincronizar selección de hardware si siguen usando esa vista |

Crear firmware con calibración **por eje**: GPIO, timer/canal, sentido, centro y límites de pulso. El C3 no lee automáticamente el YAML de la Pi: transferir o generar parámetros y comprobar que coincidan.

No modificaría el enunciado ni reescribiría revisiones históricas.

## F. Pruebas rápidas de banco

**Criterios propuestos de aceptación, no datos de hoja.** Cada bloque lleva 15–30 minutos.

| Prueba | Procedimiento | Aceptación |
|---|---|---|
| Masa/CG | Pesar conjunto; medir equilibrio; calcular momentos de cabeza, roll y soportes | Pitch preferentemente ≤30 % del bloqueo; nunca aprobar >50 % |
| Recorrido | Primero sin carga; calibrar pulsos, luego montar y recorrer los extremos lentamente | Yaw ±70°, pitch −20/+30°, roll ±20° sin tope, roce ni cable tirante |
| Pitch cargado | Sostener peor postura 5 min; repetir cabeceos 10–15 min | Sin deriva creciente, dientes saltando ni calentamiento progresivo; parar ante carcasa ~50 °C como umbral conservador |
| Potencia | Mover tres ejes y buzzer; medir tensión en conectores, idealmente con osciloscopio | Mantener ≥4,8 V; ningún reinicio ni caída de cámara |
| Precisión | Llegar al mismo ángulo desde ambos sentidos; filmar puntero/cámara | Objetivo inicial: repetibilidad ≤2° y temblor en reposo <1° pico a pico |
| LEDC | Mantener posición mientras buzzer barre 500–4.000 Hz | PWM de servo permanece a 50 Hz, sin cambio de ancho asociado al sonido |
| Serie/reinicio | Abrir/cerrar 10 veces; resetear; desconectar/reconectar USB | Sin caída del programa; nueva sesión; sin sonidos/comandos viejos; STOP conservado |
| Watchdog | Cortar comandos durante movimiento | Frenado comienza ~500–510 ms después del último comando válido |
| Visión | Persona quieta y caminando; probar extremos de yaw con CSI instalado | Sin oscilación sostenida, tirones del cable ni pérdida de video |

**Watchdog de 500 ms no significa detenido a los 500 ms.** A velocidad máxima actual, el frenado necesita otros **~300 ms**; la distancia discreta de frenado es aproximadamente **26,1° yaw, 17,4° pitch y 13,1° roll**. Probarlo primero lejos de extremos y con amplitud reducida.

No mantendría un servo bloqueado para medir corriente: usar carga controlada, límite de corriente y cortar inmediatamente si no se mueve.

## G. Revisión de la recomendación previa

**Estoy de acuerdo con comprar 2 MG90S y asignar pitch/yaw MG90S, roll SG90**, con cuatro correcciones:

1. **Cambiar fuente ≥2 A por 5 V/4 A recomendados.**
2. Los **150 g a 2 cm** deben incluir cabeza/cámara y contemplar aparte roll, soportes y cable.
3. El rodamiento de yaw debe descargar peso **y flexión**.
4. Añadir velocidades iniciales menores, saludo más lento y validación de recorrido, temperatura y reinicios.

| Compra | Resultado | Decisión |
|---|---|---|
| **1 MG90S** | 2 MG90S + 1 SG90, sin repuesto | Mínimo correcto para M1 |
| **2 MG90S** | Misma asignación + 1 MG90S de repuesto | **Mi recomendación para cabeza ≤150 g/≤2 cm** |
| “Otro cualquiera” | Prestaciones, recorrido y montaje inciertos | **No**; especificar servo posicional, tensión, par y recorrido |
| Servo mayor en pitch | Más margen; nuevo soporte y mayor demanda eléctrica | Preferible si cabeza pesada/desbalanceada o ensayo fallido |

Para **250 g a 3 cm**, el modelo exige ~0,88 kgf·cm. Para trabajar al 30 %, basta nominalmente un servo de **≥3 kgf·cm** a la tensión usada. El **MG996R**, publicado con **9,4 kgf·cm a 4,8 V**, tiene amplio margen de par, aunque no garantiza mejor precisión. [Ficha del fabricante](https://towerpro.com.tw/product/mg996R/).

Un DS3218 también implica revisar variante, recorrido, corriente y montaje; no lo compraría solo por el número de torque anunciado. Al agrandar pitch, recalcular yaw porque ahora gira un servo y soporte más pesados.

**Elección concreta:** para llegar mañana a M1, cabeza liviana y **1 MG90S adicional obligatorio; 2 adicionales si pueden comprarlos hoy**. Para la demo, conservar esa solución solo si pasa las pruebas. Si ya saben que la cabeza quedará cerca de **250 g y 3 cm**, conviene pasar pitch a un servo mayor desde ahora.