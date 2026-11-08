"""Inventario geométrico de los STEP heredados. No implica medición física."""
from pathlib import Path
import json
import cadquery as cq

RAIZ = Path(__file__).resolve().parent
REPO = RAIZ.parents[1]


def inspeccionar(ruta):
    pieza = cq.importers.importStep(str(ruta)).val()
    caja = pieza.BoundingBox()
    cilindros = []
    for cara in pieza.Faces():
        if cara.geomType() != 'CYLINDER':
            continue
        cil = cara._geomAdaptor().Cylinder()
        p, d = cil.Location(), cil.Axis().Direction()
        cilindros.append({'radio_mm': round(cil.Radius(), 4),
                          'punto_mm': [round(p.X(), 4), round(p.Y(), 4), round(p.Z(), 4)],
                          'eje': [round(d.X(), 4), round(d.Y(), 4), round(d.Z(), 4)]})
    return {'archivo': str(ruta.relative_to(REPO)), 'valido': pieza.isValid(),
            'caja_mm': [caja.xmin, caja.ymin, caja.zmin, caja.xmax, caja.ymax, caja.zmax],
            'volumen_mm3': pieza.Volume(), 'caras_cilindricas': cilindros}


def main():
    directorio = REPO / 'docs/cad_anteriores/keepon_v4_cad/step/componentes'
    archivos = [directorio / (nombre + '.step') for nombre in
                ('horn_yaw', 'horn_pitch', 'horn_roll', 'servo_yaw_rds3218',
                 'servo_pitch_hs7955tg', 'servo_roll_mg996r')]
    datos = [inspeccionar(ruta) for ruta in archivos]
    (RAIZ / 'evidencias/referencias_step.json').write_text(
        json.dumps(datos, indent=2, ensure_ascii=False), encoding='utf-8')
    for item in datos:
        print(item['archivo'], 'caja', [round(x, 2) for x in item['caja_mm']],
              'cilindros', len(item['caras_cilindricas']), flush=True)


if __name__ == '__main__':
    main()
