# Cómo se genera el informe

`Informe_Keepon_pro.ipynb` (la carpeta de arriba) se arma con estos dos scripts, a partir de la guía
(`docs/guia/guia_keepon.html`):

```bash
# 1. Diagramas de la guía → PNG (necesita cairosvg)
python extraer_svg.py ../../guia/guia_keepon.html          # deja los PNG en figs/
# 2. Cuaderno con las figuras incrustadas (necesita nbformat y Pillow)
python armar_informe.py figs ../../diseno_v6/revision_R4/vistas/01_R4_cambios.png Informe_Keepon_pro.ipynb
# 3. Ejecutar las celdas para que las salidas queden guardadas (nbclient, o "Ejecutar todo" en Colab)
```

Las celdas de código clonan el repo público y leen `config.yaml`, los benchmarks y el escenario simulado.
