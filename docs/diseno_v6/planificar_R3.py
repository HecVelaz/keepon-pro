from pathlib import Path
import importlib.util,json,sys
p=Path('C:/Users/mathi/.codex/skills/solidworks-automation/apps/desktop/cad_workbench/engineering_orchestrator.py')
s=importlib.util.spec_from_file_location('orquestador_r3',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
plan=m.build_engineering_plan('Keepon V6 R3: piezas CAD, montaje trasero buzzer, ojos integrados, brazos de servos, agujeros M3, ensamblaje SolidWorks, STEP STL y revisión de interferencias')
Path('diseno_v6/evidencias/dag_R3.json').write_text(json.dumps(plan.to_dict(),ensure_ascii=False,indent=2),encoding='utf-8')
