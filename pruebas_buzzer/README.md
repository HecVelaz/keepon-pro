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

## Buzzer y su circuito

| Componente | Cant. | Para qué |
|---|---|---|
| Buzzer **pasivo** 5 V (~16 Ω, ~30 mA) | 1 | El sonido. [electronica.com.py](https://www.electronica.com.py/producto/buzzer-zumbador-5v-pasivo/), ₲10.000. **No** el "activo" de al lado: trae oscilador y hace un solo tono |
| Transistor 2N2222 (o PN2222A) | 1 | Le da al buzzer la corriente que el GPIO no puede dar |
| Resistencia 1 kΩ | 1 | Entre el GPIO10 y la base |
| Resistencia 10 kΩ | 1 | Entre base y emisor: el transistor queda apagado mientras la ESP32 arranca |
| Diodo 1N4148 (o 1N400x) | 1 | En paralelo con el buzzer: absorbe el pico de la bobina al cortar |

```
5 V (ESP32) ──┬──────────── + buzzer
              │                │
   1N4148 cátodo (raya)        │
   1N4148 ánodo ───────────────┴── − buzzer ── colector 2N2222
                                               base ── 1 kΩ ── GPIO10
                                               base ── 10 kΩ ── GND
                                               emisor ── GND
```

- **Probar el buzzer antes de montarlo:** con 5 V continuos tiene que hacer solo "clic". Si pita solo, es activo y no
  sirve (el enunciado pide uno pasivo modulado en frecuencia).
- **Diodo:** la raya (cátodo) va hacia los 5 V. Al derecho hace cortocircuito a través del transistor.
- **Patas del transistor:** el 2N2222A y el PN2222A en TO-92 vienen con las patas en orden distinto (E-B-C o C-B-E,
  según el fabricante). Mirar la hoja del que compren o medirlo con el multímetro en modo diodo.
- El esquema está también en `docs/diagrama_sistema/index.html` ("Circuito del buzzer").
