"""Vistas del ensamble v3 con VTK (render fuera de pantalla, con z-buffer: sin errores de oclusión).

    ~/cq_env/bin/python vistas.py        # escribe ../vistas/*.png
"""
from pathlib import Path

import vtk

import keepon_v3_cad as k

SALIDA = Path(__file__).resolve().parent.parent / "vistas"


def actor(forma, color, opacidad=1.0):
    datos = forma.toVtkPolyData(tolerance=0.2, angularTolerance=0.3)
    m = vtk.vtkPolyDataMapper()
    m.SetInputData(datos)
    a = vtk.vtkActor()
    a.SetMapper(m)
    r, g, b, _ = color.toTuple()
    a.GetProperty().SetColor(r, g, b)
    a.GetProperty().SetOpacity(opacidad)
    return a


def render(nombre, piezas, pos, foco, arriba=(0, 0, 1), ocultar=(), translucidas=(), zoom=1.0, ancho=1100, alto=900):
    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)
    for n, forma, color, *_ in piezas:
        if n in ocultar:
            continue
        ren.AddActor(actor(forma, color, 0.25 if n in translucidas else 1.0))
    cam = ren.GetActiveCamera()
    cam.SetPosition(*pos)
    cam.SetFocalPoint(*foco)
    cam.SetViewUp(*arriba)
    ren.ResetCameraClippingRange()
    cam.Zoom(zoom)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.AddRenderer(ren)
    win.SetSize(ancho, alto)
    win.Render()
    f = vtk.vtkWindowToImageFilter()
    f.SetInput(win)
    f.Update()
    w = vtk.vtkPNGWriter()
    w.SetFileName(str(SALIDA / f"{nombre}.png"))
    w.SetInputConnection(f.GetOutputPort())
    w.Write()


if __name__ == "__main__":
    SALIDA.mkdir(exist_ok=True)
    zc = k.Z_PITCH
    p0 = k.ensamble()
    render("01_frente_iso", p0, (520, 330, 330), (20, 0, 140))
    render("02_atras_iso", p0, (-460, -330, 360), (20, 0, 140))
    render("03_costado", p0, (40, 600, 150), (40, 0, 150), zoom=1.1)
    # Interior de la cabeza: sin la caja, se ve la Pi parada, la cinta en U y la cámara
    render("04_cabeza_interior", p0, (190, 200, zc + 60), (80, 10, zc + 15), zoom=1.0,
           ocultar=("caja_cabeza", "nariz_camara", "ojo_izq", "ojo_der"))
    render("05_cinta_corte", p0, (80, 400, zc + 10), (80, 0, zc + 10), zoom=1.6,
           ocultar=("caja_cabeza", "nariz_camara", "ojo_izq", "ojo_der", "placa_roll"), translucidas=("pi5_puertos",))
    pa = k.ensamble(pitch=k.PITCH_ABAJO, roll=k.ROLL_MAX)
    render("06_nariz_abajo_roll", pa, (480, 330, 260), (20, 0, 130))
    pb = k.ensamble(yaw=40, pitch=-k.PITCH_ARRIBA, roll=-k.ROLL_MAX)
    render("07_mira_arriba", pb, (520, 330, 330), (20, 0, 150))
    print("vistas en", SALIDA)
