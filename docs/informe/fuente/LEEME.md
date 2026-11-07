# Cómo se genera el informe

`Informe_técnico.ipynb` (la carpeta de arriba) es la plantilla de informe del grupo, completada con el contenido real
del proyecto por `completar_informe.py`. Los diagramas salen de la guía (`docs/guia/guia_keepon.html`):

```bash
# 1. Diagramas de la guía → PNG (necesita cairosvg); quedan en figs/
python extraer_svg.py ../../guia/guia_keepon.html
# 2. Plantilla original + contenido + figuras incrustadas (necesita nbformat y Pillow)
python completar_informe.py plantilla.ipynb figs ../../diseno_v6/revision_R4/vistas/01_R4_cambios.png Informe_técnico.ipynb
# 3. Ejecutar las celdas para guardar las salidas (nbclient, o "Ejecutar todo" en Colab)
```

Las celdas de código clonan el repo público y leen `config.yaml`, los benchmarks y el escenario simulado.
