# Pendientes

Ordenados por prioridad (03/11/2026). Lo terminado se borra y queda en `docs/BITACORA.md`.

## 1. Para que la demo no falle
1. **Buzzer que se corta con los servos en movimiento.** Probar moviendo el cable con la mano con el robot quieto:
   si se corta, es mecánico (conectores Dupont, cable por el cuello: soldar o cambiar, precintar, bucle flojo). Si no,
   eléctrico: 100 nF + 10 µF en el módulo, volver a poner el 2200 µF en la bornera de 6 V, GND de servos en estrella.
2. **Pitch**: juego del brazo simple en su bolsillo (oscila al empujarlo). Calzarlo, volver a poner una retención o un
   horn redondo; o el servo nuevo. Después, ajustar `gaze.kp` (el seguimiento oscila un poco).
3. **Calibrar la cámara** con un tablero (cx, cy, fx, fy, distorsión) y validar `looking_deg` (15°) con 2–3 personas.
4. Beep del modo que se pierde si suena otro sonido de OPERADOR (el árbitro lo toma como el mismo grant): que reemplace.
5. Probar en real SALIENDO + piropo (Maleducado); confirmar que el roll a −20° (1818 µs con compensación) no toca.

## 2. Lo que falta de la guía
6. **Camisetas**: detector hecho (`keepon/camiseta.py`, resultados en `pruebas_camisetas/README.md`). Falta:
   probarlo en vivo con el robot; grabar una **remera blanca lisa real** (solo hay sintética en los tests);
   decidir si de cerca (< 1,5 m, la cara centrada tapa el torso) se apunta más abajo o se pide distancia.
7. Observador: **sacadas** a puntos de interés y pequeñas variaciones de roll (el roll, mejor con el servo nuevo).
8. **Medir la latencia evento → inicio de la respuesta** (≤ 300 ms, T6 e), p. ej. SALUDO → R2D2, para el informe.
9. Opcionales: desaprobación al liberar el objetivo (T3 c; el sonido DESAPROBACION existe), aburrimiento (T3 e).

## 3. Entregables (domingo después del parcial)
10. Informe en Colab: mecanismo y electrónica, modelos de IA (con fuente), definición operativa de cada evento,
    arquitectura, tabla de prioridades, diagramas de estado de los modos, parámetros y resultados medidos.
11. README de instalación y ejecución para el evaluador. Video ≤ 3 min con todos los comportamientos. Código en .zip.
12. Integrar el PR #3 (`diseno-v6-vigente`) a `main`.

## 4. Otros
- Diseño v6: medidas de `docs/diseno_v6/MEDICIONES_PENDIENTES.md` antes de reimprimir piezas estructurales; subir
  `docs/diseno_v5/` (lo importa `generar_v6.py`) y compartir `Keepon_V6_R4.zip` por Drive.
- `docs/diagrama_sistema/index.html` sigue en la v4 y con el buzzer en GPIO10; `docs/hoja_de_ruta.html` en la v2;
  el comentario de encendido de `firmware/keepon_fw/keepon_fw.ino` apunta a la v4.
- Herramientas de calibración (`~/keepon/calibracion/` en la Pi): pasarlas a `scripts/` si se van a reusar.
- Reconexión automática de `SerialLink` si se desconecta el USB; autofoco (hoy `AfMode=0`).
- Revisión de Codex (`docs/REVISION_CODEX_ARQ.md`): punto 3 (asociar pose y persona por timestamp; hoy por caja).
- Medir ≥ 4,9 V en los pines de alimentación de la Pi con todo andando.
- Cuando se cambie un servo: recalibrar su cero, signo y límites (`scripts/prueba_movimientos.py`).
