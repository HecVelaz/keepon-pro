"""Entrega nativa 2021 de la V6 nominal: piezas importadas y tres giros.

Los parámetros editables permanecen en config.yaml y generar_v6.py. Se verifica
guardado, reapertura, cuerpos y solver; no se afirma disponer de croquis nativos.
"""
from pathlib import Path
import importlib.util
import json
import math
import sys
import traceback
import argparse
import hashlib
import numpy as np
import pythoncom
import win32com.client
from PIL import Image
from cache_nativos_v6 import actualizar_pieza
from revision_R3 import nombre_es
from verificar_dependencias_nativas_v6 import dependencias

RAIZ=Path(__file__).resolve().parent
SALIDA=RAIZ/'SOLIDWORKS_V6_R3'
EVIDENCIA=RAIZ/'evidencias/solidworks_R3'
for c in (SALIDA,EVIDENCIA):c.mkdir(exist_ok=True,parents=True)
sys.path.insert(0,'C:/Users/mathi/.codex/skills/solidworks-automation/scripts')
sys.path.insert(0,str(RAIZ.parents[1]/'pruebas_solidworks_2021'))
from sw_connect import connect_solidworks, get_com_member as leer, open_document, save_document, new_document
from sw_assembly import add_component, get_assembly_entity, select_entities_for_mate, add_mate5_checked, collect_mate_feature_summary
from sw_review import run_review
from compatibilidad_com import metodo_com
spec=importlib.util.spec_from_file_location('ayudas_nativas_v5',RAIZ.parent/'diseno_v5/crear_solidworks.py')
ayuda=importlib.util.module_from_spec(spec);spec.loader.exec_module(ayuda)
Z=json.loads((RAIZ/'evidencias/trazabilidad_v6.json').read_text(encoding='utf-8'))['z_eje_pitch_roll_mm']


def exigir(x,m):
    if not x:raise RuntimeError(m)


def matriz(utilidad,datos):
    return metodo_com(utilidad,'CreateTransform',win32com.client.VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,datos))


def transformacion(grupo,yaw,pitch,roll):
    y,p,r=map(math.radians,(yaw,-pitch,roll))
    rz=np.array([[math.cos(y),-math.sin(y),0],[math.sin(y),math.cos(y),0],[0,0,1]])
    ry=np.array([[math.cos(p),0,math.sin(p)],[0,1,0],[-math.sin(p),0,math.cos(p)]])
    rx=np.array([[1,0,0],[0,math.cos(r),-math.sin(r)],[0,math.sin(r),math.cos(r)]])
    rot=np.eye(3)
    if grupo in ('pitch','roll'):rot=ry@(rx if grupo=='roll' else np.eye(3))
    centro=np.array([0.,0.,Z/1000]);t=centro-rot@centro
    if grupo!='fixed':rot=rz@rot;t=rz@t
    return [*rot.T.flatten().tolist(),*t.tolist(),1.,0,0,0]


def cilindrica(modelo,componente,nombre,eje,radio,punto):
    nombre=nombre_es(nombre)
    candidatas=[]
    for b in leer(modelo,'GetBodies2',0,False) or []:
        if str(leer(b,'Name'))!=nombre:continue
        for f in leer(b,'GetFaces') or []:
            s=leer(f,'GetSurface')
            if not leer(s,'IsCylinder'):continue
            d=list(leer(s,'CylinderParams'))
            if (abs(abs(sum(d[3+i]*eje[i] for i in range(3)))-1)<1e-6
                and abs(d[6]*1000-radio)<.02
                and np.linalg.norm(np.cross(np.array(d[:3])*1000-np.array(punto),eje))<.02):
                candidatas.append((leer(f,'GetArea'),f))
    exigir(candidatas,f'Falta cilindro {nombre}, R{radio}')
    return get_assembly_entity(componente,max(candidatas,key=lambda c:c[0])[1])


def main(continuar=False,etapa='todo',limite=0):
    sw,_=connect_solidworks(version=2021,wait_seconds=30)
    sw.UserControl=True
    iniciales={str(leer(d,'GetTitle')) for d in leer(sw,'GetDocuments') or []}
    propios=[]
    informe={'version':leer(sw,'RevisionNumber'),'individuales':[],'grupos':[],'poses':[],'fabricacion_liberada':False}
    informe['pid_instancia']=int(leer(sw,'GetProcessID'))
    informe['cierre_solicitado_al_final']=etapa in ('individuales','grupos') and not iniciales
    informe['sha256_config']=hashlib.sha256((RAIZ/'config.yaml').read_bytes()).hexdigest()
    previos_ind=json.loads((EVIDENCIA/'progreso_individuales.json').read_text()) if (EVIDENCIA/'progreso_individuales.json').is_file() else []
    previos_gr=json.loads((EVIDENCIA/'progreso_grupos.json').read_text()) if (EVIDENCIA/'progreso_grupos.json').is_file() else []
    nuevos=0
    prev={i:sw.GetUserPreferenceToggle(i) for i in (220,691)}
    estructura=sw.GetUserPreferenceIntegerValue(579)
    modo_guardado=sw.GetUserPreferenceIntegerValue(201)
    def abrir(ruta):
        m=open_document(sw,str(ruta),silent=True,raise_on_error=True)
        exigir(str(leer(m,'GetTitle')) not in iniciales,'Documento inicial: no se modifica')
        propios.append(m);return m
    def cerrar(m):
        sw.CloseDoc(leer(m,'GetTitle'));propios.remove(m)
    try:
        ayuda.configurar_importacion(sw)
        # Primero las piezas individuales, de una en una para limitar memoria.
        for ruta in sorted((RAIZ/'STEP_V6').glob('*.step')):
            if ruta.name.startswith(('00_','v6_grupo_','R3_grupo_')):continue
            destino=SALIDA/(ruta.stem+'.SLDPRT')
            anterior=next((p for p in previos_ind if p['archivo']==destino.name),None)
            huella=hashlib.sha256(ruta.read_bytes()).hexdigest()
            if etapa in ('grupos','ensamble') or (continuar and destino.is_file() and anterior and anterior['bytes']==destino.stat().st_size and anterior.get('sha256_step')==huella):
                if anterior:informe['individuales'].append(anterior)
                continue
            m=abrir(ruta)
            exigir(leer(m,'GetType')==1,'Se esperaba pieza individual')
            exigir(len(leer(m,'GetBodies2',0,False) or [])==1,'Pieza no monosólida')
            leer(m,'GetBodies2',0,False)[0].Name=ruta.stem
            exigir(m.ForceRebuild3(False),'Error de reconstrucción')
            exigir(save_document(m,str(destino)),'Falló SLDPRT')
            cerrar(m)
            m=abrir(destino)
            exigir(len(leer(m,'GetBodies2',0,False) or [])==1,'Reapertura sin sólido')
            informe['individuales'].append({'archivo':destino.name,'reabierto':True,'bytes':destino.stat().st_size,'sha256_step':huella})
            # Conservar también la cola ya verificada: un lote parcial no debe
            # borrar del caché las piezas posteriores que no cambiaron.
            previos_ind=actualizar_pieza(previos_ind,informe['individuales'][-1])
            (EVIDENCIA/'progreso_individuales.json').write_text(json.dumps(previos_ind,indent=2),encoding='utf-8')
            cerrar(m)
            print('SLDPRT',destino.name,'OK',flush=True)
            nuevos+=1
            if etapa=='individuales' and limite and nuevos>=limite:
                informe['estado']='LOTE DE PIEZAS GUARDADO';return
        if etapa=='individuales':informe['estado']='PIEZAS INDIVIDUALES COMPLETADAS';return
        fuentes=json.loads((RAIZ/'evidencias/cuerpos_v6.json').read_text(encoding='utf-8'))
        volumenes=json.loads((RAIZ/'evidencias/volumenes_grupos_v6.json').read_text(encoding='utf-8'))
        documentos,rutas={},{}
        util=leer(sw,'GetMathUtility')
        for grupo in ('fixed','yaw','pitch','roll'):
            destino=SALIDA/f'R3_grupo_{grupo}.SLDPRT'
            anterior=next((p for p in previos_gr if p['nombre']==grupo),None)
            paso=RAIZ/'STEP_V6'/f'R3_grupo_{grupo}.step'
            huella=hashlib.sha256(paso.read_bytes()).hexdigest()
            if etapa=='grupos' and continuar and destino.is_file() and anterior and anterior.get('sha256_step')==huella:
                informe['grupos'].append(anterior);continue
            m=abrir(destino if etapa=='ensamble' else paso)
            if leer(m,'GetType')==2:
                sw.SetUserPreferenceIntegerValue(201,1)
                exigir(save_document(m,str(destino)),'Conversión multicuerpo falló');cerrar(m);m=abrir(destino)
            cuerpos=list(leer(m,'GetBodies2',0,False) or [])
            refs=[p.copy() for p in fuentes if p['grupo']==grupo]
            exigir(len(cuerpos)==len(refs),'Cantidad de cuerpos discrepante')
            for b in cuerpos:
                caja=np.array(leer(b,'GetBodyBox'))*1000
                ref=min(refs,key=lambda p:np.max(np.abs(caja-p['caja_mm'])))
                exigir(np.max(np.abs(caja-ref['caja_mm']))<.2,'Cuerpo no identificado')
                b.Name=ref['nombre'];ayuda.colorear_cuerpo(b,ref['color']);refs.remove(ref)
            exigir(m.ForceRebuild3(False),'Error de grupo')
            # Precisión máxima documentada por API2021. La integración por
            # defecto de superficies elípticas produjo una falsa discrepancia.
            m.ClearSelection2(True)
            estado_masa=win32com.client.VARIANT(pythoncom.VT_BYREF|pythoncom.VT_I4,0)
            propiedades=list(leer(m.Extension,'GetMassProperties',2,estado_masa))
            exigir(estado_masa.value==0,'Error de propiedades de masa')
            volumen=float(propiedades[3])*1e9
            esperado=volumenes[grupo]['volumen_mm3']
            exigir(abs(volumen/esperado-1)<1e-6,'Volumen nativo discrepante: '+grupo)
            ayuda.orientar(m,util)
            exigir(save_document(m,str(destino)),'No se guardó grupo')
            documentos[grupo]=m;rutas[grupo]=destino
            dato={'nombre':grupo,'cuerpos':len(cuerpos),'volumen_nativo_mm3':volumen,'error_relativo':abs(volumen/esperado-1),'precision_volumen_api':2,'sha256_step':huella}
            informe['grupos'].append(dato)
            previos_gr=[p for p in previos_gr if p['nombre']!=grupo]+[{**dato,'bytes':destino.stat().st_size}]
            (EVIDENCIA/'progreso_grupos.json').write_text(json.dumps(previos_gr,indent=2),encoding='utf-8')
            print('GRUPO',grupo,'OK',flush=True)
            nuevos+=1
            if etapa=='grupos' and limite and nuevos>=limite:
                informe['estado']='LOTE DE GRUPOS GUARDADO';return
        if etapa=='grupos':informe['estado']='GRUPOS COMPLETADOS';return
        asm=new_document(sw,'assembly',max_documents=30);propios.append(asm)
        comps={}
        identidad=transformacion('fixed',0,0,0)
        for grupo in ('fixed','yaw','pitch','roll'):
            c=add_component(asm,str(rutas[grupo]),sw=sw)
            exigir(c is not None,'No se insertó '+grupo)
            c.Transform2=matriz(util,identidad);comps[grupo]=c
        articulaciones=[
            ('yaw','fixed','yaw','REF_RDS3218','REF_horn_yaw',(0,0,1),3.,4.5,(0,0,60),'Front Plane'),
            ('pitch','yaw','pitch','REF_HS7955TG','03_cuna_pitch',(0,1,0),3.,4.2,(0,0,Z),'Top Plane'),
            ('roll','pitch','roll','REF_MG996R_exterior','REF_horn_roll',(1,0,0),3.,4.5,(0,0,Z),'Right Plane')]
        for nombre,padre,hijo,npadre,nhijo,eje,rp,rh,punto,plano in articulaciones:
            entidades=[cilindrica(documentos[g],comps[g],n,eje,r,punto)
                       for g,n,r in ((padre,npadre,rp),(hijo,nhijo,rh))]
            ayuda.concentricas(asm,entidades,'Giro_'+nombre)
            planos=[get_assembly_entity(comps[g],documentos[g].FeatureByName(plano)) for g in (padre,hijo)]
            select_entities_for_mate(asm,*planos);add_mate5_checked(asm,0,name='Axial_'+nombre)
        exigir(asm.ForceRebuild3(False),'Reconstrucción ensamblaje falló')
        informe['relaciones']=collect_mate_feature_summary(asm)
        for pose in [(0,0,0),(-70,0,0),(70,0,0),(0,-20,0),(0,30,0),(0,0,-20),(0,0,20),(-70,-20,-20),(70,30,20),(0,0,0)]:
            for grupo in ('yaw','pitch','roll'):
                metodo_com(comps[grupo],'SetTransformAndSolve2',matriz(util,transformacion(grupo,*pose)))
            exigir(asm.ForceRebuild3(False),'Solver falló')
            errores={g:max(abs(a-b) for a,b in zip(list(leer(leer(comps[g],'Transform2'),'ArrayData')),transformacion(g,*pose))) for g in ('yaw','pitch','roll')}
            exigir(max(errores.values())<1e-5,f'Pose inalcanzada {pose}: {errores}')
            informe['poses'].append({'yaw_pitch_roll':pose,'errores':errores})
            print('POSE SW',pose,'OK',flush=True)
        ayuda.orientar(asm,util)
        destino=SALIDA/'Keepon_V6_R3.SLDASM'
        exigir(save_document(asm,str(destino)),'No se guardó ensamblaje')
        informe['revision_skill'],_=run_review(asm,str(EVIDENCIA),basename='keepon_v6',expected_outputs=[str(destino),*map(str,rutas.values())])
        asm.ShowNamedView2('',7);asm.ViewZoomtofit2();exigir(save_document(asm,str(destino)),'Guardado de vista falló')
        cerrar(asm);asm=abrir(destino)
        informe['reabierto']=True;informe['relaciones_reabiertas']=collect_mate_feature_summary(asm)
        referencias=[Path(leer(c,'GetPathName')).resolve() for c in leer(asm,'GetComponents',False) or []]
        exigir(len(referencias)==4 and all(p.is_file() and p.parent==SALIDA.resolve() for p in referencias),'Referencias fuera del paquete o ausentes')
        informe['referencias_locales']=list(map(str,referencias))
        # Revisar dependencias mientras aún conservamos la interfaz COM; una
        # segunda conexión a una instancia sin registro ROT puede fallar.
        deps=dependencias(asm)
        exigir(len(deps)==4 and all(Path(p).parent==SALIDA for p in deps),'Dependencias de ensamblaje inesperadas')
        grupos_dep=[]
        for c in leer(asm,'GetComponents',False) or []:
            externas=dependencias(leer(c,'GetModelDoc2'))
            exigir(not externas,'El grupo conserva enlaces externos')
            grupos_dep.append({'archivo':Path(leer(c,'GetPathName')).name,'dependencias_externas':externas})
        (EVIDENCIA/'dependencias_nativas.json').write_text(json.dumps({
            'aprobado':True,'dependencias_ensamblaje':deps,'grupos':grupos_dep,
            'requiere_STEP_para_abrir':False},indent=2,ensure_ascii=False),encoding='utf-8')
        asm.ShowNamedView2('',7);asm.ViewZoomtofit2()
        propios.remove(asm)
        informe['estado']='GUARDADO Y REABIERTO; revisión física pendiente'
    except Exception as e:
        informe.update(estado='FALLIDO',error=str(e),traza=traceback.format_exc());raise
    finally:
        (EVIDENCIA/'verificacion_nativa.json').write_text(json.dumps(informe,indent=2,ensure_ascii=False),encoding='utf-8')
        for ruta in EVIDENCIA.glob('*.bmp'):
            Image.open(ruta).save(ruta.with_suffix('.png'))
        for m in reversed(propios):
            try:
                if str(leer(m,'GetTitle')) not in iniciales:sw.CloseDoc(leer(m,'GetTitle'))
            except Exception:pass
        try:
            for i,val in prev.items():sw.SetUserPreferenceToggle(i,val)
            sw.SetUserPreferenceIntegerValue(579,estructura);sw.SetUserPreferenceIntegerValue(201,modo_guardado)
        except Exception:pass
        if etapa in ('individuales','grupos') and not iniciales:
            try:sw.ExitApp()
            except Exception:pass


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--continuar',action='store_true')
    p.add_argument('--etapa',choices=['todo','individuales','grupos','ensamble'],default='todo')
    p.add_argument('--limite',type=int,default=0)
    a=p.parse_args();main(a.continuar,a.etapa,a.limite)
