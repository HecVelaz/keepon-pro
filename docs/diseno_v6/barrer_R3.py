"""Barrido nominal R3: 45 combinaciones, sin ocultar contactos no previstos."""
from revision_R3 import nombre_es
import auditar_v6 as a
from pathlib import Path
import json

a.IGNORAR={frozenset(nombre_es(n) for n in par) for par in a.IGNORAR}
a.IGNORAR.add(frozenset((nombre_es('10_adaptador_yaw'),nombre_es('REF_RDS3218'))))
a.main(rapido=True)
p=Path(__file__).parent/'evidencias/auditoria_v6_rapida.json'
s=json.loads(p.read_text(encoding='utf-8'));s['nota_presion']='Solape nominal 0.05 mm/lado en alojamiento RDS3218, intencional para encastre; requiere calibración física.'
s['nota_acoples']='Ejes y cubos comerciales sin estriado exacto; solapes nominales de representación por pareja.'
(Path(__file__).parent/'evidencias/barrido_R3.json').write_text(json.dumps(s,indent=2,ensure_ascii=False),encoding='utf-8')
if s['interferencias_home'] or any(p['interferencias'] for p in s['poses']):raise RuntimeError('Interferencias R3 pendientes; leer barrido_R3.json')
