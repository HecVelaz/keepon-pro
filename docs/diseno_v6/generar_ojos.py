"""Ojo adhesivo para la cara plana V5. Medidas en milímetros.

La elipse reproduce el gráfico de generar_v3.py; el espesor es una decisión
de diseño modificable, no una medida de un componente comprado.
"""
from pathlib import Path
import json
import math
import struct
import cadquery as cq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

RAIZ = Path(__file__).resolve().parent
SEMIEJE_HORIZONTAL = 18.0
SEMIEJE_VERTICAL = 20.0
ESPESOR = 1.2


def generar():
    for nombre in ("STEP", "IMPRESION_STL", "evidencias", "vistas"):
        (RAIZ / nombre).mkdir(exist_ok=True)
    ojo = cq.Workplane("XY").ellipse(SEMIEJE_HORIZONTAL, SEMIEJE_VERTICAL).extrude(ESPESOR).val()
    if not ojo.isValid() or len(ojo.Solids()) != 1:
        raise ValueError("El ojo no es un sólido válido")
    step = RAIZ / "STEP/ojo_adhesivo.step"
    stl = RAIZ / "IMPRESION_STL/ojo_adhesivo.stl"
    cq.exporters.export(ojo, str(step))
    cq.exporters.export(ojo, str(stl), tolerance=0.02, angularTolerance=0.08)
    leido = cq.importers.importStep(str(step)).val()
    if not leido.isValid() or len(leido.Solids()) != 1:
        raise ValueError("El STEP reimportado no es un sólido válido")
    volumen_esperado = math.pi * SEMIEJE_HORIZONTAL * SEMIEJE_VERTICAL * ESPESOR
    if abs(leido.Volume() - volumen_esperado) > 0.01:
        raise ValueError("Volumen inesperado")
    datos = stl.read_bytes()
    cantidad = struct.unpack_from("<I", datos, 80)[0]
    if len(datos) != 84 + 50 * cantidad:
        raise ValueError("STL binario truncado")
    aristas = {}
    for i in range(cantidad):
        valores = struct.unpack_from("<12fH", datos, 84 + i * 50)
        vertices = [tuple(round(v, 5) for v in valores[j:j + 3]) for j in (3, 6, 9)]
        for a, b in ((0, 1), (1, 2), (2, 0)):
            clave = tuple(sorted((vertices[a], vertices[b])))
            aristas[clave] = aristas.get(clave, 0) + 1
    if not cantidad or any(n != 2 for n in aristas.values()):
        raise ValueError("Malla con aristas abiertas o no manifold")
    vertices, caras = ojo.tessellate(0.1, 0.12)
    poligonos = [[[vertices[i].x, vertices[i].y, vertices[i].z] for i in cara] for cara in caras]
    figura = plt.figure(figsize=(6, 5))
    eje = figura.add_subplot(111, projection="3d")
    eje.add_collection3d(Poly3DCollection(poligonos, facecolor="#344956", edgecolor="none"))
    eje.set(xlim=(-20, 20), ylim=(-22, 22), zlim=(0, 5), xlabel="mm", ylabel="mm", zlabel="mm")
    eje.set_box_aspect((40, 44, 5))
    eje.view_init(elev=35, azim=-55)
    eje.set_title("Ojo adhesivo: sólido generado")
    figura.tight_layout()
    figura.savefig(RAIZ / "vistas/ojo.png", dpi=150)
    plt.close(figura)
    informe = {"solido_valido": True, "solidos": len(ojo.Solids()),
               "step_reimportado_valido": True, "volumen_mm3": leido.Volume(),
               "dimensiones_mm": [36, 40, ESPESOR], "triangulos_stl": cantidad,
               "aristas_con_dos_incidencias": True,
               "limites": "Sin ensayo físico de impresión, adhesivo o resistencia."}
    (RAIZ / "evidencias/ojos.json").write_text(json.dumps(informe, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(informe, ensure_ascii=False))


if __name__ == "__main__":
    generar()
