"""Ejecuta lotes cortos, conserva avances y termina con el ensamblaje 2021."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

sys.path.insert(0,'C:/Users/mathi/.codex/skills/solidworks-automation/scripts')
from sw_connect import solidworks_processes

R=Path(__file__).resolve().parent
E=R/'evidencias/solidworks_v6'
def huella(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lista(nombre):return json.loads((E/nombre).read_text()) if (E/nombre).is_file() else []
def correr(etapa,limite=0):
    args=[sys.executable,'-X','utf8','-u',str(R/'crear_solidworks_v6.py'),'--continuar','--etapa',etapa]
    if limite:args+=['--limite',str(limite)]
    subprocess.run(args,check=True)
    # ExitApp es asíncrono: no lanzar la siguiente instancia hasta que haya
    # terminado el proceso que acaba de guardar este lote.
    reporte=json.loads((E/'verificacion_nativa.json').read_text(encoding='utf-8'))
    if reporte.get('cierre_solicitado_al_final'):
        pid=reporte['pid_instancia'];limite_salida=time.monotonic()+120
        while pid in (solidworks_processes() or {}):
            if time.monotonic()>limite_salida:
                raise RuntimeError(f'La instancia propia {pid} sigue cerrando; reanudar el lote después de su salida')
            time.sleep(1)

individuales=[p for p in (R/'STEP_V6').glob('*.step') if not p.name.startswith(('00_','v6_grupo_'))]
for _ in range(len(individuales)+1):
    progreso=lista('progreso_individuales.json')
    faltan=[p for p in individuales if not any(d['archivo']==p.stem+'.SLDPRT' and d.get('sha256_step')==huella(p) for d in progreso)]
    if not faltan:break
    correr('individuales',3)
else:raise RuntimeError('No se completaron los lotes de piezas')
for _ in range(5):
    progreso=lista('progreso_grupos.json')
    faltan=[g for g in ('fixed','yaw','pitch','roll') if not any(d['nombre']==g and d.get('sha256_step')==huella(R/'STEP_V6'/f'v6_grupo_{g}.step') for d in progreso)]
    if not faltan:break
    correr('grupos',1)
else:raise RuntimeError('No se completaron los grupos')
correr('ensamble')
