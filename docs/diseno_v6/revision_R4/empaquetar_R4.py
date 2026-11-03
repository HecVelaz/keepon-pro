"""Entrega R4 autocontenida para abrir CAD; fuentes completas permanecen en proyecto."""
from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).parent

def main():
    e=R/'evidencias/solidworks_R4'
    n=json.loads((e/'verificacion_nativa.json').read_text(encoding='utf-8'))
    assert n.get('reabierto') and len(n.get('poses',[]))==10
    assert json.loads((R/'evidencias/auditoria_v6_rapida.json').read_text(encoding='utf-8'))['aprobado_nominal']
    assert all(json.loads((R/'evidencias/regresiones_R4.json').read_text(encoding='utf-8')).values())
    a=[]
    for carpeta in ('SOLIDWORKS_R4','STEP_V6','STL_REVISION_NO_IMPRIMIR'):
        a.extend(p for p in (R/carpeta).iterdir() if p.is_file())
    for nombre in ('README.md','interfaces_R4.csv','documentar_R4.py','config.yaml','generar_R4.py','verificar_R4.py','crear_solidworks_R4.py','renderizar_R4.py','renderizar_disco_R4.py','verificar_mallas_R4.py','empaquetar_R4.py','auditar_nombres_R4.py','clasificar_interferencias_R4.py','inventario_v6.json','vistas/01_R4_cambios.png','vistas/02_R4_disco_roll.png','evidencias/auditoria_v6_rapida.json','evidencias/regresiones_R4.json','evidencias/mallas_R4.json','evidencias/trazabilidad_v6.json','evidencias/cuerpos_v6.json','evidencias/volumenes_grupos_v6.json'):
        a.append(R/nombre)
    for nombre in ('verificacion_nativa.json','dependencias_nativas.json','interferencias_clasificadas.json','nombres_verificados.json','keepon_v6_review_report.json'):
        a.append(e/nombre)
    a.extend(e.glob('keepon_v6_*.png'))
    assert all(p.is_file() and p.stat().st_size for p in a)
    m=R/'manifest_R4.json';m.write_text(json.dumps({'revision':'R4','fuente_cotas_roll':'Croquis aportado por usuario en chat','fabricacion_liberada':False,'nota':'CAD abre sin Python. Regenerar fuentes requiere proyecto V2–V6 y banco SolidWorks2021.','archivos':[{'ruta':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in a]},ensure_ascii=False,indent=2),encoding='utf-8');a.append(m)
    destino=R.parent/'Keepon_V6_R4.zip'
    with zipfile.ZipFile(destino,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in a:z.write(p,Path('Keepon_V6_R4')/p.relative_to(R))
    with zipfile.ZipFile(destino) as z:assert z.testzip() is None
    print(destino.resolve(),destino.stat().st_size,'bytes; ZIP verificado')

if __name__=='__main__':main()
