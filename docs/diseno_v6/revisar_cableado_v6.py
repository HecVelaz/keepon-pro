"""Condición necesaria de longitud entre anclajes; no simula flexibilidad."""
from pathlib import Path
import json
import math
import itertools
import yaml
import numpy as np

RAIZ=Path(__file__).resolve().parent
cfg=yaml.safe_load((RAIZ/'config.yaml').read_text(encoding='utf-8'))
tr=json.loads((RAIZ/'evidencias/trazabilidad_v6.json').read_text(encoding='utf-8'))
z=tr['z_eje_pitch_roll_mm'];dz=tr['elevacion_conjunto_mm'];c=np.array([0,0,z])


def punto(p,grupo,yaw,pitch,roll):
    p=np.array(p,dtype=float)
    y,pi,r=map(math.radians,(yaw,-pitch,roll))
    rz=np.array([[math.cos(y),-math.sin(y),0],[math.sin(y),math.cos(y),0],[0,0,1]])
    ry=np.array([[math.cos(pi),0,math.sin(pi)],[0,1,0],[-math.sin(pi),0,math.cos(pi)]])
    rx=np.array([[1,0,0],[0,math.cos(r),-math.sin(r)],[0,math.sin(r),math.cos(r)]])
    if grupo=='roll':p=c+rx@(p-c)
    if grupo in ('pitch','roll'):p=c+ry@(p-c)
    if grupo!='fixed':p=rz@p
    return p


filas=[]
poses=list(itertools.product((-70,-35,0,35,70),range(-20,31,5),range(-20,21,5)))
for t in cfg['cableado']['tramos']:
    extremos=[]
    for lado in 'ab':
        p=np.array(t.get('punto_'+lado+'_mm',t.get('punto_'+lado+'_antes_elevacion_mm')),dtype=float)
        if 'punto_'+lado+'_antes_elevacion_mm' in t:p[2]+=dz
        extremos.append(p)
    mayor=(-1,None)
    for pose in poses:
        d=np.linalg.norm(punto(extremos[0],t['grupo_a'],*pose)-punto(extremos[1],t['grupo_b'],*pose))
        if d>mayor[0]:mayor=(float(d),pose)
    margen=t['longitud_libre_inicial_mm']-mayor[0]
    filas.append({'tramo':t['nombre'],'distancia_recta_maxima_mm':mayor[0],'pose':mayor[1],
                  'longitud_libre_inicial_mm':t['longitud_libre_inicial_mm'],'reserva_frente_distancia_recta_mm':margen,
                  'condicion_necesaria_longitud':margen>=cfg['cableado']['margen_longitud_mm']})
informe={'tramos':filas,'poses_por_tramo':len(poses),'flexion_simulada':False,
         'limitacion':'La recta entre extremos no prueba forma, radio de curvatura, rozamiento ni tensión de conectores. Probar cables reales.'}
(RAIZ/'evidencias/cableado_v6.json').write_text(json.dumps(informe,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(informe,ensure_ascii=False))
