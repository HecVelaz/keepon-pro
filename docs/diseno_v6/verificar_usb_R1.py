"""Comprueba el paso y una reserva USB de diseño, sin atribuirla al cable real."""
from pathlib import Path
import json
import tempfile
import zipfile
import cadquery as cq
import generar_v6 as v6
from auditar_v6 import interseccion

R=Path(__file__).resolve().parent


def main():
    soporte=cq.importers.importStep(str(R/'STEP_V6/03_cuna_pitch.step')).val()
    cuba=cq.importers.importStep(str(R/'STEP_V6/04_cuba_cabeza.step')).val()
    reserva=v6.reserva_usb()
    # El archivo anterior sólo se utiliza para contrastar la interferencia que
    # motivó la revisión. Nunca se altera la pieza de referencia del respaldo.
    with zipfile.ZipFile(R/'HISTORIAL/Keepon_V6_antes_USB_R1.zip') as z:
        with tempfile.TemporaryDirectory(prefix='keepon_usb_') as d:
            p=Path(d)/'03_anterior.step'
            p.write_bytes(z.read('diseno_v6/STEP_V6/03_cuna_pitch.step'))
            anterior=cq.importers.importStep(str(p)).val()
    poses=[]
    for roll in range(-20,21):
        movida=v6.transformar(reserva,roll=roll)
        poses.append({'roll_grados':roll,
            'volumen_reserva_soporte_anterior_mm3':interseccion(movida,anterior),
            'volumen_reserva_soporte_R1_mm3':interseccion(movida,soporte),
            'distancia_reserva_soporte_R1_mm':soporte.distance(movida)})
    resultado={'revision':v6.CFG.get('revision','USB_R1'),'lado_evaluado':'Y negativo: salida USB anterior de diseño',
        'reserva_es_medida_fisica':False,
        'reserva_xyz_mm':{'x':v6.CFG['usb']['reserva_conector_x_mm'],
                         'y':v6.CFG['usb']['reserva_conector_y_mm'],
                         'z_relativo_eje_roll':v6.CFG['usb']['reserva_conector_z_relativa_mm']},
        'poses':poses,'volumen_reserva_cuba_home_mm3':interseccion(reserva,cuba),
        'holgura_minima_muestreada_mm':min(p['distancia_reserva_soporte_R1_mm'] for p in poses),
        'choque_anterior_reproducido':any(p['volumen_reserva_soporte_anterior_mm3']>.1 for p in poses),
        'aprobado_reserva':not any(p['volumen_reserva_soporte_R1_mm3']>.01 for p in poses) and interseccion(reserva,cuba)<.01,
        'limites':['Reserva de espacio elegida para diseño, no geometría del USB comprado',
                   'Giro roll discreto de 1°; pitch y yaw comunes a cuna/cabeza no alteran esta holgura relativa',
                   'No verifica radio ni recorrido del cable flexible ni el conector real']}
    (R/'evidencias/USB_R1.json').write_text(json.dumps(resultado,indent=2,ensure_ascii=False),encoding='utf-8')
    cq.exporters.export(reserva,str(R/'evidencias/RESERVA_USB_R1_NO_MEDIDA.step'))
    print(json.dumps({k:v for k,v in resultado.items() if k!='poses'},ensure_ascii=False),flush=True)
    assert resultado['aprobado_reserva'],'La reserva USB todavía interfiere'


if __name__=='__main__':main()
