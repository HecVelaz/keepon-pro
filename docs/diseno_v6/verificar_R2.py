"""Consolida cotas del PCB y geometrías nuevas sin validar componentes ausentes."""
from pathlib import Path
import json
import cadquery as cq
import generar_v6 as v6

R=Path(__file__).resolve().parent


def main():
    inventario=json.loads((R/'inventario_v6.json').read_text(encoding='utf-8'))
    nombres=[p['nombre'] for p in inventario]
    pcb=v6.pcb_buzzer();bb=pcb.BoundingBox();x,y,z,hy,hz=v6.datos_buzzer()
    ojos=[cq.importers.importStep(str(R/'STEP_V6'/(n+'.step'))).val() for n in ('16_ojo_izq','17_ojo_der')]
    error_espejo=ojos[0].mirror('XZ').cut(ojos[1]).Volume()+ojos[1].cut(ojos[0].mirror('XZ')).Volume()
    cq.exporters.export(pcb,str(R/'evidencias/RLBZ23_PCB_MEDIDO.step'))
    resultado={'revision':v6.CFG['revision'],'PCB_medido_mm':[bb.ylen,bb.zlen,bb.xlen],
        'agujero_diametro_mm':v6.CFG['buzzer']['agujero_diametro_mm'],
        'centro_agujero_desde_bordes_mm':list(v6.agujero_buzzer_desde_bordes()),
        'asiento_PCB_x_mm':x,'extremo_buzzer_yz_mm':[y,z],'centro_agujero_yz_mm':[hy,hz],
        'tapa14_ausente':not any(n.startswith('14_') for n in nombres),
        'error_espejo_ojos_mm3':error_espejo,'piezas_revision':len(nombres),
        'nativos_individuales_esperados':len(nombres)+1,
        'M3_PCB':'Uno M3x5 con arandela impresa de0.8 e inserto L3',
        'enganche_nominal_M3_PCB_mm':2.7,'margen_fondo_M3_PCB_mm':.9,
        'faltantes_modulo':['Altura y contorno de buzzer/componentes en ambas caras','Patas y enchufe GND/I-O/VCC insertado','Zona libre alrededor del agujero'],
        'limite':'No se modelan ni se atribuyen alturas a los componentes ausentes; comprobar el PCB real montado antes de liberar su soporte.'}
    resultado['aprobado_geometria_R2']=resultado['tapa14_ausente'] and error_espejo<.01 and pcb.isValid()
    (R/'evidencias/R2_buzzer_ojos.json').write_text(json.dumps(resultado,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(resultado,ensure_ascii=False))
    assert resultado['aprobado_geometria_R2']


if __name__=='__main__':main()
