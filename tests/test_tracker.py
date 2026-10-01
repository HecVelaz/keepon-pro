"""Tracker propio de personas."""

from keepon.tracker import IoUTracker


def box(cx, w=100, h=300, cy=250):
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def test_ids_stable_while_walking():
    t = IoUTracker()
    first = t.update([box(100), box(500)])
    for k in range(1, 30):  # A camina a la derecha 5 px/cuadro, B a la izquierda
        ids = t.update([box(100 + 5 * k), box(500 - 5 * k)])
        assert ids == first


def test_short_occlusion_keeps_id():
    t = IoUTracker(max_lost=10)
    (a,) = t.update([box(200)])
    for _ in range(5):
        t.update([])
    assert t.update([box(210)]) == [a]


def test_long_absence_new_id():
    t = IoUTracker(max_lost=5)
    (a,) = t.update([box(200)])
    for _ in range(10):
        t.update([])
    assert t.update([box(200)]) != [a]


def test_crossing_people_keep_ids_with_velocity():
    """Dos personas que se cruzan: la predicción por velocidad evita que se intercambien."""
    t = IoUTracker()
    a, b = t.update([box(200), box(400)])
    for k in range(1, 25):
        ids = t.update([box(200 + 8 * k), box(400 - 8 * k)])
    assert ids == [a, b]


def test_order_of_detections_does_not_matter():
    t = IoUTracker()
    a, b = t.update([box(100), box(500)])
    assert t.update([box(505), box(105)]) == [b, a]
