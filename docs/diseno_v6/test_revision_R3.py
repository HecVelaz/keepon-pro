"""Regresiones de entrega R3: no confundir ensamblaje antiguo con nueva revisión."""
import json,math
from pathlib import Path
import cadquery as cq
import yaml
R=Path(__file__).parent

def test_cotas_de_referencia():
    c=yaml.safe_load((R/'config.yaml').read_text(encoding='utf-8'));b=c['brazos']
    assert b['circular_servo']=='roll'
    assert b['doble_longitud_mm']==37.7
    assert b['simple_longitud_mm']==26.4 and b['simple_espesor_mm']==2.8
    assert b['simple_diametros_extremos_mm']==[6.2,9.2]
    assert b['circular_diametro_mm']==20 and b['circular_espesor_mm']==2.6
    assert abs(b['circular_radio_agujeros_mm']*math.sqrt(2)-7)<.08

def test_regresiones_geometricas_y_barrido():
    d=json.loads((R/'evidencias/regresiones_R3.json').read_text(encoding='utf-8'))
    assert len(d['pruebas'])>=34 and all(d['pruebas'].values())
    b=json.loads((R/'evidencias/barrido_R3.json').read_text(encoding='utf-8'))
    assert b['aprobado_nominal'] and b['poses_representadas']==45
    assert not b['interferencias_home']
    assert not any(p['interferencias'] for p in b['poses'])

def test_cara_step_monopieza_sin_ojos_sueltos():
    s=cq.importers.importStep(str(R/'STEP_V6/06_cara_con_ojos_integrados.step')).val()
    assert s.isValid() and len(s.Solids())==1
    assert not any(p.name.startswith(('16_','17_','19_','20_')) for p in (R/'STEP_V6').iterdir())

def test_nombres_de_cuerpos_en_espanol():
    cuerpos=json.loads((R/'evidencias/cuerpos_v6.json').read_text(encoding='utf-8'))
    assert not any(any(p in b['nombre'] for p in ('Open CASCADE','horn','ESTUDIO_','REF_')) for b in cuerpos)
    assert any(b['nombre']=='Referencia_disco_balanceo' for b in cuerpos)

if __name__=='__main__':
    pruebas=[v for n,v in list(globals().items()) if n.startswith('test_') and callable(v)]
    for prueba in pruebas:
        prueba();print(prueba.__name__,'OK',flush=True)
    print(len(pruebas),'pruebas de regresión de entrega aprobadas')
