"""Captura del panel del celular y figura con sus botones explicados (para el README y el informe).

Levanta el panel real (scripts/panel_web.py, con scripts/panel/) en la notebook con un estado de ejemplo
(robot encendido, modo Neutro, siguiendo a una persona que mira y sonando la polca), lo abre en un Chromium sin
ventana con tamaño de celular (390 × 844, como un iPhone) y arma docs/img/panel_celular.png: dos pantallas
(arriba y abajo de la página) y la explicación de cada grupo de botones. No usa la Pi ni el robot.

Uso:  pip install playwright pillow && python -m playwright install chromium
      python scripts/captura_panel.py
"""
import json
import sys
import tempfile
import threading
import time
from http.server import ThreadingHTTPServer
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ))
import panel_web  # noqa: E402
from keepon import load_config  # noqa: E402

LATO = "/usr/share/fonts/truetype/lato/Lato-{}.ttf"
FONDO, TINTA, TENUE, ACENTO = (246, 245, 241), (29, 29, 27), (107, 106, 100), (242, 160, 32)


def capturar():
    """Devuelve (pantalla de arriba, página completa) como imágenes PIL, a 3× de resolución."""
    from playwright.sync_api import sync_playwright
    sonidos = list(load_config()["sounds"])
    run = Path(tempfile.mkdtemp())
    estado = {"t": time.time() + 36000, "modo": "NEUTRO", "stop": False, "home": False, "lazo_hz": 38,
              "foco": 1, "me_mira": True, "cuello": "SEGUIMIENTO", "buzzer": "CAMISETA (POLCA)",
              "ref": [12.0, -4.0, 0.0], "personas_hz": 15, "edad_ms": 110, "personas": 1,
              "ultimo_comando": "n", "volumen": 60, "sonidos": sonidos}
    (run / "estado.json").write_text(json.dumps(estado), encoding="utf-8")
    srv = ThreadingHTTPServer(("127.0.0.1", 0),
                              panel_web.crear_handler(sonidos, run=run, ctl=lambda accion: (True, "active")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            nav = p.chromium.launch()
            pag = nav.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3,
                               is_mobile=True, has_touch=True)
            pag.goto(f"http://127.0.0.1:{srv.server_address[1]}/")
            pag.wait_for_timeout(1500)                  # que llegue /estado y se armen los botones de sonido
            arriba = Image.open(BytesIO(pag.screenshot()))
            completa = Image.open(BytesIO(pag.screenshot(full_page=True)))
            nav.close()
    finally:
        srv.shutdown()
    return arriba, completa


def celular(pantalla, alto):
    """La captura dentro de un marco de celular de `alto` píxeles."""
    k = (alto - 36) / pantalla.height
    img = pantalla.convert("RGB").resize((round(pantalla.width * k), alto - 36), Image.LANCZOS)
    w, h = img.width + 36, alto
    marco = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(marco)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 46, fill=(24, 24, 27))
    mascara = Image.new("L", img.size, 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, img.width - 1, img.height - 1), 30, fill=255)
    marco.paste(img, (18, 18), mascara)
    d.rounded_rectangle((w / 2 - 50, 26, w / 2 + 50, 46), 10, fill=(24, 24, 27))   # isla de la cámara
    return marco


def figura(arriba, completa, salida):
    W, H = 1800, 1100
    lam = Image.new("RGB", (W, H), FONDO)
    d = ImageDraw.Draw(lam)
    f = {n: ImageFont.truetype(LATO.format(e), s) for n, e, s in
         [("tit", "Black", 40), ("sub", "Medium", 20), ("h", "Black", 22), ("t", "Regular", 18), ("p", "Medium", 16)]}
    d.text((60, 40), "Panel del celular: controlar a Wall-E desde el teléfono", font=f["tit"], fill=TINTA)
    d.text((60, 96), "Página web servida por la Raspberry Pi (puerto 8081) que se instala como app con "
                     "“Agregar a pantalla de inicio”. Captura del panel real con un estado de ejemplo.",
           font=f["sub"], fill=TENUE)
    abajo = completa.crop((0, completa.height - arriba.height, completa.width, completa.height))
    for i, (img, rotulo) in enumerate([(arriba, "Arriba: encendido, STOP, modos y movimiento"),
                                       (abajo, "Abajo: sonidos, volumen y estado en vivo")]):
        tel = celular(img, 880)
        x = 60 + i * (tel.width + 40)
        lam.paste(tel, (x, 160), tel)
        d.text((x + tel.width / 2, 1060), rotulo, font=f["p"], fill=TENUE, anchor="mm")
    x0 = 60 + 2 * (celular(arriba, 880).width + 40) + 20
    grupos = [
        ("Encender / Apagar", ["Arranca o apaga el robot entero (servicio en la Pi).",
                               "Apagar lo lleva a HOME antes de soltar los servos."]),
        ("STOP", ["Detiene cuello y buzzer y queda enclavado.", "Tocarlo de nuevo = RESUME."]),
        ("Modo de personalidad", ["Neutro, Tímido, Atrevido y Maleducado, al instante.",
                                  "Cada uno confirma con su beep; el actual se resalta."]),
        ("Movimiento", ["Home: va a 0/0/0 y se queda hasta Resume.",
                        "Ejes: muestra yaw, pitch y roll en ~15 s (para la demo)."]),
        ("Sonidos y volumen", ["R2D2, polcas de Olimpia y Cerro, abucheo, piropo…",
                               "Volumen 0–100 %, guardado para el próximo arranque."]),
        ("Estado en vivo (cada 1 s)", ["Modo, a quién sigue y si lo mira, dueño del cuello",
                                       "y del buzzer, ángulos, percepción y último comando."]),
        ("Overlay de la cámara", ["Enlace al video con las detecciones (monitoreo T7)."]),
    ]
    y = 175
    for titulo, lineas in grupos:
        d.ellipse((x0, y + 6, x0 + 14, y + 20), fill=ACENTO)
        d.text((x0 + 26, y), titulo, font=f["h"], fill=TINTA)
        for j, l in enumerate(lineas):
            d.text((x0 + 26, y + 34 + j * 25), l, font=f["t"], fill=TENUE)
        y += 46 + 25 * len(lineas) + 18
    d.rounded_rectangle((x0, y + 4, W - 60, y + 92), 12, fill=(255, 255, 255), outline=(217, 214, 204), width=2)
    d.text((x0 + 18, y + 18), "Seguridad: el servidor solo acepta una lista cerrada", font=f["p"], fill=TINTA)
    d.text((x0 + 18, y + 42), "de comandos; desde la página no se puede ejecutar", font=f["p"], fill=TINTA)
    d.text((x0 + 18, y + 66), "nada más en la Pi (scripts/panel_web.py).", font=f["p"], fill=TINTA)
    lam.save(salida, optimize=True)


def main():
    arriba, completa = capturar()
    salida = RAIZ / "docs" / "img" / "panel_celular.png"
    figura(arriba, completa, salida)
    completa.convert("RGB").save(RAIZ / "docs" / "img" / "panel_celular_completo.png", optimize=True)
    print(salida)


if __name__ == "__main__":
    main()
