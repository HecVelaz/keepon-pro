"""Vistas de revisión R3 obtenidas de la geometría exportada."""
from pathlib import Path
import importlib.util,json
R=Path(__file__).parent
spec=importlib.util.spec_from_file_location('vistas_r3',R.parent/'diseno_v3_simple/render_v3.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r);r.OUT=R/'vistas'
mall=json.loads((R/'mallas_v6.json').read_text(encoding='utf-8'))
fig=r.page('Keepon V6 · revisión R3','Cara y ojos integrados · Montaje trasero · Brazos comerciales actualizados',size=(16,12))
selecciones=[(.04,.51,'Conjunto actualizado',lambda m:True,23,35),(.52,.51,'Cara: una sola pieza con ojos',lambda m:m['name']=='06_cara_con_ojos_integrados',8,10),(.04,.10,'Buzzer: fijación desde atrás',lambda m:m['name'] in ('06_cara_con_ojos_integrados','15_soporte_trasero_modulo_buzzer','Referencia_placa_modulo_buzzer','21_arandela_aislante_buzzer') or m['name'].startswith(('Tornillo_M3_buzzer','Tornillo_M3_soporte_buzzer')),15,155),(.52,.10,'Soporte centrado y agujeros en pilares',lambda m:m['name'] in ('01_base_con_pilares','10_soporte_centrado_servo_base','Referencia_servo_base_RDS3218'),25,120)]
for x,y,titulo,filtro,elev,azim in selecciones:
    ax=fig.add_axes([x,y,.43,.32]);r.render(ax,[m for m in mall if filtro(m)],elev=elev,azim=azim,floor=False)
    fig.text(x+.01,y+.335,titulo,fontsize=14,weight='bold',color=r.INK)
r.save(fig,'07_R3_montaje_integrado.png','Dimensiones nominales verificadas con B-Rep. Falta comprobar encastres, transductor y tornillería reales.')
