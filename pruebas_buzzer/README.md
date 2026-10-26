# Pruebas del buzzer

`simulador_sonidos.html` se abre en el navegador (también publicado como artefacto privado:
https://claude.ai/artifact/7wyNPrzj6QqcPJQvrpaPwB). Sirve para escuchar y ajustar los sonidos antes de pasarlos al firmware.

- Cada sonido es una tabla de segmentos `{f_inicio, f_fin, ms}`: nota fija si `f_inicio == f_fin`, barrido lineal si
  son distintas, silencio si es 0. Es el formato que va a usar el firmware de la ESP32 (`ledcWriteTone()` en el GPIO10,
  actualizando los barridos cada 5 ms, sin `delay()`).
- Los sonidos son los de `sounds:` en `config.yaml`. El simulador avisa si la duración de una tabla no coincide.
- Abajo genera las tablas en C para el firmware y las duraciones para `config.yaml`.
- Las tablas editadas quedan guardadas solo en ese navegador. Para que el grupo las tenga, hay que copiarlas al
  simulador (constante `SONIDOS`) y commitear.

## Pendiente

- **POLCA_CERRO** (Club Cerro Porteño, Paraguay) es un **marcador**: falta la partitura. Hay que transcribir un
  fragmento reconocible (8–16 compases) nota por nota, con el formato `G5 230 ; - 20`.
- POLCA_CERRO es un extra: según la Tabla 1 del enunciado, ante la camiseta de Cerro el robot hace el **ABUCHEO**.

## POLCA (Club Olimpia, Paraguay)

Transcrita de `notas_polca_de_olimpia/` (14/10): la primera frase, compases 1 a 8 (el mismo motivo vuelve en los
compases 9–16 y 66–74). 6/8, negra con puntillo = 135, Fa mayor: corchea de 148 ms, compás de 888 ms, **7,104 s**
en total (`config.yaml` actualizado). Va **una octava más arriba** que la partitura (659–1397 Hz), porque escrita
(330–698 Hz) cae donde el buzzer suena débil. Cada nota deja 15 ms de silencio para que las repetidas se separen;
el acento del primer tiempo de los cuatrillos no se puede hacer con un buzzer.

## Módulo del buzzer

Desde el 26/10 se usa un **módulo de buzzer pasivo MH-FMD** (foto en `docs/Fotos/modulo_buzzer_pasivo/`). Trae el
transistor (PNP) y la resistencia de base: el circuito anterior con el 2N2222, el 1 kΩ, el 10 kΩ y el 1N4148 ya no
hace falta.

| Pin del módulo | ESP32-C3 |
|---|---|
| VCC | **3V3** (no 5V) |
| I/O | GPIO10 |
| GND | GND |

- **VCC a 3V3, no a 5V:** el PNP se apaga solo cuando el I/O llega a la tensión de VCC. Con VCC a 5 V, el ALTO de
  3,3 V del GPIO no lo apaga y el buzzer queda con corriente todo el tiempo. A 3,3 V suena algo más bajo.
- **Se activa por nivel bajo** (低电平触发, impreso en la placa). El firmware invierte la salida del GPIO10
  (`ledcOutputInvert`): callado = pin en ALTO, sin corriente en la bobina. Las notas (onda cuadrada al 50 %) suenan
  igual.
- **Probarlo antes de montarlo:** con el I/O a GND fijo tiene que hacer solo "clic". Si pita solo, es activo y no
  sirve (el enunciado pide uno pasivo modulado en frecuencia).
- **Volumen:** `buzzer.volumen` en `config.yaml` (1.0 = ciclo de trabajo del 50 %, el máximo). El 26/10 se bajó a
  0.25 (12,5 %). La sensación de volumen no es lineal con el ciclo de trabajo: ajustar de oído y volver a generar el
  firmware (`scripts/generar_firmware.py`).
- **Prueba de banco:** `prueba_buzzer/prueba_buzzer.ino` alterna un tono hecho con `digitalWrite` (prueba solo el
  hardware) y el mismo tono por LEDC invertido (el camino del firmware). El 26/10 no sonaba ninguno de los dos: era
  un **falso contacto en el pin 10**.
- El conexionado está también en `docs/diagrama_sistema/index.html` ("Módulo del buzzer").
