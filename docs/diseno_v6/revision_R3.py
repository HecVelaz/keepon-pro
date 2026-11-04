"""Revisión R3: interfaces coordinadas, mm. Las fuentes R2 quedan en HISTORIAL."""
import math
from pathlib import Path
import cadquery as cq
import yaml

CFG=yaml.safe_load((Path(__file__).parent/'config.yaml').read_text(encoding='utf-8'))
NOMBRES={
 '01_base':'01_base_con_pilares','02_horquilla_yaw':'02_horquilla_de_giro',
 '03_cuna_pitch':'03_cuna_de_inclinacion','04_cuba_cabeza':'04_carcasa_inferior_cabeza',
 '05_tapa_ventilada':'05_tapa_superior_ventilada','06_cara_binocular':'06_cara_con_ojos_integrados',
 '08_bandeja_electronica':'08_bandeja_de_electronica','09_retencion_esp32':'09_abrazadera_ESP32',
 '10_adaptador_yaw':'10_soporte_centrado_servo_base','11_retencion_horn_yaw':'11_retencion_brazo_doble_base',
 '12_retencion_horn_pitch_simple':'12_retencion_brazo_simple_inclinacion',
 '13_retencion_horn_roll':'13_retencion_disco_balanceo','15_soporte_RLBZ23':'15_soporte_trasero_modulo_buzzer',
 '21_arandela_buzzer':'21_arandela_aislante_buzzer','REF_RDS3218':'Referencia_servo_base_RDS3218',
 'REF_HS7955TG':'Referencia_servo_inclinacion_HS7955TG','REF_MG996R_exterior':'Referencia_servo_balanceo_MG996R',
 'REF_horn_yaw':'Referencia_brazo_doble_base','REF_horn_roll':'Referencia_disco_balanceo',
 'ESTUDIO_horn_pitch_simple_NO_MEDIDO':'Referencia_brazo_simple_inclinacion',
 'REF_Pi5':'Referencia_Raspberry_Pi_5','REF_Active_Cooler_reserva':'Reserva_refrigerador_Raspberry_Pi',
 'REF_Camera3_NoIR':'Referencia_camara_NoIR_3','REF_pivote_M4':'Referencia_pivote_M4',
 'REF_FFC150_R28':'Referencia_cinta_camara_150','REF_RLBZ23_PCB':'Referencia_placa_modulo_buzzer'}

def nombre_es(nombre):
    if nombre in NOMBRES:return NOMBRES[nombre]
    if nombre.startswith('REF_M3_'):
        return nombre.replace('REF_M3_','Tornillo_M3_').replace('ret_','retencion_').replace('yaw','base').replace('pitch','inclinacion').replace('roll','balanceo').replace('portamodulo','soporte_buzzer').replace('PCB','placa')
    return nombre.replace('REF_','Referencia_').replace('yaw','base').replace('pitch','inclinacion').replace('roll','balanceo')

def perfil_simple(espesor,z0,holgura=0):
    """Envolvente de dos extremos circulares y sus tangentes exteriores exactas.

    Eje del servo en (0,0), extremo pequeño hacia +X. 26.4 es largo total.
    Los extremos tienen diámetros 9.2 y 6.2, no radios ni distancias entre centros.
    """
    b=CFG['brazos'];rp,rg=[d/2 for d in b['simple_diametros_extremos_mm']]
    distancia=b['simple_longitud_mm']-rp-rg
    nx=(rg-rp)/distancia;ny=math.sqrt(1-nx*nx)
    rg+=holgura;rp+=holgura
    puntos=[(rg*nx,rg*ny),(distancia+rp*nx,rp*ny),(distancia+rp*nx,-rp*ny),(rg*nx,-rg*ny)]
    s=cq.Workplane('XY').polyline(puntos).close().extrude(espesor).val().translate((0,0,z0))
    for x,r in ((0,rg),(distancia,rp)):
        s=s.fuse(cq.Solid.makeCylinder(r,espesor,cq.Vector(x,0,z0)))
    return s.clean()

def aplicar(piezas,mod):
    """Modifica piezas y referencias juntas antes de exportar cualquier formato."""
    cil,caja=mod['cil'],mod['caja'];Z=mod['Z'];HP,MR,MY,HY=[mod[k] for k in ('HP','MR','MY','HY')]
    v2,k3,g=[mod[k] for k in ('v2','k3','g')];M3=mod['M3'];H=mod['H']
    por={p['name']:p for p in piezas}
    # Base: centros geométricos de ambos pilares. Se rellenan los pilotos anteriores.
    base=por['01_base']['shape'];z0=CFG['yaw']['z_pedestales_mm']
    for x in (-18,38):
        for y in (-6,6):
            viejo=x+4 if x<0 else x-4
            base=base.fuse(cil(1.3,8,(viejo,y,30)))
            base=base.cut(cil(CFG['insertos']['diametro_instalacion_mm']/2,6.6,(x,y,z0-6.6)))
    por['01_base'].update(shape=base.clean(),printed=True,note='Pilares con alojamientos ciegos M3 centrados; insertos L5 nominales.')
    # Adaptador: cuerpo centrado en X=0,Y=10; eje de giro conserva X=Y=0.
    p=CFG['yaw'];an,fo,al=p['dimensiones_adaptador_mm'];cx,cy=p['centro_adaptador_xy_mm']
    soporte=g.rbox(an,fo,al,(cx,cy,z0+al/2),4)
    servo=v2.RDS3218;xc=servo.L/2-servo.a;pres=p['interferencia_presion_por_lado_mm']
    ventana=caja(-servo.a+pres,servo.L-servo.a-pres,-servo.W/2+pres,servo.W/2-pres,-1,al+1)
    # Brida bajo el soporte: orejas alojadas en dos rebajes poco profundos.
    for signo in (-1,1):
        xx=xc+signo*(servo.L/2+(servo.Lf-servo.L)/4)
        ventana=ventana.fuse(caja(xx-(servo.Lf-servo.L)/4-H,xx+(servo.Lf-servo.L)/4+H,
                                  -servo.W/2-H,servo.W/2+H,-1,0.5))
    soporte=soporte.cut(v2.Montaje((0,0,z0),(0,0,1),(0,1,0))(ventana))
    for x,y in p['fijaciones_base_xy_mm']:
        soporte=soporte.cut(cil(M3/2,al+2,(x,y,z0-1)))
    for a in (-1,1):
        for b in (-1,1):
            x,y=b*servo.hw/2,xc+a*servo.hs/2
            soporte=soporte.cut(cil(CFG['insertos']['diametro_instalacion_mm']/2,5.6,(x,y,z0+.4)))
    # Dos pares de labios abrazan las orejas por sus bordes laterales.
    # La brida asienta a Z=44; no se obliga a pasar las orejas por el hueco del cuerpo.
    montaje_base=v2.Montaje((0,0,z0),(0,0,1),(0,1,0))
    for signo in (-1,1):
        xa=xc-servo.Lf/2 if signo<0 else servo.L-servo.a
        xb=-servo.a if signo<0 else xc+servo.Lf/2
        for lado in (-1,1):
            ya,yb=(servo.W/2-pres,servo.W/2+2) if lado>0 else (-servo.W/2-2,-servo.W/2+pres)
            soporte=soporte.fuse(montaje_base(caja(xa,xb,ya,yb,al-.2,al+servo.tf)))
    por['10_adaptador_yaw'].update(shape=soporte.clean(),note='Cuerpo centrado y orejas con asiento; interferencia nominal de presión 0.05 mm/lado, calibrar impresión.')
    # Pi: diámetro 6→9 y altura 12.6→10.6. Bajar también placa, cooler y extremo de flex.
    p=CFG['raspberry'];cuba=por['04_cuba_cabeza']['shape'];zp=Z+p['z_base_relativo_mm'];delta=p['altura_anterior_mm']-p['altura_poste_mm']
    for x,y in p['postes_xy_mm']:
        cuba=cuba.cut(cil(3.01,p['altura_anterior_mm']+1,(x,y,zp)))
        cuba=cuba.fuse(cil(p['diametro_poste_mm']/2,p['altura_poste_mm'],(x,y,zp)))
        cuba=cuba.cut(cil(p['piloto_mm']/2,p['altura_poste_mm']+2,(x,y,zp-1)))
    for n in ('REF_Pi5','REF_Active_Cooler_reserva'):
        por[n]['shape']=por[n]['shape'].translate((0,0,-delta))
    # El flex sólo es una reserva geométrica: extender el tramo que conecta a la Pi.
    flex=por['REF_FFC150_R28']['shape'];por['REF_FFC150_R28']['shape']=flex.fuse(caja(8.675,8.925,-6.25,6.25,Z-33.45-delta,Z-33.45)).clean()
    por['REF_FFC150_R28']['note']='Reserva de flex con extremo Pi bajado 2 mm; comprobar recorrido físico de cinta de 150 mm.'
    # Brazo simple real y acceso de lado a lado de la cuna, coaxial al HS7955.
    b=CFG['brazos'];ts=b['simple_espesor_mm'];pp=v2.HS7955.S+1-ts
    simple=perfil_simple(ts,pp).fuse(cil(4.5,pp-(v2.HS7955.H-v2.HS7955.Fb+.5),(0,0,v2.HS7955.H-v2.HS7955.Fb+.5)))
    simple=simple.cut(cil(1.7,20,(0,0,0)))
    por['ESTUDIO_horn_pitch_simple_NO_MEDIDO'].update(shape=HP(simple),note=CFG['pitch']['nota_brazo'])
    cuna=por['03_cuna_pitch']['shape'];bb=cuna.BoundingBox()
    cuna=cuna.cut(cil(b['paso_tornillo_central_mm']/2,bb.ylen+4,(0,bb.ymin-2,Z),(0,1,0)))
    por['03_cuna_pitch'].update(shape=cuna.clean(),note='Acceso pasante coaxial Ø8.4 de extremo a extremo para tornillo central del brazo simple.')
    # Disco de roll Ø20x2.6: nuevo bolsillo, mismo eje y misma cara de apoyo.
    tr=b['circular_espesor_mm'];pl=v2.MG996R.S+1-tr;top=v2.MG996R.S+1;pr=v2.MG996R.S+1-k3.BRAZO_T
    # Reconstrucción limitada del bolsillo doble y del acceso central anterior.
    cuba=cuba.fuse(MR(caja(-21,21,-5,5,pr,top+.1)))
    cuba=cuba.fuse(MR(cil(4.2,top+4-pr,(0,0,pr))))
    cuba=cuba.cut(MR(cil(b['circular_diametro_mm']/2+H,tr+H,(0,0,pl))))
    # Acceso central reducido: Ø8.4 se solaparía con los M3 de radio5.
    cuba=cuba.cut(MR(cil(1.7,16,(0,0,pl-1))))
    disco=cil(b['circular_diametro_mm']/2,tr,(0,0,pl))
    cubo_z=v2.MG996R.H-v2.MG996R.Fb+.5
    disco=disco.fuse(cil(4.5,pl-cubo_z,(0,0,cubo_z)))
    disco=disco.cut(cil(1.7,20,(0,0,0)))
    for i in range(b['circular_numero_agujeros']):
        ang=i*2*math.pi/b['circular_numero_agujeros'];u=b['circular_radio_agujeros_mm']*math.cos(ang);v=b['circular_radio_agujeros_mm']*math.sin(ang)
        disco=disco.cut(cil(M3/2,20,(u,v,0)))
        cuba=cuba.cut(MR(cil(M3/2,16,(u,v,pl-1))))
    por['REF_horn_roll'].update(shape=MR(disco.clean()),note='Disco comercial Ø20×2.6; cuatro pasos M3 a R5, 90°. Cubo y estriado se conservan como referencia nominal.')
    # Retención periférica: apoya el borde del disco, deja libre cubo/eje.
    # El patrón R5 se resuelve en la carcasa, no en la tapa del lado del motor.
    cap=por['13_retencion_horn_roll']['shape'].translate((pl-pr,0,0))
    cap=cap.cut(MR(cil(9.8,6,(0,0,pl-3))))
    por['13_retencion_horn_roll'].update(shape=cap.clean(),note='Retención periférica del disco, abertura Ø19.6; cuatro M3 a R5 pasantes en carcasa. Comprobar tornillería real del disco.')
    # La tapa del brazo simple acompaña su espesor medido de 2.8 mm.
    por['12_retencion_horn_pitch_simple']['shape']=por['12_retencion_horn_pitch_simple']['shape'].translate((0,-(ts-k3.BRAZO_T),0))
    por['04_cuba_cabeza']['shape']=cuba.clean()
    # Integrar carcasas y lentes a la cara; rellenar holgura radial de lentes.
    cara=por['06_cara_binocular']['shape']
    for y in CFG['ojos']['centros_y_mm']:
        ojo=mod['ojo_walle'](y);lente=mod['lente_walle'](y)
        cara=cara.fuse(ojo).fuse(lente)
        p=CFG['ojos'];x=73+p['espesor_base_mm']-p['profundidad_alojamiento_mm']
        cara=cara.fuse(cil(p['alojamiento_lente_diametro_mm']/2,p['profundidad_alojamiento_mm']+.05,(x,y,Z+p['z_relativo_mm']),(1,0,0)))
    # Buzzer por detrás: PCB paralelo al frente, transductor mirando +X.
    p=CFG['buzzer'];r=p['montaje_R3'];x=r['pcb_x_mm'];y0=r['pcb_y_inicial_mm'];zc=Z+r['pcb_z_centro_relativo_mm'];z0b=zc-p['pcb_ancho_mm']/2
    y1=y0+p['pcb_largo_mm'];z1=z0b+p['pcb_ancho_mm'];hy=r['centro_fijacion_y_mm'];hz=Z+r['centro_fijacion_z_relativo_mm'];esp=p['pcb_espesor_mm']
    pcb=caja(x,x+esp,y0,y1,z0b,z1).cut(cil(p['agujero_diametro_mm']/2,esp+2,(x-1,hy,hz),(1,0,0)))
    # Bastidor del lado delantero del PCB, abierto sobre la electrónica; tornillo entra por atrás.
    xa,xb=r['placa_soporte_x_mm'];soporte=caja(xa,xb,y0-2,y1+2,z0b-2,z1+2)
    soporte=soporte.cut(caja(xa-1,xb+1,y0+.8,y1-.8,z0b+.8,z1-.8))
    soporte=soporte.fuse(cil(4,xb-xa,(xa,hy,hz),(1,0,0)))
    # Conectar el apoyo del agujero al borde superior del bastidor.
    soporte=soporte.fuse(caja(xa,xb,hy-2,hy+2,hz,z1+1))
    soporte=soporte.fuse(caja(61,63,min(p['fijaciones_y_mm'])-4,y0-1,zc-5,zc+5))
    soporte=soporte.fuse(caja(61,63,y1+1,max(p['fijaciones_y_mm'])+4,zc-5,zc+5))
    for yy in p['fijaciones_y_mm']:
        soporte=soporte.fuse(caja(61,63,yy-4,yy+4,zc-5,zc+5))
        soporte=soporte.cut(cil(M3/2,6,(60,yy,zc),(1,0,0)))
        soporte=soporte.cut(cil(4.75,5,(63,yy,zc),(1,0,0)))
    # Apoyo roscado ciego desde X=64; nunca atraviesa la piel frontal X=70..73.
    cara=cara.fuse(cil(r['radio_poste_pcb_mm'],70-r['inicio_poste_pcb_x_mm'],(r['inicio_poste_pcb_x_mm'],hy,hz),(1,0,0)))
    cara=cara.cut(cil(CFG['insertos']['diametro_instalacion_mm']/2,r['profundidad_ciega_pcb_mm'],(r['inicio_poste_pcb_x_mm'],hy,hz),(1,0,0)))
    soporte=soporte.cut(cil(r['radio_poste_pcb_mm']+.25,4,(r['inicio_poste_pcb_x_mm']-1,hy,hz),(1,0,0)))
    # Ocultar también las fijaciones heredadas de cara y cámara: entradas ciegas
    # desde atrás, con piel frontal continua. El resto de la cara no cambia.
    for yy in (-56,56):
        for dz in (-34,34):
            cara=cara.fuse(cil(1.7,3,(70,yy,Z+dz),(1,0,0)))
            cara=cara.cut(cil(1.1,2.2,(70,yy,Z+dz),(1,0,0)))
    for yy in (-10.5,10.5):
        for dz in (-12.4,.1):
            cara=cara.fuse(cil(1.1,3,(70,yy,Z+dz),(1,0,0)))
            cara=cara.cut(cil(1.1,5.24,(66.56,yy,Z+dz),(1,0,0)))
    por['06_cara_binocular'].update(shape=cara.clean(),note='Cara y dos ojos completos en un sólido; módulo buzzer desmontable sólo desde atrás, postes ciegos.')
    por['15_soporte_RLBZ23'].update(shape=soporte.clean(),note='PCB paralelo al dorso de cara, transductor orientado a boca +X; altura real y posición del cilindro pendientes.')
    por['REF_RLBZ23_PCB'].update(shape=pcb.clean(),note=r['nota'])
    alto=p['arandela_impresa_espesor_mm'];ar=cil(3.5,alto,(x-alto,hy,hz),(1,0,0)).cut(cil(M3/2,alto+2,(x-alto-1,hy,hz),(1,0,0)))
    por['21_arandela_buzzer']['shape']=ar
    # Tornillo de PCB ahora desde atrás hacia cara; M3x6, punta X=67.7.
    torn=cil(1.5,6,(x-alto,hy,hz),(1,0,0)).fuse(cil(3,3,(x-alto,hy,hz),(-1,0,0)))
    por['REF_M3_buzzer_PCB'].update(shape=torn,note='M3x6 desde atrás; punta ciega X=63.7, frente X=73.')
    # El acceso completo no debe dejar holgado el apoyo opuesto M4.
    # Casquillo extraíble: retirarlo junto con el pivote para pasar la herramienta.
    cp=CFG['pitch']['casquillo_pivote'];ya,yb=cp['y_cuerpo_mm'];e=cp['espesor_labio_mm']
    casquillo=cil(cp['diametro_cuerpo_mm']/2,yb-ya,(0,ya,Z),(0,1,0))
    casquillo=casquillo.fuse(cil(cp['diametro_labio_mm']/2,e,(0,ya-e,Z),(0,1,0)))
    casquillo=casquillo.cut(cil(cp['diametro_paso_mm']/2,yb-ya+e+2,(0,ya-e-1,Z),(0,1,0)))
    piezas.append(dict(name='22_casquillo_extraible_pivote_inclinacion',shape=casquillo.clean(),group='pitch',printed=True,orientation='pitch_cap_down',color=(.85,.65,.22),note='Restituye apoyo M4 tras abrir acceso Ø8.4; retirar pivote y casquillo para acceso axial completo.'))
    retirar={'16_ojo_izq','17_ojo_der','19_lente_ojo_izq','20_lente_ojo_der'}
    salida=[]
    for p in piezas:
        if p['name'] in retirar:continue
        p['name']=nombre_es(p['name']);salida.append(p)
    return salida
