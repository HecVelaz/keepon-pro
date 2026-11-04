"""Verificaciones geométricas y barrido B-Rep de la V6 nominal, sin FEA."""
import argparse
import itertools
import json
import time
import hashlib
from pathlib import Path
import generar_v6 as v6

RAIZ=Path(__file__).resolve().parent
IGNORAR={frozenset(p) for p in [
    ('REF_RDS3218','REF_horn_yaw'),('REF_HS7955TG','ESTUDIO_horn_pitch_simple_NO_MEDIDO'),
    ('REF_MG996R_exterior','REF_horn_roll'),('REF_pivote_M4','02_horquilla_yaw'),
    ('REF_Pi5','REF_Active_Cooler_reserva')]}


def interseccion(a,b):
    aa,bb=a.BoundingBox(),b.BoundingBox()
    if any(getattr(aa,e+'max')<=getattr(bb,e+'min')+1e-6 or
           getattr(bb,e+'max')<=getattr(aa,e+'min')+1e-6 for e in 'xyz'): return 0.
    return max(0.,a.intersect(b).Volume())


def main(rapido=False,exportar=False,piezas=None):
    inicio=time.monotonic()
    if piezas is None:piezas=v6.construir()
    informe={'revision':v6.CFG.get('revision','inicial'),
             'sha256_config':hashlib.sha256((RAIZ/'config.yaml').read_bytes()).hexdigest(),
             'base_modificada':True,'fabricacion_liberada':False,'piezas':[],
             'interferencias_home':[],'poses':[],'excepciones':[sorted(p) for p in IGNORAR]}
    for p in piezas:
        s=p['shape'];bb=s.BoundingBox()
        informe['piezas'].append({'nombre':p['name'],'valida':s.isValid(),'solidos':len(s.Solids()),
                                 'volumen_mm3':s.Volume(),'caja_mm':[bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax]})
    tol=v6.CFG['validacion']['volumen_interferencia_mm3']
    for a,b in itertools.combinations(piezas,2):
        if frozenset((a['name'],b['name'])) in IGNORAR:continue
        v=interseccion(a['shape'],b['shape'])
        if v>tol:
            informe['interferencias_home'].append({'a':a['name'],'b':b['name'],'volumen_mm3':round(v,4)})
            print('HOME COLISION',a['name'],b['name'],round(v,3),flush=True)
    print('HOME',len(informe['interferencias_home']),'interferencias',flush=True)
    # No multiplicar el trabajo por yaw entre piezas que comparten ese giro.
    pit=(-20,0,30) if rapido else range(-20,31,5)
    rol=(-20,0,20) if rapido else range(-20,21,5)
    fijas=[p for p in piezas if p['group']=='fixed']
    moviles=[p for p in piezas if p['group']!='fixed']
    for pitch,roll in itertools.product(pit,rol):
        actuales=[(p,v6.transformar(p['shape'],0,pitch,roll,p['group'])) for p in moviles]
        choques=[]
        for (a,sa),(b,sb) in itertools.combinations(actuales,2):
            if a['group']==b['group'] or frozenset((a['name'],b['name'])) in IGNORAR:continue
            v=interseccion(sa,sb)
            if v>tol:choques.append({'a':a['name'],'b':b['name'],'volumen_mm3':round(v,4)})
        for yaw in v6.CFG['validacion']['yaw_muestras_grados']:
            for a,sa in actuales:
                girada=sa.rotate((0,0,0),(0,0,1),yaw)
                for b in fijas:
                    if frozenset((a['name'],b['name'])) in IGNORAR:continue
                    v=interseccion(girada,b['shape'])
                    if v>tol:choques.append({'a':a['name'],'b':b['name'],'yaw':yaw,'volumen_mm3':round(v,4)})
        informe['poses'].append({'pitch':pitch,'roll':roll,'interferencias':choques})
        print('POSE',pitch,roll,'COLISIONES',len(choques),flush=True)
    informe['segundos']=round(time.monotonic()-inicio,2)
    informe['poses_representadas']=len(informe['poses'])*len(v6.CFG['validacion']['yaw_muestras_grados'])
    informe['aprobado_nominal']=(not informe['interferencias_home'] and
        all(p['valida'] for p in informe['piezas']) and
        not any(p['interferencias'] for p in informe['poses']))
    informe['limites']=['Muestreo discreto','Largos de brazos y perfil simple seg?n usuario; cubos/estriados y ancho/espesor doble pendientes',
        'Cabezas M3 en envolvente configurable; roscas e insertos no modelados',
        'Módulo RLBZ23 y conectores USB reales ausentes','Sin resistencia ni cable flexible simulado']
    nombre='auditoria_v6_rapida.json' if rapido else 'auditoria_v6.json'
    (RAIZ/'evidencias'/nombre).write_text(json.dumps(informe,indent=2,ensure_ascii=False),encoding='utf-8')
    if exportar:v6.exportar(piezas)
    print('APROBADO NOMINAL:',informe['aprobado_nominal'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--rapido',action='store_true');p.add_argument('--exportar',action='store_true')
    a=p.parse_args();main(a.rapido,a.exportar)
