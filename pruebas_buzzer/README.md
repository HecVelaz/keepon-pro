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

Transcrita de `notas polca de olimpia/` (14/10): la primera frase, compases 1 a 8 (el mismo motivo vuelve en los
compases 9–16 y 66–74). 6/8, negra con puntillo = 135, Fa mayor: corchea de 148 ms, compás de 888 ms, **7,104 s**
en total (`config.yaml` actualizado). Va **una octava más arriba** que la partitura (659–1397 Hz), porque escrita
(330–698 Hz) cae donde el buzzer suena débil. Cada nota deja 15 ms de silencio para que las repetidas se separen;
el acento del primer tiempo de los cuatrillos no se puede hacer con un buzzer.

## Buzzer

Pasivo electromagnético de 12 mm, 5 V (~16–42 Ω, resonancia ~2–2,7 kHz). Con 5 V continuos tiene que hacer solo
"clic": si pita solo, es activo y no sirve (el enunciado pide uno pasivo modulado en frecuencia). Conexión: 5 V de
la ESP32 → buzzer → colector del 2N2222; GPIO10 → 1 kΩ → base; 10 kΩ base-emisor; 1N4148 en paralelo con el buzzer.
