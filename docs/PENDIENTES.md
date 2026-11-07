# Pendientes

Ordenados por prioridad (07/11/2026). Lo terminado se borra y queda en `docs/BITACORA.md`.

## 0. Entrega documentada (08/11)
1. **Informe en Colab** (9 casillas del checklist; material en `docs/HARDWARE.md`, `docs/ARQUITECTURA.md`,
   `config.yaml`, `docs/ESTADO_PI.md`). Faltan de cero: diagramas de estados de los modos, definición operativa de
   cada evento y aportes individuales (los escribe el grupo).
2. **Integrar los PR #3 → #4 → #5 a `main`** (el usuario, o con su autorización explícita): sin eso, `main` es del 26/10.
3. ZIP del código, enlace al repo y verificar que todo abre desde otra cuenta. Decidir si el repo queda público.
4. Video ≤ 3 min con todos los comportamientos. Confirmar con la cátedra la fecha de la demo (`CLAUDE.md` dice 30/10).

## 1. Para que la demo no falle
1. **Probar en el robot la mirada por objetivo y el Observador por miradas** (firmware ya cargado). Mirar: ¿vibran
   menos?, ¿se pasa y vuelve al empezar a seguir (ajustar `gaze.quieto_deg`)?, ¿molestan los saltitos (`umbral_deg`)?
   Si no anda: `gaze.modo: velocidad` y `observer.modo: barrido`. Grabar con el celular apoyado y quieto para medir.
2. **Verificar el signo del roll** con los MG996R nuevos (`scripts/prueba_movimientos.py`: roll + = horario visto desde
   atrás) y que a ±20° no toque. Mirar si la vibración del roll quieto en 0 (al volver de −20°) sigue.
3. Si siguen temblando: volver a poner el **capacitor 2200 µF + 100 nF** en la bornera de los servos y revisar el límite
   de corriente de la fuente (ahora son dos MG996R).
4. **Modo Tímido**: volver a probarlo (no desviaba la mirada porque ME_MIRA casi no se activaba). Con la línea
   ESTADO (`mira mín/mediana`) y el overlay (`angulo N`) decidir si `perception.looking_deg` (15°) alcanza.
5. **Calibrar la cámara** con un tablero (cx, cy, fx, fy, distorsión) y validar `looking_deg` (15°) con 2–3 personas.
6. Beep del modo que se pierde si suena otro sonido de OPERADOR (el árbitro lo toma como el mismo grant): que reemplace.
7. Buzzer: soldar o cambiar los jumpers del cable por el cuello (un falso contacto lo cortaba). Precintar.
8. Probar en real SALIENDO + piropo (Maleducado).

## 2. Lo que falta de la guía
9. **Camisetas** (anda en vivo): grabar una **remera blanca lisa real** (solo hay sintética en los tests) y otras
   prendas de prueba; decidir si la polca se repite cada 25 s con la misma persona (`cooldowns.CAMISETA_por_persona`)
   o suena una vez; con la luz de la demo, volver a correr `pruebas_camisetas/evaluar.py videos`; después, borrar
   `~/keepon/capturas/camisetas/` en la Pi. Barcelona da Cerro: explicarlo en la defensa.
10. Observador: ya va por miradas (05/11); faltan pequeñas variaciones de roll.
11. **Medir la latencia evento → inicio de la respuesta** (≤ 300 ms, T6 e), p. ej. SALUDO → R2D2, para el informe.
12. Opcionales: desaprobación al liberar el objetivo (T3 c; el sonido DESAPROBACION existe), aburrimiento (T3 e).


## 3. Otros
- Diseño v6: medidas de `docs/diseno_v6/MEDICIONES_PENDIENTES.md` antes de reimprimir piezas estructurales; subir
  `docs/diseno_v5/` (lo importa `generar_v6.py`) y compartir `Keepon_V6_R4.zip` por Drive.
- `docs/diagrama_sistema/index.html` sigue en la v4 y con el buzzer en GPIO10 (va en GPIO5); `docs/hoja_de_ruta.html` en la v2;
  el comentario de encendido de `firmware/keepon_fw/keepon_fw.ino` apunta a la v4.
- Herramientas de calibración (`~/keepon/calibracion/` en la Pi): pasarlas a `scripts/` si se van a reusar.
- Reconexión automática de `SerialLink` si se desconecta el USB; autofoco (hoy `AfMode=0`).
- Revisión de Codex (`docs/REVISION_CODEX_ARQ.md`): punto 3 (asociar pose y persona por timestamp; hoy por caja).
- Medir ≥ 4,9 V en los pines de alimentación de la Pi con todo andando.
- Documentos que siguen nombrando al HS-7955TG como pitch: `pruebas_servos/README.md` (planilla: es historia),
  `pruebas_servos/CLAUDE.md`, `firmware/README.md` y el comentario de arranque de `firmware/keepon_fw/keepon_fw.ino`.
- `pruebas_servos/mover_servos.py`: el roll está con signo +1 y centro 1500 (sin verificar); alinearlo con `config.yaml`.
