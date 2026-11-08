"""Ejecuta regresiones reales y guarda el resultado de la revisión vigente."""
from pathlib import Path
import hashlib
import json
import time
import unittest
import yaml

R=Path(__file__).resolve().parent
inicio=time.monotonic()
resultado=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('test_regresiones_v6'))
config=yaml.safe_load((R/'config.yaml').read_text(encoding='utf-8'))
datos={'revision':config['revision'],'pruebas_ejecutadas':resultado.testsRun,
       'fallos':len(resultado.failures),'errores':len(resultado.errors),
       'resultado':'OK' if resultado.wasSuccessful() else 'FALLIDO',
       'segundos':round(time.monotonic()-inicio,3),
       'sha256_test':hashlib.sha256((R/'test_regresiones_v6.py').read_bytes()).hexdigest(),
       'sha256_config':hashlib.sha256((R/'config.yaml').read_bytes()).hexdigest()}
(R/'evidencias/regresiones_v6.json').write_text(json.dumps(datos,indent=2,ensure_ascii=False),encoding='utf-8')
if not resultado.wasSuccessful():raise SystemExit(1)
