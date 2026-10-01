#!/usr/bin/env python3
"""Mide la percepción en paralelo (keepon/perception.py) en la Pi, con gente en escena.

    python scripts/perception_bench.py --secs 20

Informa por proceso: Hz de resultados nuevos, ms por cuadro, edad del resultado y CPU;
y la calidad: personas por cuadro, fracción de personas con rostro, ME_MIRA, poses.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from keepon import load_config  # noqa: E402
from keepon.perception import Perception, _cpu_seconds, proc_cpu_seconds  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--secs", type=float, default=20.0)
    ap.add_argument("--warmup", type=float, default=12.0, help="espera a que carguen los modelos")
    ap.add_argument("--workers", default="personas,pose", help="procesos a lanzar (para aislar)")
    a = ap.parse_args()

    cfg = load_config()
    per = Perception(cfg, workers=tuple(a.workers.split(",")))
    t_end_warm = time.monotonic() + a.warmup
    while time.monotonic() < t_end_warm or len(per.latest) < len(per.procs):
        per.poll()
        time.sleep(0.05)
        if time.monotonic() > t_end_warm + 30:
            print("algún proceso no entrega resultados:", set(per.procs) - set(per.latest))
            per.close()
            return

    pids = per.pids()
    cpu0 = {k: proc_cpu_seconds(pid) for k, pid in pids.items()}
    main0, t0 = _cpu_seconds(), time.monotonic()
    res = {k: [] for k in pids}
    while time.monotonic() - t0 < a.secs:
        for r in per.poll():
            res[r.kind].append(r)
        time.sleep(0.005)
    wall = time.monotonic() - t0
    cpu = {k: 100 * (proc_cpu_seconds(pid) - cpu0[k]) / wall for k, pid in pids.items()}
    cpu["principal"] = 100 * (_cpu_seconds() - main0) / wall
    per.close()

    mean = lambda xs: statistics.mean(xs) if xs else float("nan")  # noqa: E731
    print(f"\n=== Percepción en paralelo ({wall:.0f} s) ===")
    for k, rs in res.items():
        ms = [r.proc_ms for r in rs]
        age = [(r.t_done - r.stamp) * 1e3 for r in rs]
        print(f"  {k:<9} {len(rs) / wall:5.1f} Hz | {mean(ms):5.1f} ms/cuadro | edad del resultado "
              f"{mean(age):5.0f} ms | CPU {cpu[k]:4.0f} %")
        if rs and rs[0].parts:
            print("            " + " | ".join(f"{part} {mean([r.parts[part] for r in rs]):5.1f} ms" for part in rs[0].parts))
    print(f"  principal CPU {cpu['principal']:4.0f} %   | TOTAL CPU {sum(cpu.values()):4.0f} % de 400 %")

    if "personas" not in res:
        return
    rp = res["personas"]
    persons = [p for r in rp for p in r.persons]
    with_face = [p for p in persons if p.face]
    print(f"\n  personas por cuadro        {mean([len(r.persons) for r in rp]):.2f}")
    print(f"  personas con rostro        {len(with_face)}/{len(persons)} = {100 * len(with_face) / max(1, len(persons)):.0f} %")
    if with_face:
        print(f"  ME_MIRA (crudo)            {100 * sum(p.face.looking for p in with_face) / len(with_face):.0f} % de los rostros")
        print(f"  desvío cara->cámara        mediana {statistics.median(p.face.dev_deg for p in with_face):.1f}°")
        ids = sorted({p.id for p in persons})
        for pid in ids[:4]:
            fs = [p.face for p in persons if p.id == pid and p.face]
            if fs:
                print(f"    ID {pid}: {len(fs)} rostros, desvío mediana {statistics.median(f.dev_deg for f in fs):5.1f}°, "
                      f"yaw {statistics.median(f.yaw_deg for f in fs):+5.1f}°, pitch {statistics.median(f.pitch_deg for f in fs):+5.1f}°")
    print(f"  IDs distintos vistos       {len({p.id for p in persons})}")
    if "pose" in res:
        print(f"  poses por cuadro           {mean([len(r.poses) for r in res['pose']]):.2f}")


if __name__ == "__main__":
    main()
