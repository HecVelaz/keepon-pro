"""Componentes comprados de Keepon pro v3, sin las piezas impresas.

Escribe:
  - ../step/keepon_v3_componentes.step   ensamble solo con los componentes (servos, Pi, cámara, ...)
  - ../step/componentes/<nombre>.step    cada componente por separado
  - ../componentes_v3.txt                lista de componentes con sus dimensiones

Las piezas modeladas conservan la posición del ensamble completo (mismo origen que keepon_v3_ensamble.step).
Las demás (reguladores, fusible, tornillos, ...) salen de la lista del PDF (lista_componentes.py).

    ~/cq_env/bin/python componentes.py
"""
from datetime import date
from pathlib import Path
import re

import cadquery as cq

import keepon_v3_cad as k
import lista_componentes as lc

RAIZ = Path(__file__).resolve().parent.parent

# Nombre legible de cada componente modelado (los impresos no van)
NOMBRES = {
    "bateria_lipo_3s": "Batería LiPo 3S 8000 mAh (MEDIR)",
    "regulador_6v_20a": "Regulador 12 → 6 V, módulo 20 A",
    "regulador_5v_5a": "Regulador 12 → 5,1 V, 5 A",
    "interruptor": "Interruptor de balancín",
    "servo_yaw_rds3218": "Servo de yaw DSSERVO RDS3218",
    "horn_yaw": "Brazo doble del RDS3218 (38 mm)",
    "esp32c3": "ESP32-C3-DevKitM-1",
    "buzzer": "Buzzer pasivo Ø12",
    "servo_pitch_hs7955tg": "Servo de pitch Hitec HS-7955TG",
    "horn_pitch": "Brazo doble del HS-7955TG (38 mm)",
    "servo_roll_mg996r": "Servo de roll TowerPro MG996R",
    "horn_roll": "Brazo doble del MG996R (38 mm)",
    "pi5_pcb": "Raspberry Pi 5: placa",
    "pi5_puertos": "Raspberry Pi 5: USB, Ethernet, USB-C, micro-HDMI y GPIO",
    "pi5_conectores_csi": "Raspberry Pi 5: conectores CAM/DISP",
    "pi5_active_cooler": "Active Cooler de la Pi 5 (MEDIR la altura)",
    "camara_pcb": "Camera Module 3 NoIR: placa",
    "camara_lente": "Camera Module 3 NoIR: lente",
    "camara_conector": "Camera Module 3 NoIR: conector de la cinta",
    "cinta_ffc": "Cinta FFC CSI 22 → 15 pines, 150 mm (MEDIR)",
}


def limpio(t):
    """Saca el HTML de las celdas del PDF."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(t).replace("<br/>", " · "))).strip(" ·")


def num(x):
    return f"{x:.1f}".replace(".", ",")


def main():
    piezas = [p for p in k.ensamble() if not p[3]]   # p[3]: impresa
    (RAIZ / "step" / "componentes").mkdir(parents=True, exist_ok=True)
    asm = cq.Assembly(name="keepon_v3_componentes")
    for nombre, forma, color, _, _ in piezas:
        asm.add(forma, name=nombre, color=color)
        cq.exporters.export(forma, str(RAIZ / "step" / "componentes" / f"{nombre}.step"))
    asm.save(str(RAIZ / "step" / "keepon_v3_componentes.step"))

    L = ["KEEPON PRO v3 · COMPONENTES (sin las piezas impresas)",
         f"Generado el {date.today():%d/%m/%Y} por docs/keepon_v3_cad/fuente/componentes.py",
         "",
         "Medidas en mm. «MEDIR» = verificar con calibre antes de imprimir.",
         "",
         "=" * 100,
         "1. COMPONENTES MODELADOS EN EL CAD",
         "   (están en step/keepon_v3_componentes.step y cada uno en step/componentes/<archivo>.step)",
         "   Caja envolvente en la posición del robot: X (hacia la cara) × Y (de lado a lado) × Z (alto).",
         "   «Desde» = esquina mínima de la caja, respecto del origen del robot (eje de yaw, piso de la caja base).",
         "=" * 100,
         f"{'Componente':58s} {'X × Y × Z':22s} {'Desde (x, y, z)':24s} Archivo"]
    for nombre, forma, _, _, _ in piezas:
        bb = forma.BoundingBox()
        L.append(f"{NOMBRES.get(nombre, nombre):58s} "
                 f"{num(bb.xlen) + ' × ' + num(bb.ylen) + ' × ' + num(bb.zlen):22s} "
                 f"{'(' + num(bb.xmin) + '; ' + num(bb.ymin) + '; ' + num(bb.zmin) + ')':24s} {nombre}.step")

    L += ["", "Servos (medidas nominales del modelo, sin brida ni eje):"]
    for s in (lc.RDS3218, lc.HS7955, lc.MG996R):
        L.append(f"  {s.nombre:10s} cuerpo {num(s.L)} × {num(s.W)} × {num(s.H)} · brida {num(s.Lf)} × {num(s.tf)} "
                 f"de espesor, agujeros {num(s.hs)} × {num(s.hw)} · eje a {num(s.S)} sobre la brida, "
                 f"a {num(s.a)} del extremo · brazo doble de {num(k.BRAZO_L)}")

    secciones = [("2. ACTUADORES", lc.SERVOS), ("3. TORNILLERÍA", lc.TORNILLOS),
                 ("4. ELECTRÓNICA: PROCESAMIENTO, VISIÓN Y CONTROL", lc.PROCESAMIENTO),
                 ("5. ELECTRÓNICA: ALIMENTACIÓN", lc.POTENCIA), ("6. ELECTRÓNICA: BUZZER Y SEÑALES", lc.BUZZER)]
    for titulo, filas in secciones:
        L += ["", "=" * 100, titulo, "=" * 100,
              f"{'Componente':52s} {'Cant.':6s} {'Dimensiones':42s} Estado"]
        for nombre, cant, dim, det, est in filas:
            L.append(f"{limpio(nombre):52s} {str(cant):6s} {limpio(dim):42s} {est}")
            L.append(f"{'':59s}↳ {limpio(det)}")
    L += ["", "No hay rodamiento de yaw: el plato se atornilla al horn del RDS3218."]
    (RAIZ / "componentes_v3.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"{len(piezas)} componentes → step/keepon_v3_componentes.step, step/componentes/ y componentes_v3.txt")


if __name__ == "__main__":
    main()
