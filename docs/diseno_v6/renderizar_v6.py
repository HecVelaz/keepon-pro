"""Vistas de la geometría exportada, con referencias separadas de las medidas."""
from pathlib import Path
import importlib.util
import json

RAIZ=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('render_heredado',RAIZ.parent/'diseno_v3_simple/render_v3.py')
r=importlib.util.module_from_spec(sp);sp.loader.exec_module(r)
r.OUT=RAIZ/'vistas'
mall=json.loads((RAIZ/'mallas_v6.json').read_text(encoding='utf-8'))
tr=json.loads((RAIZ/'evidencias/trazabilidad_v6.json').read_text(encoding='utf-8'))
z=tr['z_eje_pitch_roll_mm']
for archivo,titulo,sub,elev,azim,filtro in [
    ('01_V6_isometrica.png','Keepon V6 · integración nominal','Base V5 reutilizada · RDS3218 girado · HS7955TG · MG996R exterior',23,35,lambda m:True),
    ('02_roll_exterior.png','Motor de roll fuera de la cabeza','Cuna pitch y unión desmontable; cuerpo del motor pertenece a pitch',20,145,lambda m:m['group'] in ('pitch','roll') and m['name'] not in ('05_tapa_ventilada','06_cara_binocular')),
    ('03_adaptador_base.png','Adaptador independiente del RDS3218','Mismos puntos nominales de base; giro del cuerpo 90°; comprobar roscas y cable',40,130,lambda m:m['name'] in ('01_base','10_adaptador_yaw','REF_RDS3218') or m['name'].startswith('REF_M3_servo_yaw')),
    ('04_USB_y_portamodulo.png','Cabeza · dos aberturas y PCB RLBZ23','Tapa14 retirada; PCB13x31,8x1,5 medido en bastidor lateral abierto',22,145,lambda m:m['group']=='roll' and not m['name'].startswith('REF_M3_') and m['name']!='05_tapa_ventilada')]:
    fig=r.page(titulo,sub)
    ax=fig.add_axes([.06,.13,.86,.74])
    r.render(ax,[m for m in mall if filtro(m)],elev=elev,azim=azim,floor=False)
    r.save(fig,archivo,'Revisión R2. Alturas/pines RLBZ23, brazos reales, USB, material, insertos y fijaciones de base pendientes de comprobar.')
print('Cuatro vistas V6 generadas.')
