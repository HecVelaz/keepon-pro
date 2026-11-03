"""Prototipo de roll exterior sobre las piezas V5. NO LISTO PARA IMPRIMIR.

Los cortes son nominales y se mantienen identificados: faltan horn real,
conectores, tornillos, inserto y carga. Se exporta sólo a PRELIMINAR.
"""
from pathlib import Path
import importlib.util
import json
import cadquery as cq
import yaml
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

RAIZ = Path(__file__).resolve().parent
CFG = yaml.safe_load((RAIZ / 'config_prototipo.yaml').read_text(encoding='utf-8'))
BASE = RAIZ.parent / 'diseno_v5'
SALIDA = RAIZ / 'PRELIMINAR'


def caja(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def cilindro_x(radio, largo, x, y, z):
    return cq.Solid.makeCylinder(radio, largo, cq.Vector(x, y, z), cq.Vector(1, 0, 0))


def cargar(nombre):
    return cq.importers.importStep(str(BASE / 'STEP' / (nombre + '.step'))).val()


def construir():
    p = CFG['roll']
    z = p['z_centro']
    cuna = cargar('03_cuna_pitch')
    cuba = cargar('04_cuba_cabeza')
    # El modelo V5 fija las orejas del MG996R en Y=-14/+34, Z=±5.
    # Se agrega apoyo del lado posterior; el eje permanece sobre X y Z=150.
    apoyo = caja(-52 - p['fondo_soporte'], -51.9, -20, 40, z - 16, z + 16)
    cuna = cuna.fuse(apoyo)
    h = p['holgura_ventana_servo_provisional']
    # El cuerpo nominal sale 3 mm por delante del plano de orejas.
    # Sin esta ventana, el apoyo ocupa parte del volumen del motor.
    cuna = cuna.cut(caja(-58, -53 + h, -10-h, 30.7+h, z-9.85-h, z+9.85+h))
    cuna = cuna.cut(cilindro_x(p['radio_paso_eje'], 14, -58, 0, z))
    for y in p['y_agujeros']:
        for dz in p['z_agujeros_relativos']:
            cuna = cuna.cut(cilindro_x(p['diametro_tornillo_paso'] / 2, 14, -58, y, z + dz))

    # La placa pasa a pertenecer a la cabeza, en lugar de fijar allí el motor.
    # El patrón de ranuras es sólo una reserva ajustable, NO el encastre real.
    d = p['profundidad_placa_horn']
    soporte = caja(-42 - d, -41.8, -p['ancho_placa_horn']/2,
                   p['ancho_placa_horn']/2, z-p['alto_placa_horn']/2, z+p['alto_placa_horn']/2)
    cuba = cuba.fuse(soporte)
    cuba = cuba.cut(cilindro_x(4, 12, -48, 0, z))
    plano = cq.Plane(origin=(-47, 0, z), xDir=(0, 1, 0), normal=(1, 0, 0))
    for signo in (-1, 1):
        a, b = p['ranura_r_min'], p['ranura_r_max']
        corte = (cq.Workplane(plano).center(signo * (a + b) / 2, 0)
                 .slot2D(b - a + p['ranura_ancho'], p['ranura_ancho']).extrude(8).val())
        cuba = cuba.cut(corte)

    # Envolvente MG996R V5 reflejada por una rotación de 180°: el cuerpo
    # queda detrás de la cuna y su eje permanece colineal con roll.
    motor = (caja(-39, 3.9, -10, 30.7, z - 9.85, z + 9.85)
             .fuse(caja(-36, -33, -16.65, 37.35, z - 9.85, z + 9.85))
             .fuse(cilindro_x(3, 7, -46, 0, z)))
    motor = motor.rotate((-46, 0, z), (-46, 1, z), 180)
    return cuna.clean(), cuba.clean(), motor.clean()


def main():
    SALIDA.mkdir(exist_ok=True)
    cuna, cuba, motor = construir()
    objetos = {'cuna_pitch_roll_exterior': cuna, 'cuba_cabeza_roll_exterior': cuba,
               'referencia_motor_roll_nominal': motor}
    informe = {'estado': 'PROTOTIPO: NO IMPRIMIR NI MONTAR SIN MEDICIONES', 'piezas': {}}
    for nombre, forma in objetos.items():
        registro = {'valido': forma.isValid(), 'solidos': len(forma.Solids()),
                    'volumen_mm3': forma.Volume()}
        informe['piezas'][nombre] = registro
        if not registro['valido'] or registro['solidos'] != 1:
            raise ValueError(f'{nombre}: sólido inválido o desconectado: {registro}')
        cq.exporters.export(forma, str(SALIDA / (nombre + '.step')))
    a = cq.Assembly(name='concepto_roll_exterior_v6')
    for nombre, forma in objetos.items():
        a.add(forma, name=nombre)
    a.export(str(SALIDA / 'concepto_roll_exterior.step'))
    figura = plt.figure(figsize=(9, 6))
    eje = figura.add_subplot(111, projection='3d')
    for forma, color in ((cuna, '#e6a833'), (cuba, '#859a9c'), (motor, '#28323d')):
        vertices, caras = forma.tessellate(.5, .15)
        triangulos = [[[vertices[i].x, vertices[i].y, vertices[i].z] for i in f] for f in caras]
        eje.add_collection3d(Poly3DCollection(triangulos, facecolor=color, edgecolor='none', alpha=.83))
    eje.set(xlim=(-110, 80), ylim=(-100, 100), zlim=(90, 210), xlabel='X mm', ylabel='Y mm', zlabel='Z mm')
    eje.set_box_aspect((190, 200, 120))
    eje.view_init(elev=22, azim=-125)
    eje.set_title('Prototipo: cuna, cuba y MG996R nominal exterior')
    figura.tight_layout()
    figura.savefig(SALIDA / 'vista_roll_exterior.png', dpi=150)
    plt.close(figura)
    pares = [('cuna_cuba', cuna, cuba), ('cuna_motor', cuna, motor),
             ('cuba_motor', cuba, motor)]
    informe['intersecciones_home_mm3'] = {n: max(0., a.intersect(b).Volume()) for n, a, b in pares}
    informe['limitaciones'] = ['No se modelan el brazo real, tornillos, cable ni conectores',
        'No se ha comprobado todo el mecanismo ni la resistencia',
        'Motor nominal simplificado, no medido', 'Las ranuras no son encastre del brazo real']
    (SALIDA / 'informe.json').write_text(json.dumps(informe, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(informe, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
