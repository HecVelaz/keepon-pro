"""Conserva los STEP cuyo único cambio respecto al respaldo es la fecha ISO."""
from pathlib import Path
import json
import re
import zipfile

R=Path(__file__).resolve().parent


def sin_fecha(datos):
    return re.sub(rb"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'",b"'FECHA'",datos)


def main():
    conservados=[];modificados=[]
    with zipfile.ZipFile(R/'HISTORIAL/Keepon_V6_antes_USB_R1.zip') as z:
        for p in sorted((R/'STEP_V6').glob('*.step')):
            ruta='diseno_v6/STEP_V6/'+p.name
            if ruta not in z.namelist():continue
            anterior=z.read(ruta)
            if sin_fecha(p.read_bytes())==sin_fecha(anterior):
                p.write_bytes(anterior);conservados.append(p.name)
            else:modificados.append(p.name)
    resultado={'STEP_geometria_sin_cambios':conservados,'STEP_modificados':modificados,
               'criterio':'Igualdad byte a byte excepto la fecha ISO del encabezado; sin aproximar geometría.'}
    (R/'evidencias/cambios_STEP_USB_R1.json').write_text(json.dumps(resultado,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(resultado,ensure_ascii=False))


if __name__=='__main__':main()
