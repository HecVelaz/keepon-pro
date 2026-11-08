"""Comprueba colisiones del prototipo contra referencias nominales V5.

Nueve poses de pitch/roll; no prueba cableado, tornillos ni movimiento continuo.
El cuerpo del servo se monta ahora en el grupo pitch. Se excluye su horn porque
la geometría y posición reales para el montaje nuevo aún no se han definido.
"""
from pathlib import Path
import importlib.util
import itertools
import json
import cadquery as cq

RAIZ = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('v5', RAIZ.parent / 'diseno_v5/generar_v5.py')
v5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v5)
spec6 = importlib.util.spec_from_file_location('prototipo', RAIZ / 'generar_roll_exterior.py')
v6 = importlib.util.module_from_spec(spec6)
spec6.loader.exec_module(v6)


def volumen(a, b):
    aa, bb = a.BoundingBox(), b.BoundingBox()
    if any((getattr(aa, eje+'max') <= getattr(bb, eje+'min') or
            getattr(bb, eje+'max') <= getattr(aa, eje+'min')) for eje in 'xyz'):
        return 0.0
    return max(0.0, a.intersect(b).Volume())


def main():
    piezas = v5.construir()
    cuna, cuba, motor = v6.construir()
    piezas = [p for p in piezas if p['name'] not in ('REF_MG996R_invertido', 'REF_horn_doble_roll_fijo')
              and not p['name'].startswith('GRAFICO_')]
    next(p for p in piezas if p['name'] == '03_cuna_pitch')['shape'] = cuna
    next(p for p in piezas if p['name'] == '04_cuba_cabeza')['shape'] = cuba
    piezas.append({'name': 'MG996R_exterior_nominal', 'shape': motor, 'group': 'pitch'})
    conjunto = cq.Assembly(name='V6_estudio_incompleto')
    for pieza in piezas:
        # La referencia de pitch de V5 es doble y contradice el brazo real.
        if pieza['name'] != 'REF_horn_doble_pitch':
            conjunto.add(pieza['shape'], name=pieza['name'])
    conjunto.export(str(RAIZ / 'PRELIMINAR/robot_estudio_incompleto.step'))
    nuevos = {'03_cuna_pitch', '04_cuba_cabeza', 'MG996R_exterior_nominal'}
    ignoradas = {frozenset(('MG996R_exterior_nominal', '03_cuna_pitch'))}
    resultados = []
    for pitch, roll in itertools.product((-20, 0, 30), (-20, 0, 20)):
        actuales = [(p, v5.g.transform(p['shape'], 0, pitch, roll, p['group'])) for p in piezas]
        choques = []
        for (a, sa), (b, sb) in itertools.combinations(actuales, 2):
            if not ({a['name'], b['name']} & nuevos) or frozenset((a['name'], b['name'])) in ignoradas:
                continue
            inter = volumen(sa, sb)
            if inter > .1:
                choques.append({'a': a['name'], 'b': b['name'], 'volumen_mm3': round(inter, 3)})
        resultados.append({'pitch': pitch, 'roll': roll, 'interferencias': choques})
        print('pitch', pitch, 'roll', roll, 'choques', len(choques), flush=True)
    informe = {'poses': resultados, 'total_poses': len(resultados),
               'con_interferencias': sum(bool(p['interferencias']) for p in resultados),
               'alcance': 'Referencias V5 simplificadas; nueve poses, yaw=0; no se representa horn roll, cables ni tornillos.',
               'apto_para_fabricar': False}
    (RAIZ / 'PRELIMINAR/barrido.json').write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Poses con interferencias:', informe['con_interferencias'], flush=True)


if __name__ == '__main__':
    main()
