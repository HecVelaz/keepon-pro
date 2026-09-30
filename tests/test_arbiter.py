"""Reglas del árbitro (T6)."""

from keepon.arbiter import BUZZER, NECK, Arbiter, Proposal

N, B, NB = frozenset({NECK}), frozenset({BUZZER}), frozenset({NECK, BUZZER})


def owner(a, r):
    g = a.owner[r]
    return g.behavior if g else None


def test_priority_preempts_interruptible():
    a = Arbiter()
    a.step(0, [Proposal("SEGUIMIENTO", 4, N, continuous=True)])
    d = a.step(1, [Proposal("SEGUIMIENTO", 4, N, continuous=True), Proposal("SALUDO", 1, NB, interruptible_by=0)])
    assert owner(a, NECK) == "SALUDO" and owner(a, BUZZER) == "SALUDO"
    assert [g.behavior for g in d.cancelled] == ["SEGUIMIENTO"]


def test_non_interruptible_is_respected():
    a = Arbiter()
    a.step(0, [Proposal("SALUDO", 1, NB, interruptible_by=0)])
    a.step(1, [Proposal("CAMISETA", 2, B)])
    a.step(1, [Proposal("OTRO", 1, N)])  # misma prioridad tampoco interrumpe
    assert owner(a, BUZZER) == "SALUDO" and owner(a, NECK) == "SALUDO"


def test_shirt_only_interruptible_by_0_1():
    a = Arbiter()
    a.step(0, [Proposal("CAMISETA", 2, B, interruptible_by=1)])
    a.step(1, [Proposal("MODO", 3, B)])
    assert owner(a, BUZZER) == "CAMISETA"
    a.step(2, [Proposal("SALUDO", 1, NB, interruptible_by=0)])
    assert owner(a, BUZZER) == "SALUDO"


def test_atomic_acquisition():
    """El saludo necesita cuello+buzzer: si uno no se puede tomar, no toma ninguno."""
    a = Arbiter()
    a.step(0, [Proposal("X", 0, B, interruptible_by=-1), Proposal("SEGUIMIENTO", 4, N, continuous=True)])
    a.step(1, [Proposal("SALUDO", 1, NB), Proposal("SEGUIMIENTO", 4, N, continuous=True)])
    assert owner(a, NECK) == "SEGUIMIENTO" and owner(a, BUZZER) == "X"


def test_coexistence_on_different_resources():
    a = Arbiter()
    a.step(0, [Proposal("SEGUIMIENTO", 4, N, continuous=True), Proposal("CAMISETA", 2, B)])
    assert owner(a, NECK) == "SEGUIMIENTO" and owner(a, BUZZER) == "CAMISETA"


def test_continuous_released_when_not_proposed():
    a = Arbiter()
    a.step(0, [Proposal("OBSERVADOR", 5, N, continuous=True)])
    d = a.step(1, [])
    assert owner(a, NECK) is None and d.finished[0].behavior == "OBSERVADOR"


def test_episodic_holds_until_finish():
    a = Arbiter()
    d = a.step(0, [Proposal("CAMISETA", 2, B)])
    a.step(1, [])
    assert owner(a, BUZZER) == "CAMISETA"
    a.finish(d.started[0].id, 2)
    assert owner(a, BUZZER) is None


def test_cooldown_registered_on_start_only():
    a = Arbiter()
    p = Proposal("CAMISETA", 2, B, person=1, cooldown=(("CAM", 1), 25.0))
    blocker = Proposal("SALUDO", 1, NB, interruptible_by=0)
    a.step(0, [blocker, p])              # rechazada: buzzer ocupado -> NO entra en cooldown
    assert not a.in_cooldown(("CAM", 1), 0.1)
    a.finish(a.owner[BUZZER].id, 1)
    d = a.step(1, [p])
    assert d.started and a.in_cooldown(("CAM", 1), 20)
    a.finish(d.started[0].id, 7)
    assert not a.step(8, [p]).started    # dentro del cooldown
    assert a.step(27, [p]).started


def test_expired_proposal_discarded():
    a = Arbiter()
    assert not a.step(5, [Proposal("SALUDO", 1, NB, expires=4.9)]).started


def test_stop_cancels_everything_and_latches():
    a = Arbiter()
    a.step(0, [Proposal("SALUDO", 1, NB, interruptible_by=0)])
    cancelled = a.emergency_stop(1)
    assert [g.behavior for g in cancelled] == ["SALUDO"]
    assert not a.step(2, [Proposal("SEGUIMIENTO", 4, N, continuous=True)]).started
    a.resume(3)
    assert a.step(4, [Proposal("SEGUIMIENTO", 4, N, continuous=True)]).started


def test_continuous_retarget_keeps_resource():
    a = Arbiter()
    d0 = a.step(0, [Proposal("SEGUIMIENTO", 4, N, continuous=True, person=1)])
    d1 = a.step(1, [Proposal("SEGUIMIENTO", 4, N, continuous=True, person=2)])
    assert not d1.started and not d1.finished
    assert a.owner[NECK].id == d0.started[0].id and a.owner[NECK].person == 2
