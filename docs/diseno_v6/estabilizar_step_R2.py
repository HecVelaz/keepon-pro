"""Evita regenerar nativos si el STEP anterior sólo difiere en la fecha."""
from pathlib import Path
import json
import zipfile
from estabilizar_step_R1 import sin_fecha

R=Path(__file__).resolve().parent
conservados=[];modificados=[];nuevos=[]
with zipfile.ZipFile(R/'HISTORIAL/Keepon_V6_antes_R2.zip') as z:
    for p in sorted((R/'STEP_V6').glob('*.step')):
        nombre='diseno_v6/STEP_V6/'+p.name
        if nombre not in z.namelist():nuevos.append(p.name);continue
        anterior=z.read(nombre)
        if sin_fecha(p.read_bytes())==sin_fecha(anterior):
            p.write_bytes(anterior);conservados.append(p.name)
        else:modificados.append(p.name)
(R/'evidencias/cambios_STEP_R2.json').write_text(json.dumps({
    'conservados':conservados,'modificados':modificados,'nuevos':nuevos,
    'retirados':['14_tapa_usb','15_portamodulo_RLBZ23_ajustable'],
    'criterio':'Igualdad byte a byte salvo fecha del encabezado; los retirados permanecen en HISTORIAL.'},
    indent=2,ensure_ascii=False),encoding='utf-8')
print('STEP conservados:',conservados,'; modificados:',modificados,'; nuevos:',nuevos)
