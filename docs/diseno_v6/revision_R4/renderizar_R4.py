"""Vistas CAD de la revisión R4, desde las mallas realmente exportadas."""
from pathlib import Path
import importlib.util,json
R=Path(__file__).parent
sp=importlib.util.spec_from_file_location('vistas_r4',R.parents[1]/'diseno_v3_simple/render_v3.py')
r=importlib.util.module_from_spec(sp);sp.loader.exec_module(r);r.OUT=R/'vistas'
mall=json.loads((R/'mallas_v6.json').read_text(encoding='utf-8'))
fig=r.page('Keepon V6 · revisión R4','Fijación directa del buzzer · Postes Pi de8 mm · Pitch invertido',size=(16,12))
selecciones=[(.04,.51,'Conjunto',lambda m:True,23,35),(.52,.51,'Buzzer: un tornillo y conexiones libres',lambda m:m['name'] in ('06_cara_con_ojos_integrados','Referencia_modulo_buzzer_31_8x12_8x10','Tornillo_M3_buzzer_placa'),18,150),(.04,.10,'Pitch invertido, sin tapa ni sus fijaciones',lambda m:m['name'] in ('03_cuna_de_inclinacion','Referencia_brazo_simple_inclinacion','Referencia_servo_inclinacion_HS7955TG'),15,230),(.52,.10,'Postes de la Pi: altura8 mm',lambda m:m['name'] in ('04_carcasa_inferior_cabeza','Referencia_Raspberry_Pi_5'),35,35)]
for x,y,titulo,filtro,elev,azim in selecciones:
    ax=fig.add_axes([x,y,.43,.32]);r.render(ax,[m for m in mall if filtro(m)],elev=elev,azim=azim,floor=False);fig.text(x+.01,y+.335,titulo,fontsize=14,weight='bold',color=r.INK)
r.save(fig,'01_R4_cambios.png','Cotas del usuario incorporadas al CAD; estriado y diámetro/centro del cilindro del buzzer conservan referencias nominales.')
