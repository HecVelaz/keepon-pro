"""Lee las dependencias guardadas sin modificar los documentos del usuario."""
from pathlib import Path
import json
import sys
import argparse

R = Path(__file__).resolve().parent
sys.path.insert(0, 'C:/Users/mathi/.codex/skills/solidworks-automation/scripts')
from sw_connect import connect_solidworks, get_com_member as leer, open_document


def dependencias(modelo):
    valores = list(leer(modelo, 'GetDependencies2', False, True, False) or [])
    assert len(valores) % 2 == 0, 'Respuesta de dependencias inesperada'
    return [str(valores[i]) for i in range(1, len(valores), 2)]


def main(dejar_abierto=False):
    sw, _ = connect_solidworks(version=2021, wait_seconds=30)
    sw.UserControl = True
    salida = R / 'SOLIDWORKS_V6'
    ruta = salida / 'Keepon_V6_nominal.SLDASM'
    modelo = leer(sw, 'GetOpenDocumentByName', str(ruta))
    abierto_aqui = modelo is None
    if abierto_aqui:
        modelo = open_document(sw, str(ruta), silent=True, raise_on_error=True)
    try:
        deps = dependencias(modelo)
        assert len(deps) == 4, f'Dependencias inesperadas: {deps}'
        assert all(Path(p).parent == salida and Path(p).is_file() for p in deps)
        grupos = []
        for c in leer(modelo, 'GetComponents', False) or []:
            parte = leer(c, 'GetModelDoc2')
            assert parte is not None, 'Grupo no resuelto'
            otras = dependencias(parte)
            assert not otras, f'El grupo conserva referencias externas: {otras}'
            grupos.append({'archivo': Path(leer(c, 'GetPathName')).name,
                           'dependencias_externas': otras})
        evidencia = {'aprobado': True, 'dependencias_ensamblaje': deps,
                     'grupos': grupos, 'requiere_STEP_para_abrir': False,
                     'nota': 'Lectura COM de los archivos guardados; conservar los cuatro grupos junto al SLDASM.'}
        (R / 'evidencias/solidworks_v6/dependencias_nativas.json').write_text(
            json.dumps(evidencia, indent=2, ensure_ascii=False), encoding='utf-8')
        print(json.dumps(evidencia, ensure_ascii=False))
    finally:
        if abierto_aqui and not dejar_abierto:
            sw.CloseDoc(leer(modelo, 'GetTitle'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dejar-abierto', action='store_true')
    main(parser.parse_args().dejar_abierto)
