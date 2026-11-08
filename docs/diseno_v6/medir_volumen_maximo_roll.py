"""Contrasta precisión máxima de volumen según API oficial SolidWorks2021."""
from pathlib import Path
import sys
import json
import pythoncom
import win32com.client
sys.path.insert(0,'C:/Users/mathi/.codex/skills/solidworks-automation/scripts')
from sw_connect import connect_solidworks,open_document,get_com_member as leer

R=Path(__file__).resolve().parent
sw,_=connect_solidworks(version=2021,wait_seconds=30);sw.UserControl=True
iniciales=list(leer(sw,'GetDocuments') or [])
m=open_document(sw,str(R/'SOLIDWORKS_V6/v6_grupo_roll.SLDPRT'),raise_on_error=True)
m.ClearSelection2(True)
estado=win32com.client.VARIANT(pythoncom.VT_BYREF|pythoncom.VT_I4,0)
datos=list(leer(m.Extension,'GetMassProperties',2,estado))
resultado={'precision_solicitada':2,'estado_api':estado.value,'propiedades':datos,
           'volumen_maxima_precision_mm3':datos[3]*1e9}
(R/'evidencias/solidworks_v6/volumen_roll_maxima_precision.json').write_text(json.dumps(resultado,indent=2),encoding='utf-8')
print(resultado,flush=True)
sw.CloseDoc(leer(m,'GetTitle'))
if not iniciales:sw.ExitApp()
