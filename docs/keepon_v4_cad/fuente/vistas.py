"""Vistas del ensamble v4 (usa el renderizador VTK de la v3).

    ~/cq_env/bin/python vistas.py        # escribe ../vistas/*.png
"""
from pathlib import Path

import keepon_v4_cad as k4
import vistas as v3vistas   # el de la v3 (keepon_v4_cad agrega su carpeta al path)

v3vistas.SALIDA = Path(__file__).resolve().parent.parent / "vistas"

if __name__ == "__main__":
    v3vistas.SALIDA.mkdir(exist_ok=True)
    zc = k4.Z_PITCH
    p0 = k4.ensamble()
    r = v3vistas.render
    r("01_frente_iso", p0, (480, 330, 330), (0, 0, 120))
    r("02_atras_iso", p0, (-440, -330, 360), (0, 0, 120))
    r("03_costado", p0, (20, 600, 140), (20, 0, 120), zoom=1.1)
    r("04_frente", p0, (600, 0, 130), (0, 0, 120), zoom=1.1)
    # Interior de la base: sin la tapa, se ven las dos baterías, el regulador, la ESP32 y el buzzer
    r("05_base_interior", p0, (260, 260, 300), (0, 0, 35), zoom=1.3,
      ocultar=("tapa_base", "plato_yaw", "soporte_pitch_izq", "soporte_pitch_der", "servo_pitch_hs7955tg",
               "horquilla_cabeza", "servo_roll_mg996r", "horn_pitch", "horn_roll", "placa_roll", "caja_cabeza",
               "nariz_camara", "ojo_izq", "ojo_der", "pi5_pcb", "pi5_puertos", "pi5_conectores_csi",
               "pi5_active_cooler", "camara_pcb", "camara_lente", "camara_conector", "cinta_ffc"))
    r("06_nariz_abajo_roll", k4.ensamble(pitch=k4.k3.PITCH_ABAJO, roll=k4.k3.ROLL_MAX), (480, 330, 260), (0, 0, 120))
    r("07_mira_arriba_yaw", k4.ensamble(yaw=40, pitch=-k4.k3.PITCH_ARRIBA, roll=-k4.k3.ROLL_MAX),
      (480, 330, 330), (0, 0, 130))
    print("vistas en", v3vistas.SALIDA)
