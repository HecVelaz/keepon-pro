"""Transfiere el barrido de envolventes M3x8 a tornillos menores M3x6.

La contención entre sólidos se conserva bajo la misma transformación rígida.
También repite nueve poses y exporta el modelo final, sin falsear el barrido
completo anterior de 495 poses con las envolventes mayores.
"""
from pathlib import Path
import json
import generar_v6 as v
import auditar_v6 as auditor

R=Path(__file__).resolve().parent
anterior=json.loads((R/'evidencias/auditoria_v6.json').read_text(encoding='utf-8'))
piezas=v.construir();filas=[]
for nombre,m,servo in [('yaw',v.MY,v.v2.RDS3218),('pitch',v.HP,v.v2.HS7955),('roll',v.MR,v.v2.MG996R)]:
    xc=servo.L/2-servo.a
    asiento=0 if nombre=='yaw' else -servo.tf
    hacia=-1 if nombre=='yaw' else 1
    for i,(sx,sy) in enumerate(((-1,-1),(-1,1),(1,-1),(1,1))):
        x,y=xc+sx*servo.hs/2,sy*servo.hw/2
        viejo=m(v.cil(1.5,8,(x,y,asiento),(0,0,hacia)).fuse(v.cil(3,3,(x,y,asiento),(0,0,-hacia))))
        n=f'REF_M3_servo_{nombre}_{i}'
        actual=next(p['shape'] for p in piezas if p['name']==n)
        dato=next(p for p in anterior['piezas'] if p['nombre']==n)
        assert abs(viejo.Volume()-dato['volumen_mm3'])<.01
        residuo=actual.cut(viejo).Volume()
        assert residuo<.001
        filas.append({'pieza':n,'largo_anterior':8,'largo_final':6,'volumen_fuera_anterior_mm3':residuo})
assert anterior['aprobado_nominal'] and len(filas)==12
prueba={'tornillos':filas,'contencion_verificada':True,'barrido_conservador_poses':495,
        'razon':'Todo tornillo final está dentro de su envolvente anterior, bajo los mismos giros; no agrega colisiones.',
        'margen_fondo_final_mm':2.1,'enganche_nominal_mm':3.5}
(R/'evidencias/reduccion_tornillos.json').write_text(json.dumps(prueba,indent=2,ensure_ascii=False),encoding='utf-8')
auditor.main(True,True,piezas)
print('Contención de 12 tornillos y barrido rápido final verificados.',flush=True)
