# Pendientes

Ordenados por prioridad (08/11/2026). Lo terminado se borra y queda en `docs/BITACORA.md`.

## 0. Entrega documentada (08/11)
1. **Informe** (`docs/informe/`): elegir la versión final (`Informe_técnico.ipynb` o `_v3`, antes `_v2`) y completar los
   `[Completar]`: ninguno (el overlay va como figura generada por `keepon/overlay.py` sobre una escena sintética). ZIP = release `v1.0-entrega`; lo no medido en el
   robot (latencia de punta a punta, error de mirada) quedó indicado como tal (08/11). Subirlo a Colab y probar que abre desde otra cuenta.
2. ~~Integrar los PR a `main`~~: hecho el 08/11 (#3 → #4 → #5 → #6).
   **Pi:** `docs/` se reorganizó el 08/11 (consigna/, hardware/, cad_anteriores/, revisiones/). El `rsync` no borra: en el
   próximo sync, borrar en `~/keepon/docs/` las carpetas viejas (`Fotos`, `diagrama_sistema`, `keepon_v*_cad`,
   `micro_servo_*`, `servo_HS-7955TG_titanium_gear`, `keepon_mg996r_step`, `REVISION_CODEX*.md`, `CHECKLIST_TP.md`,
   `2026S2uTP_*`), comparando antes con `cmp`. El código del robot no cambió; el panel sí (`scripts/panel/index.html`:
   la aclaración del botón Ejes en su línea): después del sync, `systemctl --user restart keepon-panel`.
3. ~~ZIP del código~~ (release `v1.0-entrega`, 08/11). Falta verificar que todo abre desde otra cuenta.
4. ~~Video ≤ 3 min~~: hecho el 08/11, https://youtu.be/raOJljv1mVU (8 pruebas, 3 min), con miniatura en el README y
   reproductor en el informe. Falta confirmar con la cátedra la fecha de la demo (`CLAUDE.md` dice 30/10).
5. ~~Guía PDF al día~~ (08/11): curva S, roll, Observador, HOME/Ejes, polca, figuras y capítulo 19 de preguntas para la defensa.

## 1. Para que la demo no falle
1. **Probar lo del 08/11 en el robot** (todo cargado): el barrido del Observador a 25 °/s (si el yaw vibra en el medio,
   subir `observer.exploracion.vel_barrido` a 30; si solo en las puntas, dar la vuelta más rápido), el botón **Ejes**,
   la polca una vez por aparición y el seguimiento con la curva S (¿se pasa y vuelve? `gaze.quieto_deg`).
2. **Roll**: (a) resultado del roll rápido (250 °/s, 900 °/s², curva S 0,15 s) en −20 → 0 y −20 → +20; (b) si sigue
   vibrando, **prueba de banco** del MG996R sin carga en 1280→1500 µs subiendo (`pruebas_servos/prueba_servo/`) para
   separar servo de carga; girar la cabeza a mano por esa zona buscando un punto duro; (c) medir el cero llegando desde
   la derecha y, si difiere, cargar `compensacion_us`.
3. Si siguen temblando: volver a poner el **capacitor 2200 µF + 100 nF** en la bornera de los servos y revisar el límite
   de corriente de la fuente (ahora son dos MG996R).
4. **ME_MIRA** (escenas de seguimiento y personalidades del video): con **dos personas**, ver si prioriza a quien lo
   mira; volver a probar **Tímido** y **Atrevido** (no desviaba porque ME_MIRA casi no se activaba). Con la línea
   ESTADO (`mira mín/mediana`) y el overlay (`angulo N`) decidir si `perception.looking_deg` (15°) alcanza.
5. **Calibrar la cámara** con un tablero (cx, cy, fx, fy, distorsión) y validar `looking_deg` (15°) con 2–3 personas.
6. Buzzer: soldar o cambiar los jumpers del cable por el cuello (un falso contacto lo cortaba). Precintar.
7. Probar en real SALIENDO + piropo (Maleducado) y STOP durante un sonido.

## 2. Lo que falta de la guía
8. **Camisetas** (anda en vivo): grabar una **remera blanca lisa real** (solo hay sintética en los tests) y otras
   prendas de prueba; con la luz de la demo, volver a correr `pruebas_camisetas/evaluar.py videos`; después, borrar
   `~/keepon/capturas/camisetas/` en la Pi. Barcelona da Cerro: explicarlo en la defensa.
9. **Medir la latencia evento → inicio de la respuesta** (≤ 300 ms, T6 e), p. ej. SALUDO → R2D2, para el informe.
10. Opcionales: desaprobación al liberar el objetivo (T3 c; el sonido DESAPROBACION existe), aburrimiento (T3 e).


## 3. Otros
- Diseño v6: medidas de `docs/diseno_v6/MEDICIONES_PENDIENTES.md` antes de reimprimir piezas estructurales; subir
  `docs/diseno_v5/` (lo importa `generar_v6.py`) y compartir `Keepon_V6_R4.zip` por Drive.
- `docs/hoja_de_ruta.html` sigue en la v2;
  el comentario de encendido de `firmware/keepon_fw/keepon_fw.ino` apunta a la v4.
- Herramientas de calibración (`~/keepon/calibracion/` en la Pi): pasarlas a `scripts/` si se van a reusar.
- Reconexión automática de `SerialLink` si se desconecta el USB; autofoco (hoy `AfMode=0`).
- Revisión de Codex (`docs/revisiones/REVISION_CODEX_ARQ.md`): punto 3 (asociar pose y persona por timestamp; hoy por caja).
- Medir ≥ 4,9 V en los pines de alimentación de la Pi con todo andando.
- Documentos que siguen nombrando al HS-7955TG como pitch: `pruebas_servos/README.md` (planilla: es historia),
  `pruebas_servos/CLAUDE.md`, `firmware/README.md` y el comentario de arranque de `firmware/keepon_fw/keepon_fw.ino`.
- Script de secuencias automáticas de posturas (sin Enter) en `scripts/`: hoy es uno temporal en `/tmp` de la Pi.
