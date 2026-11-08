"""Regresiones de cambios R4, con B-Rep y barrido nominal."""
from pathlib import Path
import sys,json,math
import generar_R4 as g
sys.path.insert(0,str(g.R.parent))
import auditar_v6 as a
from revision_R3 import nombre_es

def main(exportar=False):
    ps=g.construir();por={p['name']:p for p in ps};pruebas={};v=g.v
    def exigir(n,x):
        pruebas[n]=bool(x)
        if not x:raise AssertionError(n)
    exigir('retencion_pitch_eliminada','12_retencion_brazo_simple_inclinacion' not in por)
    exigir('tornillos_retencion_pitch_eliminados',not any(n.startswith('Tornillo_M3_retencion_inclinacion_') for n in por))
    exigir('bastidor_y_arandela_eliminados',not any(n.startswith(('15_','21_')) for n in por))
    exigir('tornillo_unico_buzzer',sum(n=='Tornillo_M3_buzzer_placa' for n in por)==1 and not any(n.startswith('Tornillo_M3_soporte_buzzer_') for n in por))
    bb=por['Referencia_brazo_simple_inclinacion']['shape'].BoundingBox();exigir('brazo_invertido_punta_hacia_X_negativo',bb.xmin<-21 and bb.xmax<4.61)
    exigir('imprimibles_monosolidos_validos',all(p['shape'].isValid() and len(p['shape'].Solids())==1 for p in ps if p['printed']))
    s=por['03_cuna_de_inclinacion']['shape']
    for u,w in g.C['roll']['fijaciones_pitch_xz_mm']:
        # Comprobar que queda plástico donde antes había pasos/cajeados de tapa.
        herramienta=v.HP(v.cil(1.6,6,(u,w,15)))
        exigir(f'antiguo_paso_tapa_relleno_{u}_{w}',s.intersect(herramienta).Volume()>25)
    s=por['04_carcasa_inferior_cabeza']['shape'];p=g.C['raspberry'];z=v.Z+p['z_base_relativo_mm']
    for x,y in p['postes_xy_mm']:
        exigir(f'poste_8_mm_{x}_{y}',s.intersect(v.cil(2.9,.5,(x,y,z+8.05))).Volume()<1e-5 and s.intersect(v.cil(4.4,.5,(x,y,z+7.4))).Volume()>27)
    m=g.C['buzzer']['montaje_R4'];s=por['Referencia_modulo_buzzer_31_8x12_8x10']['shape'];bb=s.BoundingBox()
    exigir('buzzer_largo_31_8_ancho_12_8_altura_10',abs(bb.ylen-31.8)<1e-6 and abs(bb.zlen-12.8)<1e-6 and abs(bb.xlen-10)<1e-6)
    hy=m['pcb_y_inicial_mm']+g.C['buzzer']['agujero_desde_extremo_buzzer_mm'];hz=v.Z+m['pcb_z_centro_relativo_mm']-g.C['buzzer']['pcb_ancho_mm']/2+m['agujero_desde_borde_ancho_mm']
    exigir('agujero_PCB_14_8_desde_extremo',s.intersect(v.cil(1.49,1.4,(m['pcb_x_mm'],hy,hz),(1,0,0))).Volume()<1e-5)
    cara=por['06_cara_con_ojos_integrados']['shape'];exigir('tornillo_ciego_piel_frontal_intacta',cara.intersect(v.cil(1.4,2,(71,hy,hz),(1,0,0))).Volume()>12)
    for zz in (130.6,139.4):
        exigir(f'apoyo_conector_eliminado_{zz}',cara.intersect(v.cil(1.9,9,(60,23.3,zz),(1,0,0))).Volume()<1e-5)
    exigir('guia_conector_eliminada',cara.intersect(v.caja(58.3,69.9,25.6,26.7,129.7,140.3)).Volume()<1e-5)
    exigir('disco_rojo_25T',por['Referencia_disco_balanceo']['color']==(.85,.035,.025) and g.C['brazos']['circular_dientes']==25)
    s=por['Referencia_disco_balanceo']['shape'];bb=s.BoundingBox()
    exigir('disco_19_8_y_altura_total_4_5',abs(bb.ylen-19.8)<1e-6 and abs(bb.zlen-19.8)<1e-6 and abs(bb.xlen-4.5)<1e-6)
    exigir('paso_central_3',s.intersect(v.MR(v.cil(1.49,22,(0,0,0)))).Volume()<1e-5)
    for i in range(4):
        ang=i*math.pi/2;u=7*math.cos(ang);w=7*math.sin(ang)
        exigir(f'agujero_3_a_radio_7_{i}',s.intersect(v.MR(v.cil(1.49,22,(u,w,0)))).Volume()<1e-5)
        exigir(f'pared_alrededor_agujero_{i}',s.intersect(v.MR(v.cil(1.9,.8,(u,w,16)))).Volume()>1)
    exigir('espesor_disco_2_45',g.C['brazos']['circular_espesor_mm']==2.45)
    a.RAIZ=g.R;a.v6=v;a.IGNORAR={frozenset(nombre_es(n) for n in par) for par in a.IGNORAR}
    a.IGNORAR.add(frozenset(('10_soporte_centrado_servo_base','Referencia_servo_base_RDS3218')))
    a.IGNORAR.add(frozenset(('06_cara_con_ojos_integrados','Tornillo_M3_buzzer_placa')))
    a.main(rapido=True,piezas=ps)
    barrido=json.loads((g.R/'evidencias/auditoria_v6_rapida.json').read_text(encoding='utf-8'));exigir('barrido_sin_interferencias_imprevistas',barrido['aprobado_nominal'])
    (g.R/'evidencias/regresiones_R4.json').write_text(json.dumps(pruebas,indent=2,ensure_ascii=False),encoding='utf-8');print(len(pruebas),'comprobaciones R4 aprobadas',flush=True)
    if exportar:g.exportar(ps)

if __name__=='__main__':
    (g.R/'evidencias').mkdir(exist_ok=True);main('--exportar' in sys.argv)
