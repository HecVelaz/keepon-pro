"""Reimporta STEP y comprueba las mallas entregadas, sin certificar fabricación."""
from pathlib import Path
from collections import Counter
import json
import math
import struct
import cadquery as cq

RAIZ=Path(__file__).resolve().parent


def revisar_stl(ruta):
    datos=ruta.read_bytes();n=struct.unpack_from('<I',datos,80)[0]
    if len(datos)!=84+50*n:raise ValueError('STL truncado: '+ruta.name)
    aristas=Counter();vol=0.;degenerados=0;minz=float('inf')
    for i in range(n):
        f=struct.unpack_from('<12fH',datos,84+50*i)
        vs=[tuple(round(a,5) for a in f[j:j+3]) for j in (3,6,9)]
        a,b,c=vs
        ab=[b[j]-a[j] for j in range(3)];ac=[c[j]-a[j] for j in range(3)]
        cruz=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
        if sum(v*v for v in cruz)<1e-16:degenerados+=1
        vol+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
        minz=min(minz,*[v[2] for v in vs])
        for j,k in ((0,1),(1,2),(2,0)):aristas[tuple(sorted((vs[j],vs[k])))]+=1
    return {'triangulos':n,'aristas_dos_incidencias':all(v==2 for v in aristas.values()),
            'degenerados':degenerados,'volumen_orientado_mm3':vol,'min_z_mm':minz,
            'limite':'No prueba autointersecciones ni resistencia.'}


def main():
    inventario=json.loads((RAIZ/'inventario_v6.json').read_text(encoding='utf-8'))
    resultado=[]
    for p in inventario:
        nombre=p['nombre'];step=cq.importers.importStep(str(RAIZ/'STEP_V6'/(nombre+'.step'))).val()
        stl=revisar_stl(RAIZ/'STL_REVISION_NO_IMPRIMIR'/(nombre+'.stl'))
        error=abs(step.Volume()/p['volumen_mm3']-1)
        fila={'nombre':nombre,'step_valido':step.isValid(),'solidos':len(step.Solids()),
              'error_volumen_relativo':error,'cabe_en_215_mm':max(p['caja_impresion_mm'][:2])<=215.01,'stl':stl}
        fila['aprobado_archivo']=(fila['step_valido'] and fila['solidos']==1 and error<1e-5 and
            fila['cabe_en_215_mm'] and stl['aristas_dos_incidencias'] and stl['degenerados']==0 and
            stl['volumen_orientado_mm3']>0 and abs(stl['min_z_mm'])<.001)
        resultado.append(fila);print(nombre,fila['aprobado_archivo'],flush=True)
    (RAIZ/'evidencias/archivos_v6.json').write_text(json.dumps({'piezas':resultado,
        'aprobado_archivos':all(p['aprobado_archivo'] for p in resultado),'fabricacion_liberada':False},indent=2,ensure_ascii=False),encoding='utf-8')


if __name__=='__main__':main()
