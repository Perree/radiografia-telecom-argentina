"""Ejecuta en orden los pasos del proyecto y se detiene si alguno falla."""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from db import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sin-red',action='store_true',help='Reprocesa originales y capturas existentes; NO crea ni actualiza la base')
    args = parser.parse_args()
    if args.sin_red:
        pasos = [
            ['ingesta.py','--desde','evidencia'], ['carga.py'],
            ['medir.py','--solo-resumir'], ['calidad.py','--desde-captura'],
            ['exportar.py','--desde-captura'],
        ]
    else:
        pasos = [
            ['ingesta.py'], ['carga.py','--ejecutar'],
            ['ejecutar_sql.py','02_vistas.sql'], ['medir.py','--reiniciar-indice'],
            ['calidad.py'], ['exportar.py'],
        ]
    reporte = {'fecha_utc':datetime.now(timezone.utc).isoformat(),
               'modo':'sin_red_no_actualiza_base' if args.sin_red else 'online',
               'pasos':[], 'estado':'en_ejecucion'}
    try:
        for paso in pasos:
            resultado = subprocess.run([sys.executable,str(ROOT/'src'/paso[0]),*paso[1:]],cwd=ROOT)
            reporte['pasos'].append({'programa':paso,'codigo_salida':resultado.returncode})
            if resultado.returncode:
                raise RuntimeError(f'Fallo {paso[0]}; no se ejecutaron los pasos posteriores')
        reporte['estado'] = 'completado'
    except Exception as error:
        reporte['estado'] = 'fallido'
        reporte['error'] = str(error)
        raise
    finally:
        (ROOT/'reportes'/'pipeline_ultima.json').write_text(json.dumps(reporte,indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
