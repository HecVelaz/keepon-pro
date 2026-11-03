"""Comprobar cierres y orientación de los STL binarios realmente exportados."""
from pathlib import Path
from collections import Counter
import struct,json
R=Path(__file__).parent
salida=[]
for p in sorted((R/'STL_REVISION_NO_IMPRIMIR').glob('*.stl')):
    datos=p.read_bytes();n=struct.unpack_from('<I',datos,80)[0];assert len(datos)==84+50*n
    aristas=Counter();volumen=0.;minz=float('inf')
    for i in range(n):
        a=struct.unpack_from('<12fH',datos,84+50*i);v=[tuple(round(x,5) for x in a[j:j+3]) for j in (3,6,9)]
        minz=min(minz,*(x[2] for x in v))
        for j in range(3):aristas[tuple(sorted((v[j],v[(j+1)%3])))]+=1
        x,y,z=v
        volumen+=(x[0]*(y[1]*z[2]-y[2]*z[1])+x[1]*(y[2]*z[0]-y[0]*z[2])+x[2]*(y[0]*z[1]-y[1]*z[0]))/6
    problema=sum(c!=2 for c in aristas.values());assert not problema,(p.name,problema)
    assert volumen>0 and abs(minz)<1e-4,(p.name,volumen,minz)
    salida.append({'archivo':p.name,'triangulos':n,'aristas_no_manifold':problema,'volumen_orientado_mm3':volumen,'z_minimo_mm':minz})
(R/'evidencias/mallas_R4.json').write_text(json.dumps(salida,indent=2),encoding='utf-8')
print(len(salida),'STL cerrados, orientados hacia afuera y apoyados en Z=0')
