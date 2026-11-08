# Diagramas editables del informe (draw.io)

Cada figura de `Informe_técnico_v3.ipynb` (antes `_v2`) tiene acá su archivo `.drawio`, con cajas, textos y flechas editables.
Para abrirlos: https://app.diagrams.net → Archivo → Abrir desde → Dispositivo, la aplicación de escritorio de draw.io o
la extensión "Draw.io Integration" de VS Code.

| Archivo | Figura del informe | Sección |
|---|---|---|
| `01_esquema_keepon.drawio` | Esquema de Keepon (portada) | Portada |
| `02_cadena_cinematica.drawio` | Cadena cinemática | 3.1 |
| `03_diagrama_electrico.drawio` | Diagrama eléctrico | 3.2 |
| `04_sesion_serie.drawio` | Ejemplo de sesión Pi ↔ ESP32 | 3.3 |
| `05_cadena_de_control.drawio` | Cadena de control de un eje | 3.3 |
| `06_region_torso.drawio` | Región del torso (camisetas) | 4.1 |
| `07_histeresis_me_mira.drawio` | Histéresis de ME_MIRA | 4.2 |
| `08_arquitectura.drawio` | Arquitectura del software | 5 |
| `09_mirada_por_objetivo.drawio` | Mirada por objetivo | 6.1 |
| `10_estados_modos.drawio` | Diagramas de estados de los modos | 7.3 |
| `11_segmentos_sonido.drawio` | Segmentos de sonido | 7.4 |
| `12_conflicto_arbitro.drawio` | Ejemplo de conflicto en el árbitro | 8.2 |
| `13_…` a `19_…` | Otros diagramas de la guía PDF (sistema completo, línea de tiempo, PWM, perfil trapezoidal, estados del firmware, frecuencias, píxel → ángulo) | — |

La vista CAD del v6 R4 no está acá: es un render de SolidWorks (`docs/diseno_v6/revision_R4/vistas/`).

**Para actualizar una figura del cuaderno después de editarla:** en draw.io, Archivo → Exportar como → PNG (fondo blanco,
zoom 200 %), y en Colab reemplazar la imagen de esa celda (editar la celda de texto y pegar la imagen nueva).

Se generaron automáticamente desde los SVG de la guía (`docs/guia/guia_keepon.html`) con `../fuente/svg_a_drawio.py`.
Al editarlos en draw.io, conviene revisar que los textos no se salgan de sus cajas: el tamaño se estimó al convertir.
