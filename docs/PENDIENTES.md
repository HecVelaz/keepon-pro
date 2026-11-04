# Pendientes

Ordenados por prioridad (04/11/2026). Lo terminado se borra y queda en `docs/BITACORA.md`.

## 1. Para que la demo no falle
1. **Modo Tímido**: volver a probarlo (no desviaba la mirada porque ME_MIRA casi no se activaba). Con la línea
   ESTADO (`mira mín/mediana`) y el overlay (`angulo N`) decidir si `perception.looking_deg` (15°) alcanza.
2. **Integrar los PR en orden**: #3 → #4 → #5 (cada uno tiene de base el anterior).
3. **Pitch**: juego del brazo simple en su bolsillo (oscila al empujarlo). Calzarlo, volver a poner una retención o un
   horn redondo; o el servo nuevo. Después, ajustar `gaze.kp` (el seguimiento oscila un poco).
4. **Calibrar la cámara** con un tablero (cx, cy, fx, fy, distorsión) y validar `looking_deg` (15°) con 2–3 personas.
5. Beep del modo que se pierde si suena otro sonido de OPERADOR (el árbitro lo toma como el mismo grant): que reemplace.
6. Buzzer: soldar o cambiar los jumpers del cable por el cuello (un falso contacto lo cortaba). Precintar.
7. Probar en real SALIENDO + piropo (Maleducado); confirmar que el roll a −20° (1818 µs con compensación) no toca.

## 2. Lo que falta de la guía
8. **Camisetas** (anda en vivo): grabar una **remera blanca lisa real** (solo hay sintética en los tests) y otras
   prendas de prueba; decidir si la polca se repite cada 25 s con la misma persona (`cooldowns.CAMISETA_por_persona`)
   o suena una vez; con la luz de la demo, volver a correr `pruebas_camisetas/evaluar.py videos`; después, borrar
   `~/keepon/capturas/camisetas/` en la Pi. Barcelona da Cerro: explicarlo en la defensa.
9. Observador: **sacadas** a puntos de interés y pequeñas variaciones de roll (el roll, mejor con el servo nuevo).
10. **Medir la latencia evento → inicio de la respuesta** (≤ 300 ms, T6 e), p. ej. SALUDO → R2D2, para el informe.
11. Opcionales: desaprobación al liberar el objetivo (T3 c; el sonido DESAPROBACION existe), aburrimiento (T3 e).

## 3. Entregables (domingo después del parcial)
12. Informe en Colab: mecanismo y electrónica, modelos de IA (con fuente), definición operativa de cada evento,
    arquitectura, tabla de prioridades, diagramas de estado de los modos, parámetros y resultados medidos.
13. README de instalación y ejecución para el evaluador. Video ≤ 3 min con todos los comportamientos. Código en .zip.

## 4. Otros
- Diseño v6: medidas de `docs/diseno_v6/MEDICIONES_PENDIENTES.md` antes de reimprimir piezas estructurales; subir
  `docs/diseno_v5/` (lo importa `generar_v6.py`) y compartir `Keepon_V6_R4.zip` por Drive.
- `docs/diagrama_sistema/index.html` sigue en la v4 y con el buzzer en GPIO10 (va en GPIO5); `docs/hoja_de_ruta.html` en la v2;
  el comentario de encendido de `firmware/keepon_fw/keepon_fw.ino` apunta a la v4.
- Herramientas de calibración (`~/keepon/calibracion/` en la Pi): pasarlas a `scripts/` si se van a reusar.
- Reconexión automática de `SerialLink` si se desconecta el USB; autofoco (hoy `AfMode=0`).
- Revisión de Codex (`docs/REVISION_CODEX_ARQ.md`): punto 3 (asociar pose y persona por timestamp; hoy por caja).
- Medir ≥ 4,9 V en los pines de alimentación de la Pi con todo andando.
- Cuando se cambie un servo: recalibrar su cero, signo y límites (`scripts/prueba_movimientos.py`).
