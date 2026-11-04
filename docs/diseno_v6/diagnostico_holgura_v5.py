"""Mide la separación nominal cuna/cuba V5 a lo largo de roll, en milímetros.

Ambas piezas comparten pitch y yaw: esos giros rígidos no cambian su distancia
relativa. El barrido discreto no sustituye la medición del montaje real.
"""
from pathlib import Path
import json
import cadquery as cq

RAIZ = Path(__file__).resolve().parent
V5 = RAIZ.parent / "diseno_v5" / "STEP"


def main():
    cuna = cq.importers.importStep(str(V5 / "03_cuna_pitch.step")).val()
    cuba = cq.importers.importStep(str(V5 / "04_cuba_cabeza.step")).val()
    resultados = []
    for angulo in range(-20, 21, 5):
        movida = cuba.rotate((0, 0, 150), (1, 0, 150), angulo)
        distancia = cuna.distance(movida)
        resultados.append({"roll_grados": angulo, "distancia_mm": distancia})
    minimo = min(resultados, key=lambda fila: fila["distancia_mm"])
    informe = {"fuente": "STEP de V5, sin tornillos, cables ni deformación",
               "paso_grados": 5, "minimo": minimo, "muestras": resultados,
               "limitacion": "Muestreo discreto; no identifica el contacto físico ni prueba todo el recorrido continuo."}
    (RAIZ / "evidencias/holgura_cuna_cuba_v5.json").write_text(
        json.dumps(informe, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"minimo": minimo, "muestras": len(resultados)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
