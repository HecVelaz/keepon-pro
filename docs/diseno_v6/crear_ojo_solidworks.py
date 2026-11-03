"""Importa el STEP del ojo en SolidWorks 2021, guarda y verifica una pieza nativa.

Sólo abre y cierra los documentos creados en esta ejecución. El árbol nativo
contiene un sólido importado; las dimensiones editables están en generar_ojos.py.
"""
from pathlib import Path
import json
import sys

RAIZ = Path(__file__).resolve().parent
SKILL = Path('C:/Users/mathi/.codex/skills/solidworks-automation/scripts')
sys.path.insert(0, str(SKILL))
from sw_connect import connect_solidworks, open_document, save_document, get_com_member
from sw_review import run_review


def main():
    paso = RAIZ / 'STEP/ojo_adhesivo.step'
    salida = RAIZ / 'SOLIDWORKS/ojo_adhesivo.SLDPRT'
    evidencia = RAIZ / 'evidencias/solidworks'
    if salida.exists():
        raise FileExistsError(f'No se sobrescribe el archivo existente: {salida}')
    salida.parent.mkdir(exist_ok=True)
    evidencia.mkdir(parents=True, exist_ok=True)
    sw, _ = connect_solidworks(version=2021, wait_seconds=10)
    if sw.GetOpenDocumentByName(str(paso)) is not None:
        raise RuntimeError('El STEP ya está abierto; no se modificará el documento existente.')
    modelo = open_document(sw, str(paso), raise_on_error=True)
    if get_com_member(modelo, 'GetType') != 1:
        raise RuntimeError('El STEP no se importó como pieza.')
    if not modelo.ForceRebuild3(False):
        raise RuntimeError('Falló la reconstrucción del STEP.')
    if not save_document(modelo, str(salida)) or not salida.is_file():
        raise RuntimeError('No se guardó la pieza nativa.')
    sw.CloseDoc(get_com_member(modelo, 'GetTitle'))
    modelo = open_document(sw, str(salida), silent=True, raise_on_error=True)
    cuerpos = list(get_com_member(modelo, 'GetBodies2', 0, False) or [])
    if len(cuerpos) != 1:
        raise RuntimeError(f'Se esperaba un cuerpo sólido; se obtuvieron {len(cuerpos)}.')
    caja = list(get_com_member(modelo, 'GetPartBox', True))
    dimensiones = [1000 * (caja[i + 3] - caja[i]) for i in range(3)]
    if any(abs(a - b) > 0.05 for a, b in zip(dimensiones, (36, 40, 1.2))):
        raise RuntimeError(f'Dimensiones inesperadas: {dimensiones}')
    if not modelo.ForceRebuild3(False):
        raise RuntimeError('Falló la reconstrucción de la pieza reabierta.')
    modelo.ViewZoomtofit2()
    informe, _ = run_review(modelo, str(evidencia), basename='ojo', expected_outputs=[str(salida)])
    datos = {'version': 'SolidWorks 2021', 'cuerpos_solidos': len(cuerpos),
             'dimensiones_mm': dimensiones, 'reabierto': True,
             'arbol': 'Sólido importado de STEP; editar parámetros en generar_ojos.py',
             'evaluacion': informe.get('evaluation')}
    (evidencia / 'verificacion.json').write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(datos, ensure_ascii=False))
    sw.CloseDoc(get_com_member(modelo, 'GetTitle'))


if __name__ == '__main__':
    main()
