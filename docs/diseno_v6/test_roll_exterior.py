"""Regresión del choque entre soporte de cuna y envolvente del motor."""
import unittest
import generar_roll_exterior as prototipo


class TestRollExterior(unittest.TestCase):
    def test_ventana_libera_motor_nominal_en_home(self):
        cuna, cuba, motor = prototipo.construir()
        for pieza in (cuna, cuba, motor):
            self.assertTrue(pieza.isValid())
            self.assertEqual(len(pieza.Solids()), 1)
        self.assertLess(cuna.intersect(motor).Volume(), 0.01)
        self.assertLess(cuba.intersect(motor).Volume(), 0.01)
        self.assertLess(cuna.intersect(cuba).Volume(), 0.01)


if __name__ == '__main__':
    unittest.main()
