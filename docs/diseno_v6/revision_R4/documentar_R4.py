"""Tabla de interfaces R4: cotas activas, separadas de la configuración heredada."""
from pathlib import Path
import csv,json,yaml
R=Path(__file__).parent
c=yaml.safe_load((R/'config.yaml').read_text(encoding='utf-8'));z=json.loads((R/'evidencias/trazabilidad_v6.json').read_text(encoding='utf-8'))['z_eje_pitch_roll_mm'];filas=[]
def agregar(pieza,uso,eje,d,centro,inicio,fin,nota=''):
    filas.append([pieza,uso,eje,d,*centro,inicio,fin,nota])
for x,y in c['yaw']['fijaciones_base_xy_mm']:
    agregar('Soporte_servo_base','Paso M3 centrado en pilar','Z',3.4,(x,y,0),38,44)
    agregar('Base_con_pilares','Alojamiento inserto M3 L5','Z',4,(x,y,0),31.4,38,'Diámetro de inserto provisional')
p=c['raspberry'];base=z+p['z_base_relativo_mm']
for x,y in p['postes_xy_mm']:agregar('Carcasa_cabeza','Piloto Pi','Z',p['piloto_mm'],(x,y,0),base,base+p['altura_poste_mm'],'Poste Ø9×8')
b=c['brazos'];mz=c['roll']['x_brida_mm']
for yy,dz in ((7,0),(0,7),(-7,0),(0,-7)):
    agregar('Disco_comercial_25T','Cuatro agujeros Ø3 a R7','X',3,(0,yy,z+dz),-45.55,-43.1,'Centros opuestos14; espesor de disco2.45')
    agregar('Carcasa_cabeza','Paso M3 coincidente con disco','X',3.4,(0,yy,z+dz),-46.55,-30.55,'Pasante; límites de herramienta de corte')
agregar('Disco_comercial_25T','Paso central de tornillo','X',3,(0,0,z),-47.6,-43.1,'CuboØ9; altura total4.5. Cavidad25T nominal aparte.')
agregar('Carcasa_cabeza','Acceso central herramienta roll','X',8.4,(0,0,z),-46.55,-28.55)
agregar('Cuna_inclinacion','Acceso pasante tornillo pitch','Y',8.4,(0,0,z),-99.5,90.1,'Retirar casquillo22 y pivoteM4 para acceder de extremo a extremo')
p=c['buzzer'];m=p['montaje_R4'];yy=m['pcb_y_inicial_mm']+p['agujero_desde_extremo_buzzer_mm'];zz=z+m['pcb_z_centro_relativo_mm']-p['pcb_ancho_mm']/2+m['agujero_desde_borde_ancho_mm'];x=m['pcb_x_mm'];xf=x+p['pcb_espesor_mm']
agregar('PCB_buzzer','Agujero de fijación M3','X',3,(0,yy,zz),x,xf,'Centro14.8 desde extremo buzzer; transversal6.3 conservada de medición anterior')
agregar('Cara_integrada','Piloto ciego fijación buzzer','X',m['piloto_directo_m3_mm'],(0,yy,zz),xf,xf+m['profundidad_piloto_mm'],'Un M3×5 desde atrás; puntaX63.5; frenteX73')
with (R/'interfaces_R4.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['pieza','uso','eje','diametro_mm','centro_x_mm','centro_y_mm','centro_z_mm','inicio_eje_mm','fin_eje_mm','nota']);w.writerows(filas)
print(len(filas),'interfaces R4 documentadas')
