"""Láminas SVG de revisión B-Rep; las cotas de interfaces están en tablas CSV."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import cadquery as cq
from cadquery.occ_impl.exporters.svg import getSVG

R=Path(__file__).resolve().parent
salida=R/'documentacion/planos_svg_revision';salida.mkdir(parents=True,exist_ok=True)
ns='http://www.w3.org/2000/svg';ET.register_namespace('',ns)
def txt(root,x,y,texto,tamano=16):
    e=ET.SubElement(root,'{'+ns+'}text',{'x':str(x),'y':str(y),'font-size':str(tamano),'font-family':'Arial','fill':'#22383b'});e.text=texto

for p in json.loads((R/'inventario_v6.json').read_text(encoding='utf-8')):
    n=p['nombre'];s=cq.importers.importStep(str(R/'STEP_V6'/(n+'.step'))).val();bb=s.BoundingBox()
    root=ET.Element('{'+ns+'}svg',{'width':'1200','height':'760','viewBox':'0 0 1200 760'})
    ET.SubElement(root,'{'+ns+'}rect',{'width':'1200','height':'760','fill':'white'})
    txt(root,35,45,n,24);txt(root,35,77,'V6 nominal · REVISIÓN: NO FABRICAR SIN CERRAR MEDICIONES',17)
    for x,y,label,d in [(30,110,'Desde +X',(1,0,0)),(425,110,'Desde −Y',(0,-1,0)),(820,110,'Desde +Z',(0,0,1))]:
        vista=ET.fromstring(getSVG(s,{'width':350,'height':390,'marginLeft':25,'marginTop':25,'projectionDir':d,
                                     'showAxes':False,'showHidden':True,'strokeWidth':.6,'hiddenColor':(170,180,180)}))
        vista.set('x',str(x));vista.set('y',str(y));root.append(vista);txt(root,x+20,y+410,label)
    txt(root,35,590,f'Envolvente de montaje XYZ: {bb.xlen:.2f} × {bb.ylen:.2f} × {bb.zlen:.2f} mm',18)
    txt(root,35,625,'Agujeros, ejes y profundidades: agujeros_v6.csv · Uniones: uniones_v6.csv · Parámetros: config.yaml',14)
    txt(root,35,660,'Material, insertos, brazos y conectores reales pendientes. No usar la escala del visor como cota.',14)
    txt(root,35,700,'Proyección y aristas calculadas por OCCT desde STEP; esta lámina no certifica tolerancias ni resistencia.',14)
    ET.ElementTree(root).write(salida/(n+'.svg'),encoding='utf-8',xml_declaration=True)
print('Láminas SVG de revisión generadas.')
