"""Contrasta interferencias nativas con parejas y volúmenes B-Rep previstos."""
from pathlib import Path
import json

R=Path(__file__).resolve().parent
esperados=json.loads((R/'evidencias/acoples_nominales.json').read_text())
reporte=json.loads((R/'evidencias/solidworks_v6/keepon_v6_review_report.json').read_text(encoding='utf-8'))
datos=reporte['interference'];aceptadas=[];inesperadas=[];vistos=set()
for item in datos.get('items',[]):
    par=frozenset(Path(c['path']).stem.replace('v6_grupo_','') for c in item['components'])
    esperado=next((p for p in esperados if frozenset(p['grupos'])==par),None)
    if esperado and par not in vistos and abs(item['volume_mm3']-esperado['volumen_mm3'])<.01:
        aceptadas.append({'eje':esperado['eje'],'volumen_medido_mm3':item['volume_mm3'],
                          'volumen_brep_previsto_mm3':esperado['volumen_mm3']});vistos.add(par)
    else:inesperadas.append(item)
salida={'acoples_identificados':aceptadas,'interferencias_inesperadas':inesperadas,
        'errores':datos.get('errors',[]),'aprobado':len(aceptadas)==3 and not inesperadas and not datos.get('errors'),
        'nota':'Las envolventes no incluyen el estriado real. No se ignoran otras colisiones entre esos grupos.'}
(R/'evidencias/solidworks_v6/interferencias_clasificadas.json').write_text(json.dumps(salida,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(salida,ensure_ascii=False))
if not salida['aprobado']:raise SystemExit('Revisar interferencias nativas no justificadas')
