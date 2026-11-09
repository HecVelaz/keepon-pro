# Pendientes

Ordenados por prioridad (08/11/2026, noche). Lo terminado se borra y queda en `docs/BITACORA.md`.

## 0. Entrega (hoy, domingo 08/11)
1. **Subir `docs/informe/Informe_técnico_v3.ipynb` al Colab del Drive** (reemplazar la copia vieja), compartirlo con
   «cualquier persona con el enlace» y probar que abre desde otra cuenta o ventana privada.
2. **Aula virtual**: enlace al Colab (o el `.ipynb`), el ZIP (`~/Documentos/Entrega_Wall-E/keepon-pro-v1.0-entrega.zip`),
   el enlace al repo, el enlace al video y, opcional, `docs/diseno_v6/Keepon_V6_R4.zip` (SolidWorks, fuera de git).
3. Confirmar con la cátedra la fecha de la demo (el usuario dice martes; `CLAUDE.md` todavía dice 30/10).

## 1. Para la demo del martes
1. **Sincronizar la Pi** (`/verificar` y `/pi-sync-keepon`): lleva el arreglo del panel (botón Ejes) → después
   `systemctl --user restart keepon-panel`. Borrar en `~/keepon/docs/` las carpetas viejas de la reorganización (`Fotos`,
   `diagrama_sistema`, `keepon_v*_cad`, `micro_servo_*`, `servo_HS-7955TG_titanium_gear`, `keepon_mg996r_step`,
   `REVISION_CODEX*.md`, `CHECKLIST_TP.md`, `2026S2uTP_*`), comparando antes con `cmp`.
2. **Ensayar la secuencia de las 8 pruebas del video** con la luz y las camisetas de la demo, con 2–3 personas.
3. **Defensa**: los cuatro integrantes estudian con la guía (`docs/guia/Guia_Keepon_pro.pdf`, sobre todo el capítulo 19).
4. Roll: si la vibración molesta, prueba de banco del MG996R sin carga (1280→1500 µs subiendo) para separar servo de
   carga; medir el cero llegando desde la derecha (`compensacion_us`). Si los servos tiemblan en giros rápidos, volver a
   poner el capacitor 2200 µF + 100 nF en la bornera.
5. Buzzer: soldar o precintar los jumpers del cable por el cuello (un falso contacto lo cortaba).

## 2. Mejoras que quedaron (no bloquean la entrega)
6. **Calibrar la cámara** con un tablero y validar el umbral de ME_MIRA (15°) con 2–3 personas.
7. **Medir la latencia evento → inicio de la respuesta** (SALUDO → R2D2 con el log); hoy es una estimación.
8. Camisetas: grabar una remera blanca lisa real; después borrar `~/keepon/capturas/camisetas/` en la Pi. Barcelona da
   Cerro: explicarlo en la defensa.
9. Título de la app del panel: dice «Keepon»; cambiar a «Wall-E» si el grupo quiere (y volver a sacar la captura con
   `scripts/captura_panel.py`).
10. Opcionales de la consigna: desaprobación al liberar el objetivo (T3 c), aburrimiento (T3 e).

## 3. Otros
- Diseño v6: medidas de `docs/diseno_v6/MEDICIONES_PENDIENTES.md` antes de reimprimir; subir `docs/diseno_v5/` (lo
  importa `generar_v6.py`).
- `docs/hoja_de_ruta.html` sigue en la v2; documentos que todavía nombran al HS-7955TG como pitch:
  `pruebas_servos/CLAUDE.md`, `firmware/README.md` y el comentario de arranque de `firmware/keepon_fw/keepon_fw.ino`.
- `CLAUDE.md`: el número de tests (164) y la fecha de la demo están desactualizados (no son reglas: actualizar si se toca).
- Herramientas de calibración (`~/keepon/calibracion/` en la Pi) y el script de secuencias de posturas (hoy en `/tmp` de
  la Pi): pasarlos a `scripts/` si se van a reusar.
- Reconexión automática de `SerialLink`; autofoco (hoy `AfMode=0`); asociar pose y persona por timestamp
  (`docs/revisiones/REVISION_CODEX_ARQ.md`, punto 3); medir ≥ 4,9 V en los pines de la Pi con todo andando.
