"""Empaqueta exclusivamente la revisión R3 y verifica sus dependencias."""
from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).parent

def main():
    n=R/'evidencias/solidworks_R3/verificacion_nativa.json'
    informe=json.loads(n.read_text(encoding='utf-8'))
    assert informe.get('reabierto') and len(informe.get('poses',[]))==10
    assert json.loads((R/'evidencias/barrido_R3.json').read_text(encoding='utf-8'))['aprobado_nominal']
    archivos=[]
    for carpeta in ('SOLIDWORKS_V6_R3','STL_REVISION_NO_IMPRIMIR','IMPRESION_STL'):
        archivos.extend(p for p in (R/carpeta).iterdir() if p.is_file())
    archivos.extend(p for p in (R/'STEP_V6').glob('*.step') if not p.name.startswith('v6_grupo_'))
    for nombre in ('README.md','config.yaml','generar_v6.py','revision_R3.py','verificar_R3.py','test_revision_R3.py','barrer_R3.py','auditar_v6.py','verificar_mallas_R3.py','renderizar_R3.py','crear_solidworks_v6.py','cache_nativos_v6.py','verificar_dependencias_nativas_v6.py','empaquetar_R3.py','inventario_v6.json','documentacion/REVISION_R3.md','documentacion/agujeros_R3.csv','vistas/07_R3_montaje_integrado.png','evidencias/regresiones_R3.json','evidencias/mallas_R3.json','evidencias/barrido_R3.json','evidencias/trazabilidad_v6.json','evidencias/cuerpos_v6.json','evidencias/volumenes_grupos_v6.json','evidencias/solidworks_R3/verificacion_nativa.json','evidencias/solidworks_R3/dependencias_nativas.json','evidencias/solidworks_R3/interferencias_clasificadas.json','evidencias/solidworks_R3/keepon_v6_review_report.json'):
        archivos.append(R/nombre)
    for archivo in (R/'evidencias/solidworks_R3').glob('keepon_v6_*.png'):archivos.append(archivo)
    assert all(p.is_file() and p.stat().st_size for p in archivos)
    manifest={'revision':'R3','fabricacion_liberada':False,'incluye_fuentes_heredadas':False,'nota_fuentes':'Regenerar requiere conservar fuentes V2–V5 y banco SolidWorks del proyecto; el CAD entregado abre sin Python.','archivos':[{'ruta':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in archivos]}
    m=R/'manifest_R3.json';m.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');archivos.append(m)
    destino=R/'Keepon_V6_R3.zip'
    with zipfile.ZipFile(destino,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in archivos:z.write(p,Path('diseno_v6')/p.relative_to(R))
    with zipfile.ZipFile(destino) as z:assert z.testzip() is None
    print(destino.resolve(),destino.stat().st_size,'bytes; ZIP verificado')

if __name__=='__main__':main()
