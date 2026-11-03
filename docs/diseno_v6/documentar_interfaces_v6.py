"""Tablas de uniones, agujeros y cotas derivadas de la configuración V6."""
from pathlib import Path
import csv
import json
import yaml

RAIZ=Path(__file__).resolve().parent
cfg=yaml.safe_load((RAIZ/'config.yaml').read_text(encoding='utf-8'))
tr=json.loads((RAIZ/'evidencias/trazabilidad_v6.json').read_text(encoding='utf-8'))
z=tr['z_eje_pitch_roll_mm']
diametro_inserto=cfg['insertos']['diametro_instalacion_mm']
paso_m3=cfg['tornillos']['paso_m3_mm']
salida=RAIZ/'documentacion';salida.mkdir(exist_ok=True)
filas=[]
def agregar(pieza,uso,n,diam,eje,centros,profundo,estado):
    filas.append(dict(pieza=pieza,uso=uso,cantidad=n,diametro_mm=diam,eje=eje,centros_mm=centros,profundidad_mm=profundo,estado=estado))
agregar('10_adaptador_yaw','Base existente',4,paso_m3,'Z',str(cfg['yaw']['fijaciones_base_xy_mm']),'Pasante 6','Confirmar rosca existente; base sin modificar')
agregar('10_adaptador_yaw','RDS3218 girado',4,diametro_inserto,'Z',str([(x,y) for x in (-5,5) for y in (-14.75,34.75)]),5.6,'Inserto L5; diámetro provisional')
agregar('02_horquilla_yaw','HS7955TG',4,diametro_inserto,'Y',str([(x,z+d) for x in (-14,34) for d in (-5,5)]),5.6,'Inserto L5; diámetro provisional')
agregar('03_cuna_pitch','MG996R',4,diametro_inserto,'X',str([(y,z+d) for y in (-14.4,35.1) for d in (-5,5)]),5.6,'Inserto L5; diámetro provisional')
for pieza,cap,plano,asiento,coords in [
    ('02_horquilla_yaw','11_retencion_horn_yaw',15.5,20.5,[(-23,-10),(-23,10),(23,-10),(23,10)]),
    ('03_cuna_pitch','12_retencion_horn_pitch_simple',13.5,24.5,cfg['roll']['fijaciones_pitch_xz_mm']),
    ('04_cuba_cabeza','13_retencion_horn_roll',14.5,21.4,cfg['roll']['fijaciones_retencion_yz_mm'])]:
    agregar(cap,'Inserto en poste de retención',4,diametro_inserto,'Local Z',str(coords),3,'Pasante; inserto L3, diámetro provisional')
    agregar(pieza,'Paso tornillo de retención',4,paso_m3,'Local Z',str(coords),'Pasante','Medir cabeza M3; cilindro de reserva Ø6.4')
    agregar(pieza,'Alojamiento poste de retención',4,8.5,'Local Z',str(coords),2.1,'Holgura provisional')
agregar('06_cara_binocular','Cámara',4,2.2,'X',str([(y,z+d) for y in (-10.5,10.5) for d in (-12.4,.1)]),'Pasante','Patrón oficial 21x12.5; M2 y tuerca por confirmar')
agregar('06_cara_binocular','Portamódulo',2,diametro_inserto,'X',str([(y,z-28) for y in cfg['buzzer']['fijaciones_y_mm']]),4.6,'Inserto L4; diámetro provisional')
agregar('15_soporte_RLBZ23','Montaje en cara',2,paso_m3,'X',str([(y,z-28) for y in cfg['buzzer']['fijaciones_y_mm']]),2,'Pasante')
b=cfg['buzzer'];dy,dz=[d+b['agujero_diametro_mm']/2 for d in b['borde_agujero_a_bordes_pcb_mm']]
hy=b['pcb_borde_y_mm']+dy;hz=z+b['pcb_extremo_buzzer_z_relativo_mm']+dz
agregar('REF_RLBZ23_PCB','Agujero físico de PCB',1,b['agujero_diametro_mm'],'X',str([(hy,hz)]),b['pcb_espesor_mm'],'Cotas aportadas; comprobar paso M3 sin forzar PCB')
agregar('15_soporte_RLBZ23','Inserto de fijación PCB',1,diametro_inserto,'X',str([(hy,hz)]),3.6,'Inserto L3; diámetro provisional; M3x5 con arandela impresa')
agregar('21_arandela_buzzer','Paso M3',1,paso_m3,'X',str([(hy,hz)]),b['arandela_impresa_espesor_mm'],'Arandela aislante impresa Ø7')
with (salida/'agujeros_v6.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(filas[0]));w.writeheader();w.writerows(filas)
uniones=[
    ('Adaptador a base',4,12,None,6,None,'Rosca impresa existente pendiente; nunca forzar ni perforar base'),
    ('RDS3218 a adaptador',4,6,5,2.5,2.1,'M3 entra desde cara superior de brida; enganche 3.5'),
    ('HS7955TG a horquilla',4,6,5,2.5,2.1,'Cabeza detrás de brida; enganche 3.5'),
    ('MG996R a cuna',4,6,5,2.5,2.1,'Cabeza detrás de brida, motor exterior; enganche 3.5'),
    ('Retención yaw',4,6,3,3.2,.2,'Cabeza desde arriba del plato'),
    ('Retención pitch',4,12,3,9.2,.2,'Cabeza desde interior de cuna'),
    ('Retención roll',4,8,3,5.1,.1,'Cabeza desde interior de cabeza'),
    ('Soporte RLBZ23 a cara',2,6,4,2,.6,'Reutiliza los dos postes de cara'),
    ('PCB a soporte RLBZ23',1,5,3,2.3,.9,'PCB 1.5 + arandela impresa 0.8; enganche nominal 2.7; comprobar zona libre y paso M3')]
with (salida/'uniones_v6.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['union','cantidad','M3_largo_mm','inserto_largo_mm','distancia_hasta_entrada_mm','margen_axial_nominal_mm','nota']);w.writerows(uniones)
texto=f'''# Interfaces nominales V6

Origen en el eje yaw, piso Z=0. +X hacia la cara, +Y izquierda del robot.
El eje pitch/roll queda en (0,0,{z:g}) mm. Elevación del conjunto respecto
a V5: {tr['elevacion_conjunto_mm']:g} mm. La base conserva su geometría.

- Adaptador: 70 × 68 × 6, R4, centro XY=(10,10), Z=38…44.
- Brida yaw: cara superior Z=46,5; cuerpo girado +90° alrededor de Z.
- Horquilla: geometría V5 trasladada y nuevo collar HS; bolsillo doble nominal
  de 38 mm, cubo Ø9, rama de 2,5, anchos 6,5/4, con 0,25 mm por lado.
- Cuna: hub pitch Ø49 con paso Ø8,4; tapa Ø53. El bolsillo simple es un estudio
  de una rama, no la medición del brazo. Plano de orejas MG: X=−61.
- Cuba: boss de roll 54 × 36 × 4,8; bolsillo doble nominal y paso Ø8,4.
- R2: dos pasos posteriores iguales de 36 × 26, esquinas R3; centros Y=±35,
  Z={z-36:g}. La tapa14 y sus cuatro M3/postes ya no forman parte del modelo.
  Refuerzos interiores de 1,6, margen perimetral de4. Cotas de diseño,
  conectores sin medir; reserva USB evaluada del lado Y negativo.
- Traviesa roll R1: alivios R26 en Y=−49 y R20 en Y=57, ambos en
  Z={z-16:g}; suplemento superior de26 hasta Z={z+42:g}. Eje y fijaciones
  MG996R conservados; ver REVISION_USB_R1.md y ranuras_USB_R1.csv.
- Cámara: cuatro pasos Ø2,2; centro óptico Y=0,Z={z:g}; ventana Ø17 existente.
  Refuerzo de postes Ø6. El paso elimina el autorroscado anterior: requiere
  M2 pasante con tuerca o una retención alternativa comprobada.
- PCB RLBZ23 medido: 13 × 31,8 × 1,5; X=48,5…50, Y=35…48,
  Z={z-39:g}…{z-7.2:g}. Buzzer en extremo inferior; pines en superior.
  Agujero Ø3, centro Y={hy:g}, Z={hz:g}; desde bordes: ancho6,3, largo16,4
  desde extremo del buzzer. Montaje M3×5, inserto L3 y arandela impresa0,8.
  Bastidor abierto con3 mm de reserva bajo PCB: capacidad de diseño, no
  altura atribuida a los componentes. Faltan alturas/pines y zona libre Ø8.
- Ojos WALL-E: carcasas16/17 espejadas, dorso plano X=73, base2 y marco0,8;
  centros Y=±30, Z={z+22:g}. Lentes19/20 Ø27,8, asientoØ28,4, profundidad0,8;
  relieve2,2. Contorno y detalles en config.yaml. MarcasØ2,2 decorativas,
  no requieren tornillos ni perforar la cara.
- Cupón: 65 × 16 × 7, R2, agujeros de izquierda a derecha 3,7/3,8/3,9/4,0/4,1;
  centros X=−26,−13,0,13,26, Y=0; profundidad5,6; usar inserto de5 mm.

Las tablas CSV complementan los STEP y el código, en mm. Los valores de
alojamiento y cabeza deben medirse/calibrarse antes de fabricar. Las cotas
heredadas de las piezas reutilizadas siguen en la documentación V5.
'''
(salida/'INTERFACES.md').write_text(texto,encoding='utf-8')
u=cfg['usb'];fila_paso={'pieza':'04_cuba_cabeza','geometria':'Rectángulo redondeado pasante',
    'centro_y_mm':u['paso_trasero_centro_yz_relativo_mm'][0],
    'centro_z_mm':z+u['paso_trasero_centro_yz_relativo_mm'][1],
    'ancho_y_mm':u['paso_trasero_ancho_alto_mm'][0],'alto_z_mm':u['paso_trasero_ancho_alto_mm'][1],
    'radio_mm':u['paso_trasero_radio_esquina_mm'],'direccion':'X',
    'estado':'Capacidad de diseño; medir conector'}
ranuras=[dict(fila_paso,centro_y_mm=y) for y in cfg['usb']['centros_aberturas_y_mm']]
for alivio in cfg['roll']['alivios_usb']:
    ranuras.append({'pieza':'03_cuna_pitch','geometria':'Alivio semicircular abierto inferior',
        'centro_y_mm':alivio['centro_y_mm'],'centro_z_mm':z+cfg['roll']['alivios_usb_centro_z_relativo_mm'],
        'ancho_y_mm':2*alivio['radio_mm'],'alto_z_mm':alivio['radio_mm'],
        'radio_mm':alivio['radio_mm'],'direccion':'X','estado':'Sin cambio de eje ni agujeros MG996R'})
with (salida/'ranuras_USB_R2.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(fila_paso));w.writeheader();w.writerows(ranuras)
print('Tablas de agujeros y uniones V6 generadas.')
