"""Registra el plan paramétrico y sus condiciones de fabricación."""
from pathlib import Path
import json
import sys
import yaml
import jsonschema

RAIZ=Path(__file__).resolve().parent
cfg=yaml.safe_load((RAIZ/'config.yaml').read_text(encoding='utf-8'))
skill=Path(cfg['skill'])
plan={'plan_version':1,'source_brief':'V6 Keepon derivada de V5 con referencias de servos V3/V4, base reutilizada, adaptador, roll exterior, cámara, USB, ojos y soporte de placa buzzer.',
      'part_family':'assembly','parameters':cfg,
      'features':[{'name':k,'type':'enclosure','params':cfg[k],'required':True} for k in ('yaw','pitch','roll','usb','camara','buzzer','ojos')],
      'operation_sequence':['Inspeccionar fuentes y nominales','Generar integración B-Rep','Barrido y reparación de interferencias','Exportar STEP/STL de revisión','Crear y reabrir SLDPRT/SLDASM 2021','Documentar montaje y condiciones para fabricar'],
      'assumptions':['V5 es la familia de las piezas que se desean reutilizar.','RLBZ23: PCB13x31.8x1.5, agujero3 y distancias al borde4.8/14.9 confirmadas; alturas/pines y USB sin medir.','R2 elimina tapa14, duplica abertura y añade carcasas WALL-E espejadas con lentes decorativas.','Brazos dobles nominales de 38; pitch simple derivado sólo para estudio.','Material y diámetro de instalación de insertos pendientes.'],
      'risk_register':[{'risk':'Rosca de la base no apta para M3','mitigation':'Comprobar fijaciones existentes; no perforar ni insertar metal en base sin resolver interfaz.'},
                       {'risk':'Encastre nominal no ajusta','mitigation':'Cupón de brazo/material e inserto; completar mediciones antes de liberar.'},
                       {'risk':'Cable atrapado o conector bajo tensión','mitigation':'Ranura partida, bridas por grupo y prueba manual completa con cables reales.'}],
      'review_plan':{'expected_outputs':['STEP_V6/00_ensamble_V6_nominal.step','SOLIDWORKS_V6/Keepon_V6_nominal.SLDASM','README.md'],
                     'views':['isometric','front','top','right'],
                     'checks':['B-Rep válido','STEP reimportado','STL cerrado','Base idéntica','495 poses nominales','Tornillos y retenciones','Solver nativo y reapertura','Mediciones pendientes explícitas']}}
jsonschema.validate(plan,json.loads((skill/'subskills/solidworks-vibecad/schemas/design_plan.schema.json').read_text(encoding='utf-8')))
(RAIZ/'design_plan_v6.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False),encoding='utf-8')
print('Plan V6 validado contra schema de VibeCAD.')
