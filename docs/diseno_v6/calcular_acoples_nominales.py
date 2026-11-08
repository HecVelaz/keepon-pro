"""Cuantifica sólo el contacto nominal eje/horn, cuyo estriado no se modela."""
from pathlib import Path
import json
import generar_v6 as v

simple=v.k3.brazo_modelo(v.v2.HS7955)
perfil=v.perfil_brazo(v.k3.BRAZO_T,v.v2.HS7955.S+1-v.k3.BRAZO_T,0,True)
simple=(perfil.fuse(v.cil(4.5,10,(0,0,7))) if v.CFG['pitch'].get('perfil_brazo_simple_local_xy_mm')
        else simple.intersect(perfil.fuse(v.cil(4.5,10,(0,0,7)))))
datos=[]
for nombre,m,s,h,grupos in [
    ('yaw',v.MY,v.v2.RDS3218,v.HY(v.k3.brazo_modelo(v.v2.RDS3218)),['fixed','yaw']),
    ('pitch',v.HP,v.v2.HS7955,v.HP(simple),['yaw','pitch']),
    ('roll',v.MR,v.v2.MG996R,v.MR(v.k3.brazo_modelo(v.v2.MG996R)),['pitch','roll'])]:
    volumen=m(v.v2.servo_modelo(s)).intersect(h).Volume()
    datos.append({'eje':nombre,'grupos':grupos,'volumen_mm3':volumen})
(v.RAIZ/'evidencias/acoples_nominales.json').write_text(json.dumps(datos,indent=2),encoding='utf-8')
print(datos)
