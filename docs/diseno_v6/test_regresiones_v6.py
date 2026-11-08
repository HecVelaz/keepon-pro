"""Regresiones de interferencias y orientación encontradas al integrar V6."""
from pathlib import Path
import json
import unittest
import cadquery as cq
from verificar_archivos_v6 import revisar_stl
import generar_v6 as generador
from cache_nativos_v6 import actualizar_pieza

R=Path(__file__).resolve().parent


def pieza(n):return cq.importers.importStep(str(R/'STEP_V6'/(n+'.step'))).val()


class RegresionesV6(unittest.TestCase):
    def test_dos_aberturas_traseras_y_tapa14_retirada(self):
        s=pieza('04_cuba_cabeza');z=generador.Z
        for y in (-50,20):
            herramienta=cq.Solid.makeBox(10,30,20,cq.Vector(-46,y,z-46))
            self.assertLess(s.intersect(herramienta).Volume(),.01)
        nombres=[m['name'] for m in json.loads((R/'mallas_v6.json').read_text(encoding='utf-8'))]
        self.assertNotIn('14_tapa_usb',nombres)
        self.assertFalse(any(n.startswith('REF_M3_usb_') for n in nombres))

    def test_pcb_buzzer_medidas_y_agujero_referido_al_borde(self):
        s=generador.pcb_buzzer();bb=s.BoundingBox()
        self.assertAlmostEqual(bb.xlen,1.5,places=5)
        self.assertAlmostEqual(bb.ylen,13,places=5)
        self.assertAlmostEqual(bb.zlen,31.8,places=5)
        # Confirmación del usuario: 4,8/14,9 hasta el borde, no al centro.
        prueba=cq.Solid.makeCylinder(1.49,3,cq.Vector(bb.xmin-.5,bb.ymin+6.3,bb.zmin+16.4),cq.Vector(1,0,0))
        self.assertLess(s.intersect(prueba).Volume(),.01)
        self.assertAlmostEqual(s.Volume(),1.5*(13*31.8-3.141592653589793*1.5**2),places=4)

    def test_ojos_walle_espejados_dorso_plano_y_camara_libre(self):
        a=pieza('16_ojo_izq');b=pieza('17_ojo_der')
        espejo=a.mirror('XZ')
        self.assertLess(espejo.cut(b).Volume()+b.cut(espejo).Volume(),.01)
        for s in (a,b):
            apoyo=[f.Area() for f in s.Faces() if f.geomType()=='PLANE' and abs(f.Center().x-73)<1e-5]
            self.assertGreater(max(apoyo),900)
            ventana=cq.Solid.makeCylinder(8.5,9,cq.Vector(69,0,generador.Z),cq.Vector(1,0,0))
            self.assertLess(s.intersect(ventana).Volume(),.01)

    def test_lote_nativo_parcial_conserva_piezas_posteriores(self):
        previas=[{'archivo':f'{i:02}.SLDPRT','sha256_step':'anterior'} for i in range(16)]
        nueva={'archivo':'03.SLDPRT','sha256_step':'modificada'}
        actual=actualizar_pieza(previas,nueva)
        self.assertEqual(len(actual),16)
        self.assertEqual(next(p for p in actual if p['archivo']=='03.SLDPRT')['sha256_step'],'modificada')
        self.assertEqual(next(p for p in actual if p['archivo']=='15.SLDPRT')['sha256_step'],'anterior')

    def test_paso_usb_atraviesa_pared_trasera_marcada(self):
        s=pieza('04_cuba_cabeza');z=generador.Z
        paso=cq.Solid.makeBox(10,30,20,cq.Vector(-46,-50,z-46))
        self.assertLess(s.intersect(paso).Volume(),.01)
        # Debe permanecer pared por encima: evita una apertura que llegue
        # accidentalmente al borde o debilite toda la cara posterior.
        pared=cq.Solid.makeBox(1,4,3,cq.Vector(-41,-37,z-20))
        self.assertGreater(s.intersect(pared).Volume(),10)

    def test_usb_reservado_no_choca_con_traviesa_en_extremo_roll(self):
        cuna=pieza('03_cuna_pitch')
        reserva=generador.transformar(generador.reserva_usb(),roll=-20)
        self.assertLess(cuna.intersect(reserva).Volume(),.01)

    def test_suplemento_traviesa_respeta_retencion_roll(self):
        cuna=pieza('03_cuna_pitch');tapa=pieza('13_retencion_horn_roll')
        for roll in (-20,0,20):
            self.assertLess(cuna.intersect(generador.transformar(tapa,roll=roll)).Volume(),.01)

    def test_perfil_configurado_pitch_se_usa_en_el_bolsillo(self):
        clave='perfil_brazo_simple_local_xy_mm'
        anterior=generador.CFG['pitch'].get(clave)
        try:
            # Figura de prueba; no representa dimensiones de un brazo comprado.
            generador.CFG['pitch'][clave]=[[-4,-3],[15,-3],[15,3],[-4,3]]
            s=generador.perfil_brazo(2,0,.25,True)
            self.assertTrue(s.isValid())
            self.assertAlmostEqual(s.BoundingBox().xlen,19.5,places=5)
            self.assertAlmostEqual(s.BoundingBox().ylen,6.5,places=5)
        finally:generador.CFG['pitch'][clave]=anterior

    def test_retencion_pitch_no_toca_puente_fijo(self):
        a=pieza('02_horquilla_yaw');b=pieza('12_retencion_horn_pitch_simple')
        self.assertLess(a.intersect(b).Volume(),.01)

    def test_retencion_pitch_se_apoya_sobre_cara_plana(self):
        d=revisar_stl(R/'STL_REVISION_NO_IMPRIMIR/12_retencion_horn_pitch_simple.stl')
        self.assertAlmostEqual(d['min_z_mm'],0,places=3)
        self.assertTrue(d['aristas_dos_incidencias'])

    def test_montaje_yaw_conserva_eje_xy_y_base(self):
        d=json.loads((R/'evidencias/trazabilidad_v6.json').read_text(encoding='utf-8'))
        self.assertFalse(d['base_original_modificada'])
        aud=json.loads((R/'evidencias/auditoria_v6.json').read_text(encoding='utf-8'))
        antiguo=cq.importers.importStep(str(R.parent/'diseno_v5/STEP/01_base.step')).val()
        nuevo=next(p for p in aud['piezas'] if p['nombre']=='01_base')
        self.assertLess(abs(antiguo.Volume()/nuevo['volumen_mm3']-1),1e-7)

    def test_cabeza_tiene_montaje_camara_pasante_22(self):
        s=pieza('06_cara_binocular');z=json.loads((R/'evidencias/trazabilidad_v6.json').read_text())['z_eje_pitch_roll_mm']
        for y in (-10.5,10.5):
            for dz in (-12.4,.1):
                herramienta=cq.Solid.makeCylinder(1.09,9,cq.Vector(65,y,z+dz),cq.Vector(1,0,0))
                self.assertLess(s.intersect(herramienta).Volume(),.01)

    def test_barrido_no_oculta_interferencias(self):
        a=json.loads((R/'evidencias/auditoria_v6.json').read_text(encoding='utf-8'))
        self.assertEqual(a['poses_representadas'],495)
        self.assertFalse(a['interferencias_home'])
        self.assertFalse(any(p['interferencias'] for p in a['poses']))
        self.assertFalse(a['fabricacion_liberada'])


if __name__=='__main__':unittest.main(verbosity=2)
