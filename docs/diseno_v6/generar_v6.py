"""Keepon V6 nominal integrado, mm; +X frente, +Y izquierda, +Z arriba.

Reutiliza fuentes V5 y las referencias de servo/brazo V3/V4. Las dimensiones
comerciales no medidas se declaran en config.yaml y bloquean fabricación.
El modelo CAD puede examinarse completo sin confundirlo con un ensayo físico.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import sys
import cadquery as cq
import yaml

RAIZ = Path(__file__).resolve().parent
REPO = RAIZ.parents[1]
CFG = yaml.safe_load((RAIZ / 'config.yaml').read_text(encoding='utf-8'))
spec = importlib.util.spec_from_file_location('v5_v6', RAIZ.parent / 'diseno_v5/generar_v5.py')
v5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v5)
sys.path.insert(0, str(REPO / 'docs/keepon_v3_cad/fuente'))
import keepon_v3_cad as k3
import keepon_cad as v2

g = v5.g
k3.BRAZO_L = CFG['brazos']['doble_longitud_mm']
H = CFG['impresion']['holgura_encastre_por_lado_mm']
HS = CFG['impresion']['holgura_servo_por_lado_mm']
M3 = CFG['tornillos']['paso_m3_mm']
T = CFG['impresion']['pared_refuerzo_mm']
R = CFG['impresion']['radio_transicion_mm']
P_YAW = CFG['yaw']['z_pedestales_mm'] + CFG['yaw']['espesor_adaptador_mm'] + v2.RDS3218.tf
# El bolsillo envuelve el brazo por debajo de su plano de apoyo.
DZ = P_YAW + v2.RDS3218.S + 1 - k3.BRAZO_T - 49
Z = CFG['pitch']['z_original_mm'] + DZ
C = (0, 0, Z)
MY = v2.Montaje((0, 0, P_YAW), (0, 0, 1), (0, 1, 0))
HP = v2.Montaje((0, CFG['pitch']['y_brida_mm'], Z), (0, 1, 0), (1, 0, 0))
MR = v2.Montaje((CFG['roll']['x_brida_mm'], 0, Z), (1, 0, 0), (0, 1, 0))
HY = v2.Montaje((0, 0, P_YAW), (0, 0, 1), (1, 0, 0))


def caja(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1-x0, y1-y0, z1-z0, cq.Vector(x0, y0, z0))


def cil(r, h, p, d=(0, 0, 1)):
    return cq.Solid.makeCylinder(r, h, cq.Vector(*p), cq.Vector(*d))


def placa_plana(ancho, alto, profundidad, montaje, z0, radio=R):
    pieza = (cq.Workplane('XY').rect(ancho, alto).extrude(profundidad)
             .edges('|Z').fillet(radio).val().translate((0, 0, z0)))
    return montaje(pieza)


def perfil_brazo(espesor, z0, holgura=0, simple=False):
    """Silhueta del CAD V3 sin taladros; una rama es sólo un estudio del pitch."""
    if simple:
        from revision_R3 import perfil_simple
        return perfil_simple(espesor,z0,holgura)
    medido=CFG['pitch'].get('perfil_brazo_simple_local_xy_mm') if simple else None
    if medido:
        if len(medido)<3:raise ValueError('El perfil medido requiere tres puntos o más')
        perfil=cq.Workplane('XY').polyline(medido).close()
        if holgura:perfil=perfil.wires().toPending().offset2D(holgura)
        return perfil.extrude(espesor).val().translate((0,0,z0))
    largo = k3.BRAZO_L + 2*holgura
    w0, w1 = [a + 2*holgura for a in k3.BRAZO_ANCHO]
    xp = largo/2 - w1/2
    s = (cq.Workplane('XY').polyline([(-xp,-w1/2),(0,-w0/2),(xp,-w1/2),
         (xp,w1/2),(0,w0/2),(-xp,w1/2)]).close().extrude(espesor).val().translate((0,0,z0)))
    for signo in (-1, 1):
        s = s.fuse(cil(w1/2, espesor, (signo*xp,0,z0)))
    if simple:
        s = s.intersect(caja(0, largo, -largo, largo, z0-1, z0+espesor+1))
    return s.fuse(cil(k3.BRAZO_CUBO_D/2+holgura, espesor, (0,0,z0))).clean()


def inserto(forma, montaje, x, y, entrada, largo=4, sentido=1):
    """Alojamiento térmico provisional; nunca se crea rosca impresa ficticia."""
    p = CFG['insertos']
    origen = (x, y, entrada) if sentido > 0 else (x, y, entrada-largo-p['holgura_fondo_mm'])
    h = largo+p['holgura_fondo_mm']
    corte = cil(p['diametro_instalacion_mm']/2, h, origen)
    con = cq.Solid.makeCone(p['entrada_mm']/2, p['diametro_instalacion_mm']/2,
                           p['chaflan_entrada_mm'], cq.Vector(x,y,entrada), cq.Vector(0,0,sentido))
    return forma.cut(montaje(corte)).cut(montaje(con))


def cap_brazo(montaje, plano, fijaciones, forma='rectangular'):
    t = CFG['roll']['espesor_placa_retencion_mm']
    if forma == 'circular':
        s = cil(26.5, t, (0,0,plano-t))
    else:
        s = (cq.Workplane('XY').rect(54,36).extrude(t).edges('|Z').fillet(R)
             .val().translate((0,0,plano-t)))
    s = s.cut(cil(5.1, t+2, (0,0,plano-t-1)))
    for x,y in fijaciones:
        # El tornillo entra desde el interior de la pieza principal. Su cabeza
        # queda lejos del cuerpo del servo durante todo el giro.
        s = s.fuse(cil(4,3,(x,y,plano-t)))
        s = s.cut(cil(CFG['insertos']['diametro_instalacion_mm']/2,4,(x,y,plano-t-.5)))
    return montaje(s)


def alojamiento_cap(s,montaje,plano,fijaciones,asiento):
    for x,y in fijaciones:
        # Bolsillo para poste de retención y paso del M3 hacia él.
        s = s.cut(montaje(cil(4+H,2.1,(x,y,plano))))
        s = s.cut(montaje(cil(M3/2,asiento-plano+5,(x,y,plano))))
        # Reserva bajo la cabeza; el corte continúa al exterior cuando coincide
        # con el borde de un brazo de la cuna.
        s = s.cut(montaje(cil(3.2,10,(x,y,asiento))))
    return s


def adaptar_yaw():
    p = CFG['yaw']
    z0 = p['z_pedestales_mm']
    z1 = z0+p['espesor_adaptador_mm']
    s = g.rbox(70,68,z1-z0,(10,10,(z0+z1)/2),4)
    # Motor girado 90°; el cable sale hacia el corredor +Y, sin desplazar eje XY.
    s = s.cut(caja(-10-HS,10+HS,-10-HS,30+HS,z0-1,z1+1))
    for x,y in p['fijaciones_base_xy_mm']:
        s = s.cut(cil(M3/2,z1-z0+2,(x,y,z0-1)))
    # Orejas del RDS según clase Servo heredada, no patrón genérico V5.
    xc = v2.RDS3218.L/2-v2.RDS3218.a
    for a in (-1,1):
        for b in (-1,1):
            x, y = b*v2.RDS3218.hw/2, xc+a*v2.RDS3218.hs/2
            s = inserto(s, v2.Montaje((0,0,0),(0,0,1),(1,0,0)), x,y,z1,5,-1)
    # Dos anclajes para descargar el cable hacia el lado libre de los pedestales.
    for x in (-17,27):
        s = s.cut(g.box(2.2,7,z1-z0+2,x,34,(z0+z1)/2))
    return s.clean()


def horquilla(original):
    s = original.translate((0,0,DZ))
    # Sustituir el collar V5: el modelo de HS recuperado tiene otra altura de eje.
    s = s.cut(caja(-30,50,-160,-93.6,Z-38,Z+35))
    placa = caja(-23,43,HP.P[1],HP.P[1]+2*T,Z-28,Z+28)
    puente = caja(-23,43,HP.P[1],-90,Z-32,Z-28)
    s = s.fuse(placa).fuse(puente)
    ventana = v2.servo_ventana(v2.HS7955, z0=-1,z1=7)
    s = s.cut(HP(ventana))
    xc = v2.HS7955.L/2-v2.HS7955.a
    for sx in (-1,1):
        for sy in (-1,1):
            s = inserto(s,HP,xc+sx*v2.HS7955.hs/2,sy*v2.HS7955.hw/2,0,5,1)
    # Nuevo encastre de yaw: retira ranuras antiguas al rellenar sólo su región.
    base = 49+DZ
    relleno = caja(-22,22,-5,5,base,base+6)
    s = s.fuse(relleno)
    prof = perfil_brazo(k3.BRAZO_T+H,v2.RDS3218.S+1-k3.BRAZO_T,H)
    s = s.cut(HY(prof)).cut(cil(4.2,10,(0,0,base-1)))
    s = alojamiento_cap(s,HY,v2.RDS3218.S+1-k3.BRAZO_T,
                       [(-23,-10),(-23,10),(23,-10),(23,10)],20.5)
    return s.clean()


def cuna_pitch(original):
    s = original.translate((0,0,DZ))
    # Rellenar el acople doble de pitch y crear un alojamiento de una rama.
    s = s.fuse(cil(24.5,13,(0,-97.5,Z),(0,1,0)))
    s = s.cut(cil(4.2,16,(0,-99,Z),(0,1,0)))
    plano_pitch = v2.HS7955.S+1-CFG['brazos']['simple_espesor_mm']
    s = s.cut(HP(perfil_brazo(CFG['brazos']['simple_espesor_mm']+H,plano_pitch,H,True)))
    s = alojamiento_cap(s,HP,plano_pitch,CFG['roll']['fijaciones_pitch_xz_mm'],24.5)
    # Quitar el soporte antiguo de horn fijo para dar paso al cuerpo y a la tapa.
    s = s.cut(caja(-53,-46,-32,46,Z-21,Z+21))
    marco = caja(-61,-61+2*T,-38,52,Z-20,Z+20)
    marco = marco.cut(MR(v2.servo_ventana(v2.MG996R,z0=-1,z1=7)))
    s = s.fuse(marco)
    for ya,yb in ((-81,-32),(46,81)):
        s = s.fuse(caja(-61,-47,ya,yb,Z-16,Z+16))
    # Despejar el cuerpo por delante de las orejas y hasta el frontal del motor.
    s = s.cut(MR(v2.servo_ventana(v2.MG996R,z0=-1,z1=v2.MG996R.H-v2.MG996R.Fb+H)))
    xc = v2.MG996R.L/2-v2.MG996R.a
    for sx in (-1,1):
        for sy in (-1,1):
            s = inserto(s,MR,xc+sx*v2.MG996R.hs/2,sy*v2.MG996R.hw/2,0,5,1)
    # Revisión USB R1: conservar el eje y las bridas; compensar los dos
    # recortes inferiores agregando la misma altura por arriba de la traviesa.
    p = CFG['roll']
    s = s.fuse(caja(-61,-47,-81,81,Z+16,Z+16+p['suplemento_traviesa_superior_mm']))
    # Mantener el alivio del lado de la cabeza también en el suplemento: la
    # retención del horn de roll describe un arco por encima del eje.
    s = s.cut(caja(-53,-46,*p['apertura_traviesa_y_mm'],
                  Z-21,Z+16+p['suplemento_traviesa_superior_mm']+.1))
    for alivio in p['alivios_usb']:
        s = s.cut(cil(alivio['radio_mm'],16,
                      (-62,alivio['centro_y_mm'],Z+p['alivios_usb_centro_z_relativo_mm']),(1,0,0)))
    return s.clean()


def cuba_cabeza(original):
    s = original.translate((0,0,DZ))
    # El MG deja la cabeza. Se retiran sólo salientes interiores de su fijación.
    for y in (-14,34):
        s = s.cut(caja(-39.5,-35.9,y-3.1,y+3.1,Z-52,Z+11))
    # Boss de unión roll, encastre y retención desmontable, sin estriado impreso.
    plano_roll = v2.MG996R.S+1-k3.BRAZO_T
    boss = placa_plana(54,36,4.8,MR,plano_roll,R)
    s = s.fuse(boss)
    s = s.cut(MR(perfil_brazo(k3.BRAZO_T+H,plano_roll,H)))
    s = s.cut(cil(4.2,10,(-49,0,Z),(1,0,0)))
    s = alojamiento_cap(s,MR,plano_roll,CFG['roll']['fijaciones_retencion_yz_mm'],21.4)
    # Restaurar sólo la pared curva de las salidas V5. R2 sustituye la tapa
    # anterior y sus cuatro postes por una segunda abertura simétrica.
    u = CFG['usb']
    exterior=g.rbox(112,124,72,(14,0,Z-18),8)
    interior=g.rbox(107.2,119.2,76,(14,0,Z-13.6),5.6)
    pared=exterior.cut(interior).intersect(caja(-43,-39.5,24,59,Z-52,Z-27))
    s=s.fuse(pared)
    dz = u['paso_trasero_centro_yz_relativo_mm'][1]
    ancho,alto = u['paso_trasero_ancho_alto_mm']
    margen = u['paso_trasero_refuerzo_perimetral_mm']
    radio = u['paso_trasero_radio_esquina_mm']
    for y in u['centros_aberturas_y_mm']:
        m = v2.Montaje((-41, y, Z+dz),(1,0,0),(0,1,0))
        marco = placa_plana(ancho+2*margen,alto+2*margen,
                            1.4+u['paso_trasero_refuerzo_interior_mm'],m,0,radio+margen)
        s = s.fuse(marco).cut(placa_plana(ancho,alto,12,m,-5,radio))
    return s.clean()


def reserva_usb():
    """Corredor de diseño para estudiar giro; no representa un enchufe medido."""
    u=CFG['usb']
    return caja(*u['reserva_conector_x_mm'],*u['reserva_conector_y_mm'],
                Z+u['reserva_conector_z_relativa_mm'][0],
                Z+u['reserva_conector_z_relativa_mm'][1])


def agujero_buzzer_desde_bordes():
    b=CFG['buzzer'];r=b['agujero_diametro_mm']/2
    return tuple(d+r for d in b['borde_agujero_a_bordes_pcb_mm'])


def datos_buzzer():
    b=CFG['buzzer'];dy,dz=agujero_buzzer_desde_bordes()
    x=b['pcb_asiento_x_mm'];y=b['pcb_borde_y_mm'];z=Z+b['pcb_extremo_buzzer_z_relativo_mm']
    return x,y,z,y+dy,z+dz


def pcb_buzzer():
    b=CFG['buzzer'];x,y,z,hy,hz=datos_buzzer()
    return caja(x,x+b['pcb_espesor_mm'],y,y+b['pcb_ancho_mm'],z,z+b['pcb_largo_mm']).cut(
        cil(b['agujero_diametro_mm']/2,b['pcb_espesor_mm']+2,(x-1,hy,hz),(1,0,0)))


def cara(original):
    # Partir del frente V3 sin manguito del buzzer individual añadido en V4.
    s = original.translate((0,0,DZ))
    cam = CFG['camara']
    for y in (-10.5,10.5):
        for dz in (-12.4,.1):
            s = s.fuse(cil(cam['diametro_refuerzo_poste_mm']/2,3.44,(66.56,y,Z+dz),(1,0,0)))
            s = s.cut(cil(cam['diametro_paso_mm']/2,10,(65,y,Z+dz),(1,0,0)))
    s = s.cut(cil(cam['diametro_optico_existente_mm']/2,7,(68,0,Z),(1,0,0)))
    # Salida de sonido conserva la posición de boca V5; montaje de placa completo.
    z = Z+CFG['buzzer']['z_centro_relativo_mm']
    s = s.cut(cil(6,5,(69,0,z),(1,0,0)))
    for y in CFG['buzzer']['fijaciones_y_mm']:
        s = s.fuse(cil(4.5,7,(63,y,z),(1,0,0)))
        m = v2.Montaje((63,0,z),(1,0,0),(0,1,0))
        s = inserto(s,m,y,0,0,4,1)
    return s.clean()


def portamodulo():
    b = CFG['buzzer']
    x,y,z,hy,hz=datos_buzzer();a=b['pcb_ancho_mm'];l=b['pcb_largo_mm'];h=b['guia_holgura_por_lado_mm']
    esp=b['bastidor_espesor_mm'];fondo=x-b['separacion_inferior_componentes_mm']-esp
    # Bastidor abierto detrás del PCB, fuera del volumen de Pi/cámara.
    s=caja(fondo,fondo+esp,y-3,y+a+3,z-2,z+l+3)
    s=s.cut(caja(fondo-1,fondo+esp+1,y-.7,y+a+.7,z-.7,z+l+.7))
    s=s.fuse(caja(fondo,fondo+esp,y-3,y+a+3,hz-2,hz+2))
    s=s.fuse(cil(4,x-fondo,(fondo,hy,hz),(1,0,0)))
    m=v2.Montaje((x,0,0),(1,0,0),(0,1,0))
    s=inserto(s,m,hy,hz,0,3,-1)
    # Apoyos mínimos en los bordes; dejar libres los extremos de buzzer/pines.
    for za,zb in ((z+3,z+7),(z+l-9,z+l-5)):
        for ya,yb in ((y-1,y+1),(y+a-1,y+a+1)):
            s=s.fuse(caja(fondo+esp,x,ya,yb,za,zb))
        s=s.fuse(caja(fondo+esp,x+b['pcb_espesor_mm']+.5,y-1,y-h,za,zb))
        s=s.fuse(caja(fondo+esp,x+b['pcb_espesor_mm']+.5,y+a+h,y+a+1,za,zb))
    # Ala frontal y brazo lateral: reutilizan los dos postes existentes.
    zf=Z+b['z_centro_relativo_mm']
    s=s.fuse(caja(61,63,-29,y-h,zf-5,zf+5))
    s=s.fuse(caja(fondo,63,y-3,y-h,zf-4,zf+4))
    for yy in b['fijaciones_y_mm']:
        s=s.cut(cil(M3/2,4,(60,yy,zf),(1,0,0)))
    return s.clean()


def arandela_buzzer():
    b=CFG['buzzer'];x,y,z,hy,hz=datos_buzzer();x+=b['pcb_espesor_mm']
    alto=b['arandela_impresa_espesor_mm']
    return cil(3.5,alto,(x,hy,hz),(1,0,0)).cut(cil(M3/2,alto+2,(x-1,hy,hz),(1,0,0)))


def ojo_walle(lado):
    p=CFG['ojos'];signo=1 if lado>0 else -1
    puntos=[(signo*u,v) for u,v in p['contorno_local_uv_mm']]
    plano=cq.Plane(origin=(73,lado,Z+p['z_relativo_mm']),xDir=(0,1,0),normal=(1,0,0))
    cara=(cq.Workplane(plano).polyline(puntos).close().extrude(p['espesor_base_mm'])
          .edges('|X').fillet(p['radio_contorno_mm']).val())
    # Marco continuo y asiento ciego de la lente decorativa.
    ancho=p['ancho_marco_mm'];esp=p['espesor_base_mm']
    interior=(cq.Workplane(plano).polyline(puntos).close().wires().toPending()
              .offset2D(-ancho).extrude(esp+3).val())
    marco=cara.translate((p['relieve_marco_mm'],0,0)).cut(interior)
    s=cara.fuse(marco)
    centro=(73+esp-p['profundidad_alojamiento_mm'],lado,Z+p['z_relativo_mm'])
    s=s.cut(cil(p['alojamiento_lente_diametro_mm']/2,5,centro,(1,0,0)))
    for u,v in p['marcas_decorativas_uv_mm']:
        s=s.cut(cil(1.1,.65,(73+esp-.55,lado+signo*u,Z+p['z_relativo_mm']+v),(1,0,0)))
    return s.clean()


def lente_walle(lado):
    p=CFG['ojos'];r=p['lente_diametro_mm']/2
    x=73+p['espesor_base_mm']-p['profundidad_alojamiento_mm']
    centro=(x,lado,Z+p['z_relativo_mm'])
    s=cil(r,1.3,centro,(1,0,0))
    s=s.fuse(cil(r-1.6,1.8,centro,(1,0,0)))
    s=s.fuse(cil(r-3.1,p['relieve_lente_mm'],centro,(1,0,0)))
    return s.clean()


def cupon_insertos():
    s = g.rbox(65,16,7,(0,0,3.5),2)
    for i,d in enumerate(CFG['insertos']['diametros_cupon_mm']):
        x = -26+i*13
        s = s.cut(cil(d/2,5.6,(x,0,1.4)))
        s = s.cut(cq.Solid.makeCone(d/2,2.3,.4,cq.Vector(x,0,6.6)))
    return s.clean()


def transformar(s,yaw=0,pitch=0,roll=0,grupo='roll'):
    if grupo == 'roll': s = s.rotate(C,(1,0,Z),roll)
    if grupo in ('pitch','roll'): s = s.rotate(C,(0,1,Z),-pitch)
    if grupo != 'fixed': s = s.rotate((0,0,0),(0,0,1),yaw)
    return s


def construir():
    piezas = copy.deepcopy(v5.construir())
    # Capturar el frente base V3 de forma independiente y sin alterar originales.
    frente_v3 = next(p['shape'] for p in g.make() if p['name']=='06_cara_binocular')
    base_h = next(p['shape'] for p in piezas if p['name']=='02_horquilla_yaw')
    base_c = next(p['shape'] for p in piezas if p['name']=='03_cuna_pitch')
    base_t = next(p['shape'] for p in piezas if p['name']=='04_cuba_cabeza')
    cambios = {'02_horquilla_yaw':horquilla(base_h),'03_cuna_pitch':cuna_pitch(base_c),
               '04_cuba_cabeza':cuba_cabeza(base_t),'06_cara_binocular':cara(frente_v3)}
    eliminar = {'07_retencion_buzzer','REF_buzzer_12x9_6','REF_RDS3218','REF_Hitec_HS7955TG',
                'REF_MG996R_invertido','REF_horn_doble_yaw','REF_horn_doble_pitch','REF_horn_doble_roll_fijo'}
    salida = []
    for p in piezas:
        if p['name'] in eliminar or p['name'].startswith('GRAFICO_'): continue
        if p['name'] in cambios: p['shape'] = cambios[p['name']]
        elif p['group'] != 'fixed': p['shape'] = p['shape'].translate((0,0,DZ))
        if p['name']=='01_base': p['printed']=False; p['note']='REUTILIZAR V5; sin cambios geométricos'
        if p['name'] in ('05_tapa_ventilada','08_bandeja_electronica','09_retencion_esp32'):
            p['reutilizada']=True
        salida.append(p)
    def agregar(n,s,grupo,impresa=True,orient='normal',color=(.85,.65,.22),nota=''):
        salida.append(dict(name=n,shape=s,group=grupo,printed=impresa,orientation=orient,color=color,note=nota))
    agregar('10_adaptador_yaw',adaptar_yaw(),'fixed',nota='Gira cuerpo 90°, conserva eje XY; rosca de base y cable pendientes')
    agregar('11_retencion_horn_yaw',cap_brazo(HY,v2.RDS3218.S+1-k3.BRAZO_T,[(-23,-10),(-23,10),(23,-10),(23,10)]),'yaw')
    agregar('12_retencion_horn_pitch_simple',cap_brazo(HP,v2.HS7955.S+1-k3.BRAZO_T,CFG['roll']['fijaciones_pitch_xz_mm'],'circular'),'pitch',orient='pitch_cap_down',nota='Acople de estudio de una rama: perfil real pendiente')
    agregar('13_retencion_horn_roll',cap_brazo(MR,v2.MG996R.S+1-k3.BRAZO_T,CFG['roll']['fijaciones_retencion_yz_mm']),'roll',orient='face_down')
    agregar('15_soporte_RLBZ23',portamodulo(),'roll',orient='back_down',nota='PCB 13x31.8x1.5 medido; comprobar componentes/pines; requiere soportes bajo ala frontal')
    agregar('21_arandela_buzzer',arandela_buzzer(),'roll',orient='back_down',nota='Arandela aislante impresa para M3x5; no forzar el agujero real de PCB')
    for y in CFG['ojos']['centros_y_mm']:
        agregar('16_ojo_izq' if y>0 else '17_ojo_der',ojo_walle(y),'roll',orient='back_down',
                color=(.53,.55,.52),nota='Contorno WALL-E espejado, dorso plano adhesivo y lente aparte')
        agregar('19_lente_ojo_izq' if y>0 else '20_lente_ojo_der',lente_walle(y),'roll',orient='back_down',
                color=(.025,.07,.15),nota='Lente decorativa escalonada; pegar en asiento de ojo, no es lente óptica funcional')
    agregar('REF_RLBZ23_PCB',pcb_buzzer(),'roll',False,color=(.08,.27,.52),
            nota='Sólo PCB medido: faltan componentes, patas y cables; buzzer abajo, pines arriba')
    for n,s,grupo in [('REF_RDS3218',MY(v2.servo_modelo(v2.RDS3218)),'fixed'),
                       ('REF_HS7955TG',HP(v2.servo_modelo(v2.HS7955)),'yaw'),
                       ('REF_MG996R_exterior',MR(v2.servo_modelo(v2.MG996R)),'pitch'),
                       ('REF_horn_yaw',HY(k3.brazo_modelo(v2.RDS3218)),'yaw'),
                       ('REF_horn_roll',MR(k3.brazo_modelo(v2.MG996R)),'roll')]:
        agregar(n,s,grupo,False,color=(.2,.23,.25),nota='Referencia nominal heredada; medir unidad real')
    simple = k3.brazo_modelo(v2.HS7955)
    # Sólo ilustración de una rama. Nunca se atribuye esta forma al brazo físico.
    brazo = perfil_brazo(k3.BRAZO_T,v2.HS7955.S+1-k3.BRAZO_T,0,True)
    simple = (brazo.fuse(cil(4.5,10,(0,0,7))) if CFG['pitch'].get('perfil_brazo_simple_local_xy_mm')
              else simple.intersect(brazo.fuse(cil(4.5,10,(0,0,7)))))
    agregar('ESTUDIO_horn_pitch_simple_NO_MEDIDO',HP(simple),'pitch',False,color=(.8,.15,.15),nota='Sustituir perfil medido antes de fabricar')
    def tornillo(n,montaje,x,y,asiento,largo,grupo,hacia=1):
        d = (0,0,hacia)
        tallo = cil(1.5,largo,(x,y,asiento),d)
        cabeza = cil(CFG['tornillos']['cabeza_envolvente_d_mm']/2,
                     CFG['tornillos']['cabeza_envolvente_h_mm'],(x,y,asiento),(0,0,-hacia))
        agregar('REF_M3_'+n,montaje(tallo.fuse(cabeza)),grupo,False,color=(.55,.58,.62),nota=f'M3x{largo}; cabeza envolvente provisional')
    for nombre,mont,asiento,largo,xy,grupo in [
        ('ret_yaw',HY,20.5,6,[(-23,-10),(-23,10),(23,-10),(23,10)],'yaw'),
        ('ret_pitch',HP,24.5,12,CFG['roll']['fijaciones_pitch_xz_mm'],'pitch'),
        ('ret_roll',MR,21.4,8,CFG['roll']['fijaciones_retencion_yz_mm'],'roll')]:
        for i,(x,y) in enumerate(xy): tornillo(f'{nombre}_{i}',mont,x,y,asiento,largo,grupo,-1)
    for nombre,mont,servo,grupo in [('yaw',MY,v2.RDS3218,'fixed'),('pitch',HP,v2.HS7955,'yaw'),('roll',MR,v2.MG996R,'pitch')]:
        xc=servo.L/2-servo.a
        for i,(sx,sy) in enumerate(((-1,-1),(-1,1),(1,-1),(1,1))):
            tornillo(f'servo_{nombre}_{i}',mont,xc+sx*servo.hs/2,sy*servo.hw/2,
                     0 if nombre=='yaw' else -servo.tf,CFG['tornillos']['largo_fijacion_servo_mm'],grupo,-1 if nombre=='yaw' else 1)
    x,y,z,hy,hz=datos_buzzer();b=CFG['buzzer']
    mb_pcb=v2.Montaje((x+b['pcb_espesor_mm']+b['arandela_impresa_espesor_mm'],0,0),(1,0,0),(0,1,0))
    tornillo('buzzer_PCB',mb_pcb,hy,hz,0,5,'roll',-1)
    mb=v2.Montaje((61,0,Z+CFG['buzzer']['z_centro_relativo_mm']),(1,0,0),(0,1,0))
    for i,y in enumerate(CFG['buzzer']['fijaciones_y_mm']): tornillo(f'portamodulo_{i}',mb,y,0,0,6,'roll')
    from revision_R3 import aplicar
    return aplicar(salida,globals())


def pose_impresion(s,orientacion):
    if orientacion in ('pitch_cap_down','back_down'):
        s=(s.rotate((0,0,0),(1,0,0),90) if orientacion=='pitch_cap_down'
           else s.rotate((0,0,0),(0,1,0),-90))
        bb=s.BoundingBox()
        return s.translate((-(bb.xmin+bb.xmax)/2,-(bb.ymin+bb.ymax)/2,-bb.zmin))
    return g.print_pose(s,orientacion)


def exportar(piezas):
    for carpeta in ('STEP_V6','STL_REVISION_NO_IMPRIMIR','evidencias','vistas'):
        (RAIZ/carpeta).mkdir(exist_ok=True)
    conjunto = cq.Assembly(name='Keepon_V6_nominal')
    grupos = {k:[] for k in ('fixed','yaw','pitch','roll')}
    inventario,cuerpos,mallas = [],[],[]
    for p in piezas:
        s = p['shape']
        if not s.isValid() or (p['printed'] and len(s.Solids())!=1):
            raise ValueError(f"{p['name']}: válido={s.isValid()}, sólidos={len(s.Solids())}")
        conjunto.add(s,name=p['name'],color=cq.Color(*p['color']))
        grupos[p['group']].append(s)
        for b in s.Solids():
            bb=b.BoundingBox()
            cuerpos.append({'nombre':p['name'],'grupo':p['group'],'color':p['color'],
                'caja_mm':[bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax]})
        if p['printed']:
            cq.exporters.export(s,str(RAIZ/'STEP_V6'/f"{p['name']}.step"))
            ip=pose_impresion(s,p['orientation']);bb=ip.BoundingBox()
            cq.exporters.export(ip,str(RAIZ/'STL_REVISION_NO_IMPRIMIR'/f"{p['name']}.stl"),
                                tolerance=CFG['impresion']['tolerancia_malla_mm'],angularTolerance=.12)
            if p['name'].startswith(('16_','17_','19_','20_')):
                cq.exporters.export(ip,str(RAIZ/'IMPRESION_STL'/f"{p['name']}.stl"),
                                    tolerance=CFG['impresion']['tolerancia_malla_mm'],angularTolerance=.12)
            inventario.append({'nombre':p['name'],'grupo':p['group'],'reutilizar':p.get('reutilizada',False),
                'caja_impresion_mm':[bb.xlen,bb.ylen,bb.zlen],'volumen_mm3':s.Volume(),'nota':p['note'],
                'estado':'REVISAR MEDIDAS Y MATERIAL'})
        vs,fs=s.tessellate(.5,.16)
        mallas.append({'name':p['name'],'group':p['group'],'color':p['color'],'printed':p['printed'],
                       'v':[[v.x,v.y,v.z] for v in vs],'f':fs})
        print('EXPORTADO',p['name'],flush=True)
    conjunto.export(str(RAIZ/'STEP_V6/00_ensamble_V6_nominal.step'))
    volumenes={}
    for n,ss in grupos.items():
        grupo=cq.Compound.makeCompound(ss)
        cq.exporters.export(grupo,str(RAIZ/'STEP_V6'/f'v6_grupo_{n}.step'))
        volumenes[n]={'volumen_mm3':grupo.Volume(),'solidos':len(grupo.Solids())}
    (RAIZ/'evidencias/volumenes_grupos_v6.json').write_text(json.dumps(volumenes,indent=2),encoding='utf-8')
    cq.exporters.export(cupon_insertos(),str(RAIZ/'STEP_V6/18_cupon_insertos.step'))
    cq.exporters.export(cupon_insertos(),str(RAIZ/'IMPRESION_STL/18_cupon_insertos.stl'))
    for n,d in [('inventario_v6.json',inventario),('mallas_v6.json',mallas),('evidencias/cuerpos_v6.json',cuerpos)]:
        (RAIZ/n).write_text(json.dumps(d,ensure_ascii=False),encoding='utf-8')
    origenes=[RAIZ/'config.yaml',RAIZ/'generar_v6.py',RAIZ/'revision_R3.py',RAIZ.parent/'diseno_v5/generar_v5.py',
              REPO/'docs/keepon_v2_cad/fuente/keepon_cad.py',REPO/'docs/keepon_v3_cad/fuente/keepon_v3_cad.py']
    (RAIZ/'evidencias/trazabilidad_v6.json').write_text(json.dumps({
        'revision':CFG.get('revision','inicial'),
        'sha256':{str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in origenes},
        'z_eje_pitch_roll_mm':Z,'elevacion_conjunto_mm':DZ,'base_original_modificada':True,
        'fabricacion_liberada':False,'faltantes':['Estriados/cubos reales y ancho/espesor brazo doble','Componentes/pines y transductor RLBZ23','Tornillería del disco','USB','Material/insertos','Insertos de base','Cables reales']},indent=2),encoding='utf-8')
    print('V6 NOMINAL EXPORTADA; fabricación condicionada.',flush=True)


if __name__=='__main__':
    exportar(construir())
