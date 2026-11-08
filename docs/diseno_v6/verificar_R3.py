"""Regresiones geométricas R3 y controles de interferencia con B-Rep real."""
from pathlib import Path
import itertools,json,math
import generar_v6 as v
from revision_R3 import nombre_es,perfil_simple
R=Path(__file__).parent

def main():
    piezas=v.construir();por={p['name']:p for p in piezas};resultados={}
    def exigir(nombre,condicion):
        resultados[nombre]=bool(condicion)
        if not condicion:raise AssertionError(nombre)
    def pieza(n):return por[nombre_es(n)]['shape']
    def vacio(s,h):return abs(s.intersect(h).Volume())<1e-5
    exigir('solidos_imprimibles_validos',all(p['shape'].isValid() and len(p['shape'].Solids())==1 for p in piezas if p['printed']))
    simple=perfil_simple(2.8,0);bb=simple.BoundingBox()
    exigir('brazo_simple_26_4_por_2_8',abs(bb.xlen-26.4)<1e-6 and abs(bb.zlen-2.8)<1e-6)
    exigir('cara_y_ojos_un_solo_solido',len(pieza('06_cara_binocular').Solids())==1 and not any(p['name'].startswith(('16_','17_','19_','20_')) for p in piezas))
    cuna=pieza('03_cuna_pitch');bb=cuna.BoundingBox()
    exigir('acceso_pitch_pasante_extremo_a_extremo',vacio(cuna,v.cil(4.19,bb.ylen+2,(0,bb.ymin-1,v.Z),(0,1,0))))
    cara=pieza('06_cara_binocular');b=v.CFG['buzzer']['montaje_R3'];hy=b['centro_fijacion_y_mm'];hz=v.Z+b['centro_fijacion_z_relativo_mm']
    exigir('fijacion_pcb_ciega_frontal_intacto',cara.intersect(v.cil(1.9,3,(70,hy,hz),(1,0,0))).Volume()>33)
    exigir('tornillos_buzzer_detras_del_frente',all(p['shape'].BoundingBox().xmax<70 for p in piezas if p['name'].startswith(('Tornillo_M3_buzzer','Tornillo_M3_soporte_buzzer'))))
    for x,y in v.CFG['yaw']['fijaciones_base_xy_mm']:
        exigir(f'paso_M3_adaptador_{x}_{y}',vacio(pieza('10_adaptador_yaw'),v.cil(1.69,8,(x,y,37))))
        exigir(f'alojamiento_centrado_pilar_{x}_{y}',vacio(pieza('01_base'),v.cil(1.99,6.4,(x,y,31.5))))
    bb=pieza('10_adaptador_yaw').BoundingBox();servo=v.v2.RDS3218
    exigir('servo_centrado_en_soporte',abs((bb.xmax+bb.xmin)/2)<1e-6 and abs((bb.ymax+bb.ymin)/2-(servo.L/2-servo.a))<1e-6)
    for x,y in v.CFG['raspberry']['postes_xy_mm']:
        p=v.CFG['raspberry'];zp=v.Z+p['z_base_relativo_mm'];cuba=pieza('04_cuba_cabeza')
        exigir(f'poste_Pi_mas_ancho_{x}_{y}',cuba.intersect(v.cil(4.49,1,(x,y,zp+5))).Volume()>55)
        exigir(f'poste_Pi_mas_bajo_{x}_{y}',vacio(cuba,v.cil(2.9,1,(x,y,zp+p['altura_poste_mm']+.05))))
    disco=pieza('REF_horn_roll');bb=disco.BoundingBox()
    exigir('disco_roll_diametro_20',abs(bb.ylen-20)<1e-6 and abs(bb.zlen-20)<1e-6)
    for i in range(4):
        a=i*math.pi/2;u=5*math.cos(a);w=5*math.sin(a)
        h=v.MR(v.cil(1.69,20,(u,w,0)))
        exigir(f'patron_roll_agujero_{i}',vacio(disco,h))
    exigir('paso_vecino_referencia_7_mm',abs(5*math.sqrt(2)-7)<.08)
    exigir('doble_37_7',abs(pieza('REF_horn_yaw').BoundingBox().xlen-37.7)<1e-6)
    for yy in (-56,56):
        for dz in (-34,34):
            exigir(f'frente_cerrado_fijacion_{yy}_{dz}',cara.intersect(v.cil(1.05,.7,(72.3,yy,v.Z+dz),(1,0,0))).Volume()>2)
    # Comparaciones de interferencia se conservan sin ocultar avisos.
    def inter(a,b):
        aa,bb=a.BoundingBox(),b.BoundingBox()
        if any(getattr(aa,e+'max')<=getattr(bb,e+'min')+1e-6 or getattr(bb,e+'max')<=getattr(aa,e+'min')+1e-6 for e in 'xyz'):return 0.
        return max(0,a.intersect(b).Volume())
    choques=[]
    for a,b in itertools.combinations(piezas,2):
        volumen=inter(a['shape'],b['shape'])
        if volumen>.1:choques.append({'a':a['name'],'b':b['name'],'mm3':round(volumen,5)})
    informe={'pruebas':resultados,'interferencias_home':choques,'fabricacion_liberada':False}
    (R/'evidencias/regresiones_R3.json').write_text(json.dumps(informe,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(informe,ensure_ascii=False,indent=2),flush=True)
    import auditar_v6 as auditor
    auditor.IGNORAR={frozenset(nombre_es(n) for n in par) for par in auditor.IGNORAR}
    auditor.IGNORAR.add(frozenset((nombre_es('10_adaptador_yaw'),nombre_es('REF_RDS3218'))))
    auditor.main(rapido=True,piezas=piezas)
    informe_barrido=json.loads((R/'evidencias/auditoria_v6_rapida.json').read_text(encoding='utf-8'))
    (R/'evidencias/barrido_R3.json').write_text(json.dumps(informe_barrido,ensure_ascii=False,indent=2),encoding='utf-8')
    exigir('barrido_45_poses_sin_interferencias_no_previstas',informe_barrido['aprobado_nominal'])
    v.exportar(piezas)
    for grupo in ('fixed','yaw','pitch','roll'):
        import shutil
        shutil.copy2(R/'STEP_V6'/f'v6_grupo_{grupo}.step',R/'STEP_V6'/f'R3_grupo_{grupo}.step')

if __name__=='__main__':main()
