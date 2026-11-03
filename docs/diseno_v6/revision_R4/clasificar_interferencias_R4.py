"""Contrastar solapes del informe SolidWorks con ejes/cubos nominales B-Rep."""
from pathlib import Path
import json
import generar_R4 as g
R=Path(__file__).parent

def main():
    e=R/'evidencias/solidworks_R4';n=json.loads((e/'keepon_v6_review_report.json').read_text(encoding='utf-8'))
    ps={p['name']:p['shape'] for p in g.construir()}
    pares=[('Base_y_electronica','Horquilla_de_giro','Referencia_servo_base_RDS3218','Referencia_brazo_doble_base'),('Horquilla_de_giro','Cuna_de_inclinacion','Referencia_servo_inclinacion_HS7955TG','Referencia_brazo_simple_inclinacion'),('Cuna_de_inclinacion','Cabeza_y_cara','Referencia_servo_balanceo_MG996R','Referencia_disco_balanceo')]
    esperado={frozenset((a,b)):(p,q,max(0.,ps[p].intersect(ps[q]).Volume())) for a,b,p,q in pares}
    items=n['interference']['items'];assert len(items)==3
    verificados=[]
    for i in items:
        par=frozenset(Path(c['path']).stem for c in i['components']);p,q,vol=esperado[par]
        assert abs(vol-i['volume_mm3'])<.0001,(p,q,vol,i['volume_mm3'])
        verificados.append({'cuerpos':[p,q],'volumen_BRep_mm3':vol,'volumen_SolidWorks_mm3':i['volume_mm3'],'clasificacion':'Eje/cubo sin perfil exacto de estriado: contacto nominal de referencia'})
    (e/'interferencias_clasificadas.json').write_text(json.dumps({'pares':verificados,'interferencias_imprevistas_entre_grupos':0,'fabricacion_liberada':False,'nota':'Se conserva advertencia automática; comprobar estriado y montaje físicos.'},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Tres contactos nominales contrastados por pareja y volumen; sin interferencias imprevistas entre grupos')

if __name__=='__main__':main()
