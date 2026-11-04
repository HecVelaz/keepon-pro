"""Keepon V6 R4: fijación directa del buzzer y correcciones de interfaces, mm."""
from pathlib import Path
import sys,json,math,hashlib
import yaml,cadquery as cq
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent))
import generar_v6 as v
import revision_R3 as r3
C=yaml.safe_load((R/'config.yaml').read_text(encoding='utf-8'))
v.CFG=C;r3.CFG=C
perfil_anterior=v.perfil_brazo
alojamiento_anterior=v.alojamiento_cap

def perfil_invertido(espesor,z0,holgura=0,simple=False):
    s=perfil_anterior(espesor,z0,holgura,simple)
    return s.rotate((0,0,0),(0,0,1),180) if simple else s

def alojamiento_sin_tapa_pitch(s,montaje,plano,fijaciones,asiento):
    # Al retirar la tapa12, no generar tampoco sus cuatro pasos y cajeados.
    return s if montaje is v.HP else alojamiento_anterior(s,montaje,plano,fijaciones,asiento)

v.perfil_brazo=perfil_invertido;v.alojamiento_cap=alojamiento_sin_tapa_pitch

def construir():
    piezas=v.construir();por={p['name']:p for p in piezas};cil,caja=v.cil,v.caja
    simple=por['Referencia_brazo_simple_inclinacion'];simple['shape']=simple['shape'].rotate((0,0,v.Z),(0,1,v.Z),180)
    simple['note']='Brazo simple invertido 180 grados en su plano; alojamiento acompaña orientación.'
    # Horn comercial: el croquis distingue el paso central Ø3 de la cavidad25T.
    # Cubo hacia el motor. Se conserva0.5 mm de separación a la envolvente
    # simplificada del servo; el bolsillo y su retención acompañan el espesor real.
    b=C['brazos'];servo=v.v2.MG996R;zcubo=servo.H-servo.Fb+b['circular_juego_axial_servo_mm']
    alto_cubo=b['circular_altura_total_mm']-b['circular_espesor_mm'];pl=zcubo+alto_cubo;tope=pl+b['circular_espesor_mm']
    horn=cil(b['circular_diametro_mm']/2,b['circular_espesor_mm'],(0,0,pl))
    horn=horn.fuse(cil(b['circular_cubo_diametro_mm']/2,alto_cubo,(0,0,zcubo)))
    horn=horn.cut(cil(b['circular_agujero_central_mm']/2,b['circular_altura_total_mm']+2,(0,0,zcubo-1)))
    # Reserva nominal para acoplar el eje: el dibujo no dimensiona el perfil ni
    # la profundidad exactos del estriado. No representar dientes inventados.
    profundidad=servo.S+b['circular_reserva_fondo_cavidad_mm']-zcubo
    horn=horn.cut(cil(b['circular_diametro_cavidad_25T_nominal_mm']/2,profundidad,(0,0,zcubo)))
    for i in range(4):
        ang=i*math.pi/2;u=b['circular_radio_agujeros_mm']*math.cos(ang);w=b['circular_radio_agujeros_mm']*math.sin(ang)
        horn=horn.cut(cil(b['circular_diametro_agujeros_mm']/2,6,(u,w,zcubo-1)))
    por['Referencia_disco_balanceo'].update(shape=v.MR(horn.clean()),color=(.85,.035,.025),note='Croquis del usuario: disco rojo25T Ø19.8, cuatroØ3 a R7, paso centralØ3, cuboØ9, disco2.45, altura total4.5. Cavidad de estriado nominal sin dientes.')
    carcasa=por['04_carcasa_inferior_cabeza'];cuerpo=carcasa['shape'];pl_anterior=servo.S+1-b['circular_espesor_mm']
    # Rellenar bolsillo provisional antes de mover la cara de asiento0.9 mm.
    cuerpo=cuerpo.fuse(v.MR(cil(b['circular_diametro_mm']/2+v.H,tope-pl_anterior,(0,0,pl_anterior))))
    cuerpo=cuerpo.cut(v.MR(caja(-28,28,-19,19,min(pl_anterior,servo.S+1-v.k3.BRAZO_T)-.01,pl)))
    cuerpo=cuerpo.cut(v.MR(cil(b['circular_diametro_mm']/2+v.H,b['circular_espesor_mm']+v.H,(0,0,pl))))
    cuerpo=cuerpo.cut(v.MR(cil(b['circular_acceso_carcasa_mm']/2,18,(0,0,pl-1))))
    for i in range(4):
        ang=i*math.pi/2;u=b['circular_radio_agujeros_mm']*math.cos(ang);w=b['circular_radio_agujeros_mm']*math.sin(ang)
        cuerpo=cuerpo.cut(v.MR(cil(v.M3/2,16,(u,w,pl-1))))
    cuerpo=v.alojamiento_cap(cuerpo,v.MR,pl,C['roll']['fijaciones_retencion_yz_mm'],21.4)
    carcasa.update(shape=cuerpo.clean(),note='Postes Pi8 mm; bolsillo de discoØ19.8×2.45, asiento desplazado0.9 mm y cuatro pasosM3 a R7, acceso centralØ8.4.')
    tapa=v.cap_brazo(v.MR,pl,C['roll']['fijaciones_retencion_yz_mm'])
    tapa=tapa.cut(v.MR(cil(b['circular_abertura_retencion_mm']/2,6,(0,0,pl-3))))
    por['13_retencion_disco_balanceo'].update(shape=tapa.clean(),note='Retención periférica con aberturaØ18.2: solape radial0.8 sobre discoØ19.8. Asiento y postes acompañan el horn de4.5 mm total.')
    # Conservar los140 mm libres de la cinta al bajar la Pi4.6 mm: bajar
    # tambien la curva superior, en lugar de agregar longitud ficticia al flex.
    delta=C['raspberry']['altura_anterior_mm']-C['raspberry']['altura_poste_mm']
    x0,x1=8.8,64.8;za,zb=v.Z-33.45-delta,v.Z+9.09;radio_flex=(x1-x0)/2;medio=(x0+x1)/2
    la=(140-math.pi*radio_flex+zb-za)/2;lb=(140-math.pi*radio_flex-zb+za)/2;arriba=za+la
    inicio=cq.Workplane('XY',origin=(x0,0,za)).rect(.25,12.5).workplane(offset=20).rect(.25,17).loft().val()
    tramos=[inicio,v.g.box(.25,17,la-20,x0,0,za+20+(la-20)/2),v.g.box(.25,17,lb,x1,0,zb+lb/2)]
    arco=v.g.ring(2*radio_flex+.25,2*radio_flex-.25,17,(medio,-8.5,arriba),(0,1,0)).intersect(v.g.box(100,30,75,medio,0,arriba+37.5))
    por['Referencia_cinta_camara_150'].update(shape=cq.Compound.makeCompound(tramos+[arco]),note='Reserva de140 mm libres mas10 mm de insercion; curva superior acompana la Pi con postes de8 mm.')
    # Retirar los tres postes del montaje anterior; la piel frontal empieza en X=70.
    cara=por['06_cara_con_ojos_integrados']['shape'];anterior=C['buzzer']['montaje_R3']
    for yy in C['buzzer']['fijaciones_y_mm']:
        cara=cara.cut(cil(4.6,7,(63,yy,v.Z+C['buzzer']['z_centro_relativo_mm']),(1,0,0)))
    cara=cara.cut(cil(anterior['radio_poste_pcb_mm']+.1,70-anterior['inicio_poste_pcb_x_mm'],(anterior['inicio_poste_pcb_x_mm'],anterior['centro_fijacion_y_mm'],v.Z+anterior['centro_fijacion_z_relativo_mm']),(1,0,0)))
    p=C['buzzer'];m=p['montaje_R4'];x=m['pcb_x_mm'];xf=x+p['pcb_espesor_mm'];y0=m['pcb_y_inicial_mm'];y1=y0+p['pcb_largo_mm'];zc=v.Z+m['pcb_z_centro_relativo_mm'];z0=zc-p['pcb_ancho_mm']/2;z1=z0+p['pcb_ancho_mm']
    hy=y0+p['agujero_desde_extremo_buzzer_mm'];hz=z0+m['agujero_desde_borde_ancho_mm'];radio=m['diametro_transductor_referencia_mm']/2
    poste=cil(m['radio_poste_mm'],70-xf,(xf,hy,hz),(1,0,0))
    # Alivio local para mantener espacio alrededor del transductor. La cota de
    # diámetro/centro del cilindro sigue siendo referencia, no una medición nueva.
    alto=p['altura_total_mm']-p['pcb_espesor_mm']
    poste=poste.cut(cil(radio+m['holgura_transductor_mm'],alto+m['holgura_transductor_mm'],(xf,m['centro_transductor_y_mm'],zc),(1,0,0)))
    cara=cara.fuse(poste)
    cara=cara.cut(cil(m['piloto_directo_m3_mm']/2,m['profundidad_piloto_mm'],(xf,hy,hz),(1,0,0)))
    # Extremo de conexiones libre, sin apoyos ni guia junto al conector.
    por['06_cara_con_ojos_integrados'].update(shape=cara.clean(),note='Buzzer directo a poste integrado con M3x5 posterior ciego; extremo de cables libre.')
    pcb=caja(x,xf,y0,y1,z0,z1).cut(cil(p['agujero_diametro_mm']/2,p['pcb_espesor_mm']+2,(x-1,hy,hz),(1,0,0)))
    modulo=pcb.fuse(cil(radio,alto,(xf,m['centro_transductor_y_mm'],zc),(1,0,0))).clean()
    por['Referencia_placa_modulo_buzzer'].update(name='Referencia_modulo_buzzer_31_8x12_8x10',shape=modulo,note='PCB31.8x12.8x1.5, altura total10; agujero14.8 desde extremo del buzzer. CilindroØ12/centro nominales previos.')
    tornillo=cil(1.5,m['largo_tornillo_mm'],(x,hy,hz),(1,0,0)).fuse(cil(3,3,(x,hy,hz),(-1,0,0)))
    por['Tornillo_M3_buzzer_placa'].update(shape=tornillo,note='M3x5 directo desde dorso de PCB, puntaX63.5. Piloto plásticoØ2.5, comprobar tornillo/material real.')
    retirar={'12_retencion_brazo_simple_inclinacion','15_soporte_trasero_modulo_buzzer','21_arandela_aislante_buzzer'}
    return [p for p in piezas if p['name'] not in retirar and not p['name'].startswith(('Tornillo_M3_retencion_inclinacion_','Tornillo_M3_soporte_buzzer_'))]

def guardar_step_si_cambio(s,destino):
    """Conservar artefacto y cache nativa si su geometria no cambio."""
    if destino.exists():
        previo=cq.importers.importStep(str(destino)).val()
        if abs(previo.Volume()-s.Volume())<1e-5:
            if previo.cut(s).Volume()+s.cut(previo).Volume()<1e-5:return
    cq.exporters.export(s,str(destino))


def exportar(piezas):
    for n in ('STEP_V6','STL_REVISION_NO_IMPRIMIR','evidencias','vistas','IMPRESION_STL'):(R/n).mkdir(exist_ok=True)
    a=cq.Assembly(name='Keepon_V6_R4');grupos={n:[] for n in ('fixed','yaw','pitch','roll')};cuerpos=[];mallas=[];inventario=[]
    for p in piezas:
        s=p['shape'];assert s.isValid(),p['name']
        if p['printed']:assert len(s.Solids())==1,p['name']
        a.add(s,name=p['name'],color=cq.Color(*p['color']));grupos[p['group']].append(s)
        for cuerpo in s.Solids():
            bb=cuerpo.BoundingBox();cuerpos.append({'nombre':p['name'],'grupo':p['group'],'color':p['color'],'caja_mm':[bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax]})
        if p['printed']:
            guardar_step_si_cambio(s,R/'STEP_V6'/f"{p['name']}.step");ip=v.pose_impresion(s,p['orientation'])
            cq.exporters.export(ip,str(R/'STL_REVISION_NO_IMPRIMIR'/f"{p['name']}.stl"),tolerance=.08,angularTolerance=.12)
            inventario.append({'nombre':p['name'],'nota':p['note']})
        vs,fs=s.tessellate(.5,.16);mallas.append({'name':p['name'],'group':p['group'],'color':p['color'],'printed':p['printed'],'v':[[q.x,q.y,q.z] for q in vs],'f':fs})
        print('EXPORTADO',p['name'],flush=True)
    a.export(str(R/'STEP_V6/00_ensamble_V6_R4.step'));volumenes={}
    for n,ss in grupos.items():
        s=cq.Compound.makeCompound(ss);cq.exporters.export(s,str(R/'STEP_V6'/f'R4_grupo_{n}.step'));volumenes[n]={'volumen_mm3':s.Volume(),'solidos':len(s.Solids())}
    for nombre,datos in [('inventario_v6.json',inventario),('mallas_v6.json',mallas),('evidencias/cuerpos_v6.json',cuerpos),('evidencias/volumenes_grupos_v6.json',volumenes),('evidencias/trazabilidad_v6.json',{'revision':C['revision'],'z_eje_pitch_roll_mm':v.Z,'fabricacion_liberada':False,'sha256_config':hashlib.sha256((R/'config.yaml').read_bytes()).hexdigest()})]:(R/nombre).write_text(json.dumps(datos,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':exportar(construir())
