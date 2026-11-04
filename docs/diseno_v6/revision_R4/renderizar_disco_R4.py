"""Vistas del horn de roll según el croquis del usuario."""
from pathlib import Path
import importlib.util,json
R=Path(__file__).parent
sp=importlib.util.spec_from_file_location('detalle_r4',R.parents[1]/'diseno_v3_simple/render_v3.py')
r=importlib.util.module_from_spec(sp);sp.loader.exec_module(r);r.OUT=R/'vistas'
mall=json.loads((R/'mallas_v6.json').read_text(encoding='utf-8'));disco=[m for m in mall if m['name']=='Referencia_disco_balanceo']
fig=r.page('Disco rojo de roll · 25T','Ø19,8 · Cuatro Ø3 a R7 · 14 mm entre opuestos · Paso central Ø3',size=(14,8))
for x,titulo,elev,azim in [(.03,'Cara del disco',0,0),(.51,'Cubo hacia el servo',20,150)]:
    ax=fig.add_axes([x,.22,.45,.53]);r.render(ax,disco,elev=elev,azim=azim,floor=False);fig.text(x+.02,.78,titulo,fontsize=15,weight='bold',color=r.INK)
fig.text(.06,.15,'Disco: 2,45 mm de espesor. Cubo: Ø9 mm. Altura total: 4,5 mm.',fontsize=14,color=r.INK)
r.save(fig,'02_R4_disco_roll.png','Referencia comercial: el estriado25T no está reconstruido; cavidad nominal y reserva de montaje documentadas en README.')
