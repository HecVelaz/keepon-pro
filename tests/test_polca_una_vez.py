"""08/11: la polca (y el abucheo) suenan UNA VEZ POR APARICIÓN de la persona (cooldowns.CAMISETA_por_persona:
null). Antes era cada 25 s: con la camiseta a la vista se repetía, y en el video (escena del arbitraje,
30 s con la camiseta visible) parecía que no dejaba de sonar.
"""
from keepon.synthetic import SynthPerson, const
from keepon.tracker import IoUTracker
from test_regresiones_codex import Rig


def polcas(rig):
    return sum(1 for _, m in rig.robot.log.rows if m.startswith("ARB start CAMISETA"))


def test_con_la_camiseta_a_la_vista_suena_una_sola_vez():
    rig = Rig([SynthPerson(1, appear=0.2, az=const(0.0), shirt=[(0.5, 90.0, "OLIMPIA")])])
    rig.run_until(90.0)                                   # tres veces el cooldown viejo (25 s)
    assert polcas(rig) == 1


def test_si_un_saludo_la_corta_no_se_repite():
    """La escena del arbitraje: el saludo (prioridad 1) corta la polca y después no vuelve a sonar."""
    rig = Rig([SynthPerson(1, appear=0.2, az=const(0.0), shirt=[(0.5, 60.0, "OLIMPIA")], waves=[4.0])])
    rig.run_until(60.0)
    log = [m for _, m in rig.robot.log.rows]
    assert any("CAMISETA" in m and "interrumpido por SALUDO" in m for m in log)
    assert polcas(rig) == 1


def test_si_se_va_y_vuelve_suena_de_nuevo():
    """Al volver, el tracker le da otro ID (ver el test de abajo): para el robot es una aparición nueva."""
    rig = Rig([SynthPerson(1, appear=0.2, leave=15.0, az=const(0.0), shirt=[(0.5, 15.0, "OLIMPIA")]),
               SynthPerson(2, appear=20.0, az=const(0.0), shirt=[(20.0, 60.0, "OLIMPIA")])])
    rig.run_until(40.0)
    assert polcas(rig) == 2


def test_el_tracker_no_reusa_ids():
    """Quien sale del cuadro más de max_lost cuadros vuelve con otro ID (la base de "una vez por aparición")."""
    tr = IoUTracker(max_lost=15)
    caja = (100, 100, 200, 400)
    (primero,) = tr.update([caja])
    for _ in range(16):                                   # se fue más de max_lost cuadros
        tr.update([])
    (segundo,) = tr.update([caja])
    assert segundo != primero
    for _ in range(5):                                    # una oclusión breve conserva el ID
        tr.update([])
    assert tr.update([caja]) == [segundo]
