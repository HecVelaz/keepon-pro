"""Consolida evidencias y crea un ZIP local de revisión, sin publicar nada."""
from pathlib import Path
import hashlib
import json
import zipfile
import shutil

R=Path(__file__).resolve().parent
def leer(ruta):return json.loads((R/ruta).read_text(encoding='utf-8'))


def main():
    nativo=leer('evidencias/solidworks_v6/verificacion_nativa.json')
    archivo=leer('evidencias/archivos_v6.json')
    acoples=leer('evidencias/solidworks_v6/interferencias_clasificadas.json')
    barrido=leer('evidencias/auditoria_v6.json')
    usb=leer('evidencias/USB_R1.json')
    dependencias=leer('evidencias/solidworks_v6/dependencias_nativas.json')
    regresiones=leer('evidencias/regresiones_v6.json')
    r2=leer('evidencias/R2_buzzer_ojos.json')
    inventario=leer('inventario_v6.json')
    assert nativo.get('reabierto') and len(nativo['poses'])==10,'Falta la reapertura o solver nativo'
    assert nativo['sha256_config']==hashlib.sha256((R/'config.yaml').read_bytes()).hexdigest(),'Ensamblaje de otra configuración'
    assert len(nativo['individuales'])==len(inventario)+1 and len(nativo['grupos'])==4,'Entrega nativa incompleta'
    assert archivo['aprobado_archivos'] and acoples['aprobado'] and barrido['aprobado_nominal'] and usb['aprobado_reserva']
    assert barrido['revision']=='R2_buzzer_ojos' and barrido['poses_representadas']==495
    assert barrido['sha256_config']==hashlib.sha256((R/'config.yaml').read_bytes()).hexdigest()
    for grupo in nativo['grupos']:
        paso=R/'STEP_V6'/f"v6_grupo_{grupo['nombre']}.step"
        assert grupo['sha256_step']==hashlib.sha256(paso.read_bytes()).hexdigest(),'Grupo nativo desactualizado'
    assert dependencias['aprobado'] and not dependencias['requiere_STEP_para_abrir']
    assert regresiones['revision']=='R2_buzzer_ojos' and regresiones['pruebas_ejecutadas']==13 and regresiones['fallos']==0 and regresiones['errores']==0
    assert r2['aprobado_geometria_R2'] and usb['revision']=='R2_buzzer_ojos'
    assert not (R/'STEP_V6/14_tapa_usb.step').exists(),'Queda la tapa retirada en la entrega activa'
    resumen={'revision':'R2_buzzer_ojos','estado':'Entrega CAD nominal verificada; fabricación condicionada a mediciones',
             'SLDPRT_individuales':len(nativo['individuales']),'grupos_nativos':len(nativo['grupos']),
             'SLDASM_reabierto':True,'poses_solver':len(nativo['poses']),
             'dependencias_nativas_completas':True,
             'poses_barrido':495,'poses_reserva_USB_lado_negativo_Y':len(usb['poses']),
             'holgura_minima_reserva_USB_mm':usb['holgura_minima_muestreada_mm'],
             'regresiones_aprobadas':regresiones['pruebas_ejecutadas'],
             'cambios_R2':['04_cuba_cabeza','15_soporte_RLBZ23','16_ojo_izq','17_ojo_der','19_lente_ojo_izq','20_lente_ojo_der','21_arandela_buzzer'],
             'retiradas':['14_tapa_usb','15_portamodulo_RLBZ23_ajustable'],
             'PCB_RLBZ23_mm':r2['PCB_medido_mm'],'centro_agujero_desde_bordes_mm':r2['centro_agujero_desde_bordes_mm'],
             'STL_revision_verificados':len(archivo['piezas']),'acoples_nativos_justificados':len(acoples['acoples_identificados']),
             'base_original_modificada':False,'apto_para_fabricar_conjunto':False,
             'pendientes':['Perfil del brazo simple y ajuste de dobles','Roscas reales de base y salida del cable RDS',
                          'Altura/componentes/conectores RLBZ23 y zona libre de apoyo','Conector USB, cable y radio de curvatura',
                          'Material e insertos: cupón','Fijación M2 de cámara y tornillos propios de servo',
                          'Prueba física de recorrido, carga y refrigeración']}
    (R/'evidencias/resumen_entrega_v6.json').write_text(json.dumps(resumen,indent=2,ensure_ascii=False),encoding='utf-8')
    texto=f'''# Resultado de la entrega V6

Se guardaron y reabrieron {resumen['SLDPRT_individuales']} piezas individuales y
el ensamblaje SolidWorks 2021 con cuatro grupos rígidos, seis relaciones y
diez poses resueltas. Los tres acoples eje/horn se identificaron por pareja y
volumen; no hubo otras interferencias nativas reportadas.

R2 retira la tapa14 y sus cuatro M3, crea dos aberturas posteriores simétricas
de36 ×26 mm y conserva la cuna R1. Actualiza soporte15 al PCB medido RLBZ23
de13 ×31,8 ×1,5 mm, agujeroØ3 con centro a6,3/16,4 desde bordes; buzzer abajo
y pines arriba. Carcasas16/17 espejadas con estética WALL-E y lentes19/20
pegables aparte; arandela21 y M3×5 para el PCB.

Se repitió el barrido B-Rep completo de 495 poses con los M3×6 finales.
Una reserva USB de diseño pasa 41 poses de roll cada grado, con mínimo
muestreado 0,69 mm del lado Y negativo. No representa un enchufe físico.
Los {len(inventario)} STEP/STL de revisión pasaron geometría de archivo y
orientación; {regresiones['pruebas_ejecutadas']} regresiones están aprobadas.

La base V5 no se modificó. El modelo integrado incorpora soportes, encastres
nominales, retenciones, salida USB, cámara, portamódulo y ojos. El perfil de
pitch es una referencia de estudio de una rama. Se modela el PCB del RLBZ23;
alturas/componentes/pines y enchufes aún faltan medir. Por eso el conjunto
no se libera para fabricar. Consultar README y MEDICIONES_PENDIENTES.

Para abrir la entrega, extraer el ZIP y mantener todos los SLDPRT junto al
SLDASM dentro de SOLIDWORKS_V6. Se leyeron las dependencias guardadas de
los cuatro grupos: no tienen referencias externas ni requieren los STEP.
Para regenerar el CAD se requiere el repositorio con las fuentes V2–V5,
CadQuery y la instalación local indicada; el ZIP permite revisar los modelos
sin disponer de Python.
'''
    (R/'INFORME_ENTREGA_V6.md').write_text(texto,encoding='utf-8')
    carpetas=['STEP_V6','SOLIDWORKS_V6','STL_REVISION_NO_IMPRIMIR','IMPRESION_STL','vistas','documentacion','evidencias']
    archivos=[p for p in R.iterdir() if p.is_file() and p.name!='manifest_v6.json'
              and p.suffix.lower() in ('.py','.yaml','.md','.json')]
    archivos += [p for c in carpetas for p in (R/c).rglob('*') if p.is_file() and not p.name.startswith('~$') and p.suffix.lower() not in ('.bmp','.pyc')]
    # Diagnósticos exploratorios conservados localmente, fuera de la entrega.
    omitir={'comparacion_roll_por_cuerpo.json','comparacion_roll_por_pieza.json',
            'diagnostico_roll.json','roll_reexportado.step','auditoria_v6_rapida.json',
            'reduccion_tornillos.json','regresiones_USB_R1.json'}
    archivos=[p for p in archivos if p.name not in omitir]
    archivos=sorted(set(archivos))
    manifest=[{'archivo':str(p.relative_to(R)).replace('\\','/'),'bytes':p.stat().st_size,
               'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in archivos if p.name!='manifest_v6.json']
    man=R/'manifest_v6.json';man.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    destino=R/'Keepon_V6_R2_buzzer_ojos.zip'
    with zipfile.ZipFile(destino,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in archivos+[man]:z.write(p,Path('diseno_v6')/p.relative_to(R))
    with zipfile.ZipFile(destino) as z:
        assert z.testzip() is None
        for fila in manifest:
            contenido=z.read('diseno_v6/'+fila['archivo'])
            assert hashlib.sha256(contenido).hexdigest()==fila['sha256']
    shutil.copyfile(destino,R/'Keepon_V6_revision.zip')
    print(json.dumps({**resumen,'zip':str(destino),'bytes_zip':destino.stat().st_size},ensure_ascii=False))


if __name__=='__main__':main()
