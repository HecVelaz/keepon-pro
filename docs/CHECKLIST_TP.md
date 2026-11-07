# Checklist del TP de Robótica Social

Preparado el 7 de noviembre de 2026. Fuente principal: `2026S2uTP_RoboticaSocial.pdf`, 9 páginas, fechado el 30 de septiembre de 2026. Referencias de página indicadas por sección.

**Revisado el 07/11/2026** contra el código, `config.yaml`, `docs/ESTADO.md`, `docs/PENDIENTES.md` y `docs/BITACORA.md` (219 tests pasan).
Leyenda: `[x]` ✅ hecho y probado en el robot · `[ ]` 🟡 hecho sin probar en real, o a medias · `[ ]` ❌ falta.
Un diseño CAD o una pieza en una carpeta no prueban que el componente esté montado o funcionando: solo se marca `[x]` lo probado.

> ⚠️ **Fecha:** `CLAUDE.md` dice demo el 30/10/2026, pero el trabajo sigue al 07/11 y `PENDIENTES` habla del "domingo después del parcial". Confirmar con la cátedra la fecha de la demo y la de los archivos.

## 1. Qué entregar

### Entrega y defensa presencial (pp. 1 y 7)

- [x] ✅ Prototipo físico funcional: cabeza con ojos, cuello de 3 grados de libertad, cámara solidaria y buzzer pasivo. — v6 R4 armado.
- [ ] 🟡 Alimentación propia y todos los cables necesarios; robot listo para la prueba. El PDF no exige específicamente batería. — fuente de 6 V + powerbank andando; falta medir ≥ 4,9 V en la Pi y soldar el cable del buzzer.
- [ ] ❌ Demostración presencial en el LAR, en la fecha del Segundo Parcial. El PDF no da una fecha calendario. — fecha a confirmar.
- [ ] ❌ Presencia de todos los integrantes, máximo 5 personas. — integrantes no registrados en el repo.
- [ ] ❌ Cada integrante puede explicar cualquier parte del sistema y la contribución individual queda identificada.
- [ ] ❌ Comprender el código y las decisiones, incluidos los desarrollos asistidos con IA. — falta ensayar la defensa.

**Condición decisiva:** sin demostración funcional del prototipo físico no se asigna puntaje en el Test. Un video o simulación no sustituyen la demo. El trabajo vale 15 puntos: 3 directos y 12 adicionales; el PDF no incluye una rúbrica numérica por función.

### Informe técnico en Cuaderno Colab (p. 7)

El Colab no está empezado. Entre corchetes, de dónde sale el material que ya existe.

- [ ] ❌ Descripción del mecanismo, electrónica y conexiones. [`docs/HARDWARE.md`, `docs/diseno_v6/`; `docs/diagrama_sistema/` está desactualizado]
- [ ] ❌ Modelos de IA y librerías utilizados, con sus fuentes. [`docs/ARQUITECTURA.md`, `requirements.txt`]
- [ ] ❌ Definición operativa de cada evento: umbrales, confianza y filtros temporales. [`config.yaml`, `keepon/eventos.py`]
- [ ] ❌ Arquitectura: percepción, modelo del mundo, comportamientos, árbitro y control. [`docs/ARQUITECTURA.md`]
- [ ] ❌ Tabla de prioridades, recursos e interrupciones. [`config.yaml` → `priorities`]
- [ ] ❌ Diagramas de estados de los modos de personalidad.
- [ ] ❌ Parámetros utilizados: ganancias, límites, umbrales, tiempos, cooldowns e histéresis. [`config.yaml`]
- [ ] ❌ Resultados y pruebas de funcionamiento; incluir mediciones de frecuencia y latencia. [`docs/ESTADO_PI.md`; falta la latencia]
- [ ] ❌ Identificación de aportes individuales.

### Archivos finales (pp. 7 y 8)

- [x] ✅ Código fuente completo y comentado: percepción, control, comunicación, comportamientos y arbitraje. — en español; falta integrar los PR #3 → #4 → #5 a `main`.
- [x] ✅ README con instalación, dependencias, configuración, conexiones, ejecución y comandos de modo/STOP. — reescrito el 07/11 (`README.md`).
- [ ] ❌ Código en archivo ZIP y enlace al repositorio. — el repo es público (github.com/HecVelaz/keepon-pro); falta el ZIP.
- [ ] ❌ Video de hasta 3 minutos que muestre todos los comportamientos.
- [ ] ❌ Cuaderno Colab accesible y completo.
- [ ] 🟡 Opcional: archivos CAD del mecanismo. — en `docs/diseno_v6/`; falta compartir `Keepon_V6_R4.zip` por Drive.
- [ ] ❌ Verificar que enlaces, ZIP y video abren desde otra cuenta/equipo.
- [ ] ❌ Confirmar con la cátedra el plazo de los archivos: p. 1 pide documentación antes del inicio de la demo; p. 8 indica el domingo posterior al Segundo Parcial. Como planificación conservadora, preparar y subir todo antes de la demo hasta recibir aclaración.

## 2. Qué hacer y probar

### A. Construcción y control del robot - T1 (pp. 2 a 4)

- [x] ✅ Construir cabeza con ojos y dirección de mirada evidente.
- [x] ✅ Integrar yaw, pitch y roll, cada uno accionado por servomotor. — RDS3218 (yaw) y dos MG996R nuevos (pitch y roll, 05/11).
- [x] ✅ Fijar la cámara a la cabeza, en un ojo o entre ambos a la altura de la nariz. — NoIR montada invertida (`orientation_deg: 180`).
- [x] ✅ Definir y calibrar HOME con la mirada al frente. — ceros en 1500 µs; apagar vuelve a HOME.
- [ ] 🟡 Comprobar recorridos y topes físicos sin colisiones ni cables tensos. — falta verificar el roll a ±20° con los MG996R nuevos.
- [ ] 🟡 Evaluar los rangos sugeridos: yaw ±70°, pitch -20°/+30°, roll ±20°. Son sugeridos; respetar los límites seguros reales. — cargados en `neck.servos`; **signo del roll sin verificar** montado.
- [x] ✅ Implementar límites de posición, velocidad y aceleración por software. — `trajectory.py` y firmware (vmax 180/120/120 °/s, amax 600/400/300 °/s²).
- [ ] 🟡 Conseguir trayectorias suaves, sin golpes ni vibraciones. — los servos vibran moviéndose lento; la mirada por objetivo (el arreglo) está sin probar en real.
- [x] ✅ Implementar comunicación entre procesamiento y microcontrolador, con órdenes de articulaciones, sonido, modo y STOP. La sintaxis del PDF es un ejemplo. — protocolo v1 (`docs/PROTOCOLO.md`), FW_VERSION 2.
- [ ] 🟡 Probar STOP durante movimiento y sonido. — STOP enclavado implementado y con tests; no hay registro de la prueba en real.

### B. Percepción y modelo del mundo - T2 (p. 4)

- [x] ✅ PERSONA: detectar una o varias personas y mantener su ID entre cuadros. — YOLO + `tracker.py`.
- [ ] 🟡 ME_MIRA: estimar cuándo la persona mira al robot y filtrar temporalmente la detección. — casi no se activa; intrínsecos de cámara provisorios (sin tablero).
- [x] ✅ SALUDO: reconocer el gesto de saludo con mano y evitar múltiples eventos por el mismo gesto.
- [x] ✅ CAMISETA_OLIMPIA: reconocer la camiseta desde la región del torso. — 82 % de los cuadros (99 % desde los 10 s).
- [x] ✅ CAMISETA_CERRO: reconocer la camiseta desde la región del torso. — 98 %.
- [ ] 🟡 Rechazar como falsas camisetas de equipo las prendas lisas blancas, rojas o azules. — roja y azul reales: 0 % de falsos positivos; blanca solo sintética.
- [ ] 🟡 SALIENDO: detectar cuando la persona objetivo se aproxima a salir del campo visual o del alcance articular. — implementado, sin probar en real.
- [ ] 🟡 Documentar y probar umbrales y persistencia de todos los eventos. ±15°/0,5 s para ME_MIRA y dos ciclos de mano son ejemplos de la consigna, no valores únicos obligatorios. — en `config.yaml`; falta validar `looking_deg` y escribirlo en el informe.
- [x] ✅ Si se usan imágenes propias, obtener consentimiento antes de almacenarlas; usar integrantes o voluntarios que hayan aceptado. — `capturas/` y `video/` fuera de git; borrar `~/keepon/capturas/camisetas/` en la Pi al cerrar el detector.

### C. Mirada y selección de persona - T3 y T4 (pp. 4 y 5)

- [ ] 🟡 Centrar el rostro objetivo mediante control visual de yaw y pitch. — andaba en real con `gaze.modo: velocidad`; el modo nuevo `objetivo` está sin probar.
- [x] ✅ Incorporar zona muerta, saturación y suavizado. — `deadzone`, `vmax`, `ema` en `gaze`.
- [ ] 🟡 Seguir a una persona en movimiento y mantener mirada estable cuando está quieta. — estable con vibración de los servos; repetir con el modo `objetivo`.
- [x] ✅ Ante pérdida breve del objetivo, menor a 1 s, mantener o predecir la mirada; si persiste, liberar el objetivo. — `lost_hold_s: 1.0`.
- [ ] 🟡 Con varias personas, priorizar a quien mira al robot. — implementado (prioridad estricta de ME_MIRA); depende de ME_MIRA y no hay prueba registrada con varias personas.
- [x] ✅ Si nadie mira al robot, elegir según un criterio documentado. — tamaño y centro (`w_size` 0,6, `w_center` 0,4).
- [x] ✅ Añadir histéresis y tiempo mínimo para evitar saltos constantes de objetivo. — `switch_after_s: 1.5`.
- [x] ✅ Hacer que el árbitro gestione también seguimiento y movimientos de cabeza.

### D. Comportamientos y personalidades - T5 (pp. 5 y 6)

- [ ] 🟡 Observador: explorar suavemente sin personas, con barridos y variaciones pequeñas de mirada/roll. — modo por miradas sin probar en real; **faltan las variaciones de roll**.
- [x] ✅ Seguimiento: mantener la mirada en la persona seleccionada.
- [x] ✅ Saludo: responder con 2 a 3 cabeceos y sonido tipo R2D2. — 3 cabeceos de 12°.
- [x] ✅ Olimpia: silbar un fragmento reconocible de su polca mientras sigue a la persona.
- [x] ✅ Cerro: producir un silbido de reprobación. — abucheo.
- [ ] 🟡 Tímido: al recibir la mirada, apartarla unos segundos y volver gradualmente a espiar. — implementado; en real no desviaba porque ME_MIRA casi no se activa.
- [ ] 🟡 Atrevido: sostener la mirada y elevar periódicamente el mentón, conservando seguimiento en yaw. — implementado; sin prueba en real registrada (depende de ME_MIRA).
- [ ] 🟡 Maleducado: silbido de piropo una vez por salida de la persona objetivo. — implementado, sin probar en real.
- [x] ✅ Cambiar de personalidad durante la ejecución mediante comando. — panel del celular, `scripts/k t|a|m|n`, `MODE <X>`.
- [ ] 🟡 Confirmar cada cambio de modo con sonido breve distintivo. — anda, pero el beep se pierde si suena otro sonido de OPERADOR al mismo tiempo.
- [x] ✅ Recomendado: modo Neutro por defecto. — `modos.inicial: NEUTRO`.
- [ ] 🟡 Opcionales: inclinación de curiosidad al quedar quieto, aburrimiento y desaprobación al perder el objetivo; párpados o LEDs. No desplazar con estos extras las funciones centrales. — curiosidad ✅ en real; aburrimiento y desaprobación ❌ (el sonido DESAPROBACION existe).

La consigna permite personalizar comportamientos, pero presenta la tabla como comportamientos requeridos. Este checklist cubre el conjunto completo; acordar cualquier sustitución con la cátedra.

### E. Arbitraje, reactividad y robustez - T6 (pp. 6 y 7)

- [x] ✅ Un solo dueño del cuello y un solo dueño del buzzer en cada instante. — `arbiter.py`; `actuators.py` descarta al que no es dueño.
- [x] ✅ Permitir coexistencia de comportamientos cuando usan recursos distintos: por ejemplo, polca y seguimiento.
- [x] ✅ Resolver seguimiento y gestos dentro de una única orden coherente al cuello; evitar dos controladores escribiendo simultáneamente. — la curiosidad y los modos van dentro del dueño del cuello.
- [x] ✅ Definir tabla propia de prioridades y reglas de interrupción. La tabla del PDF es un ejemplo. — OPERADOR 0, SALUDO 1, CAMISETA 2, MODO 3, SEGUIMIENTO 4, OBSERVADOR 5.
- [x] ✅ Dar respuesta prioritaria a órdenes del operador, especialmente STOP.
- [x] ✅ No emitir dos sonidos a la vez ni seguir en pitch mientras otro comportamiento intenta asentir de forma contradictoria.
- [x] ✅ Implementar cooldowns por persona y comportamiento, y detección de gesto nuevo. — SALUDO 5 s y CAMISETA 25 s por persona, PIROPO 40 s global.
- [ ] 🟡 Documentar los tiempos elegidos: la polca cada 20 a 30 s y el piropo cada 40 s son ejemplos. — en `config.yaml`; falta en el informe y decidir si la polca se repite cada 25 s.
- [x] ✅ Añadir filtros temporales, histéresis y tiempos mínimos por estado.
- [ ] 🟡 Alcanzar percepción de al menos 10 Hz. — personas 12–17 Hz y lazo 36–39 Hz; la pose va a 7–10 Hz.
- [ ] ❌ Medir latencia desde el evento al inicio de respuesta; referencia orientativa: hasta 300 ms. — solo está medida la edad del cuadro (96–135 ms).
- [x] ✅ Ejecutar movimiento y sonido sin bloquear percepción ni control; evitar esperas bloqueantes.
- [x] ✅ Volver suavemente a seguimiento u observador tras finalizar o interrumpir una acción.
- [ ] 🟡 Ensayar eventos simultáneos: saludo + camiseta, cambio de modo durante sonido y pérdida de persona durante un gesto. — solo en el simulador y en los tests; falta en real.

### F. Monitoreo y ensayo final - T7 (p. 7)

- [x] ✅ Mostrar video con personas e ID, persona objetivo y eventos activos. — overlay en `:8080/stream_viewer?topic=/keepon/overlay`.
- [x] ✅ Mostrar modo actual, comportamiento dueño de cada recurso y ángulos comandados.
- [x] ✅ Guardar transiciones de estado con marca de tiempo. — log CSV.
- [ ] ❌ Preparar secuencia de demo que cubra todas las funciones y conflictos de arbitraje.
- [ ] 🟡 Probar con varias personas, pérdidas breves/prolongadas, camisetas y prendas que puedan causar falsos positivos. — camisetas y lisas roja/azul sí; varias personas y blanca real no.
- [ ] ❌ Preparar iluminación y camisetas: son responsabilidad del grupo. — camisetas sí; iluminación no.
- [ ] 🟡 Ensayar un arranque desde cero y la defensa individual. — arranque por panel o `scripts/k demo-on` listo; ensayo completo y defensa no.

## 3. Qué revisar, conseguir o comprar

**No es una orden de compra ni un inventario confirmado.** Primero marcar lo disponible y probado; comprar o pedir prestado solamente lo faltante. La consigna permite varias tecnologías. No se verificaron precios, stock ni compatibilidad comercial.

### Hardware que cubre el mínimo del TP (pp. 2 y 3)

- [x] ✅ 3 servomotores apropiados para los ejes y cargas del mecanismo, con sus brazos/discos y tornillos de eje compatibles. — RDS3218 + 2 × MG996R montados.
- [x] ✅ 1 microcontrolador para servos y buzzer; comprobar placa, entradas/salidas, temporizadores y firmware. — ESP32-C3, GPIO0/1/4 y buzzer en GPIO5.
- [x] ✅ 1 cámara compatible con el equipo de procesamiento, con cable y montaje solidario a la cabeza. — Camera Module 3 NoIR.
- [x] ✅ 1 buzzer **pasivo**, capaz de variar la frecuencia. No dar por válido un buzzer activo de tono fijo. — MH-FMD; toca la polca y el R2D2.
- [x] ✅ 1 equipo de procesamiento disponible: PC/notebook/Raspberry Pi/otro que logre la percepción requerida. No se exige comprar Raspberry Pi si otra opción cumple. — Pi 5 de 4 GB.
- [ ] 🟡 Alimentación propia adecuada a los componentes y a la demanda de los servos, incluidos cables y adaptadores. Determinar tensión y corriente a partir del hardware real antes de comprar. — anda; revisar el límite de corriente con los dos MG996R y medir ≥ 4,9 V en la Pi.
- [x] ✅ Material o servicio de fabricación para cabeza, cuello, base y ojos: impresión 3D u otra solución admitida.
- [x] ✅ Enlace de comunicación compatible: cable de datos o conexión inalámbrica, según la arquitectura elegida. — USB serie (CH340).

### Integración y montaje: según la solución elegida

- [x] ✅ Tornillos, tuercas, arandelas, insertos, pivotes y casquillos según el plano vigente; comprobar longitudes y cantidades antes de comprar. — v6 R4 armado.
- [ ] 🟡 Cables de alimentación/señal, conectores y distribución de energía adecuados; verificar masa de referencia común cuando corresponda. — GND común; los jumpers del buzzer por el cuello tuvieron falso contacto.
- [x] ✅ Etapa de accionamiento del buzzer y componentes auxiliares si su consumo o tensión lo requieren; confirmar con su ficha técnica. — módulo MH-FMD a 3V3.
- [ ] 🟡 Fijaciones, separadores, bridas y alivios para cables que se mueven con el cuello. — falta precintar el cable del buzzer.
- [x] ✅ Si se usa Raspberry Pi: almacenamiento, alimentación, refrigeración y cable de cámara compatibles, según lo ya disponible.
- [x] ✅ Herramientas disponibles o prestadas: destornilladores/llaves, calibre, multímetro y útiles de conexión/soldadura según el montaje.
- [ ] 🟡 Recomendado: repuestos de tornillos, conectores y cables; no son entregables obligatorios. — si siguen temblando, volver a poner el capacitor de 2200 µF + 100 nF.

### Materiales para probar y demostrar (p. 8)

- [x] ✅ Camiseta de Olimpia y camiseta de Cerro, propias o prestadas.
- [ ] 🟡 Prendas lisas blanca, roja y azul para comprobar falsos positivos; ensayar también otras prendas. — roja y azul sí; falta una blanca real.
- [ ] ❌ Iluminación suficiente y, si hace falta, lámpara disponible.
- [ ] 🟡 Personas para pruebas de seguimiento, miradas, saludo y selección de foco; consentimiento si se almacenan imágenes. — falta probar con 2–3 personas.
- [ ] ❌ Pantalla del equipo de procesamiento para el monitoreo, y equipo/cables necesarios para presentarlo. — el overlay se ve por navegador; falta definir la pantalla de la demo.

### Ajustes a tu diseño existente V6 R4

Esto procede de los archivos locales del diseño, no son exigencias adicionales de la cátedra. Referencias: `diseno_v6/README.md`, `diseno_v6/revision_R4/README.md`, `diseno_v6/revision_R4/config.yaml` y `diseno_v6/MEDICIONES_PENDIENTES.md`. El último contiene antecedentes: contrastar siempre con R4 antes de reutilizar medidas o cantidades.

- [x] ✅ Confirmar que V6 R4 es la versión que se fabricará y revisar si las piezas ya impresas coinciden. — R4 vigente y armada.
- [x] ✅ Inventariar los servos reales mencionados en el proyecto (RDS3218/MG996R), sus ejes y brazos, sin asumir qué unidades ya tienes.
- [x] ✅ Verificar físicamente acoplamiento y tornillo del disco rojo 25T; el diseño nominal no acredita encastre real. — MG996R montados con el disco de 25T.
- [x] ✅ Revisar el pivote M4, casquillo y tornillería/insertos M3 según las interfaces R4; obtener cantidades del montaje definitivo.
- [x] ✅ Confirmar si el módulo de buzzer RLBZ23 real es pasivo y admite frecuencia variable. El nombre y su alojamiento no lo prueban. — el MH-FMD toca melodías.
- [x] ✅ Verificar montaje del buzzer previsto con M3x5 sin atravesar la cara ni dañar el módulo.
- [ ] 🟡 Comprobar cámara, cinta y enchufes reales; verificar holguras durante todo el movimiento. — falta el recorrido completo con el roll a ±20°.
- [x] ✅ Definir material de impresión y validar un cupón de ajustes/insertos antes de imprimir las piezas definitivas. — piezas impresas y armadas; medidas de `MEDICIONES_PENDIENTES.md` antes de reimprimir.
- [ ] 🟡 Probar conjunto físico en HOME y extremos de recorrido: sin choques, pellizcos ni cables tensos. — falta con los MG996R nuevos.

## 4. Orden práctico de trabajo

1. ❌ Confirmar fecha/plazo con la cátedra. ✅ Inventario de componentes, buzzer, alimentación y controladores.
2. 🟡 Cuello montado y HOME, límites y STOP hechos; falta verificar el roll, la suavidad y STOP en movimiento.
3. ✅ Cámara, detección por ID y seguimiento de una persona.
4. 🟡 Eventos restantes: falta que ME_MIRA y SALIENDO anden en real y la prueba con varias personas.
5. 🟡 Árbitro, sonidos, comportamientos y personalidades: faltan Tímido, Atrevido y Maleducado en real.
6. 🟡 Monitoreo y registros listos; falta medir la latencia y ensayar los conflictos en real.
7. ❌ Colab, README, ZIP/repositorio y video; subir y comprobar accesos.
8. ❌ Ensayo completo con todos los integrantes.
