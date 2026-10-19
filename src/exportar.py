"""Exporta las tres vistas SQL y las combina en una tabla para Looker Studio."""

import argparse
import json
from datetime import datetime, timezone

from db import ROOT, consultar
from ingesta import escribir_csv

VISTAS = ['v_radiografia','v_crecimiento','v_ranking']


def obtener_vistas():
    resultado = {}
    for vista in VISTAS:
        # JSON agrega las 1.200 filas en una respuesta, evitando limites por filas de API.
        query = f'SELECT jsonb_agg(v ORDER BY anio,trimestre,provincia) AS filas FROM telecom.{vista} v;'
        resultado[vista] = consultar(query)[0]['filas']
    captura = {'project_ref':json.loads((ROOT/'proyecto.json').read_text())['supabase_project_ref'],
               'capturado_en_utc':datetime.now(timezone.utc).isoformat(), 'vistas':resultado}
    (ROOT/'data'/'vistas_snapshot.json').write_text(json.dumps(captura,ensure_ascii=False,indent=2),encoding='utf-8')
    return captura


def clave(f):
    return f['provincia_id'], f['anio'], f['trimestre']


def exportar(captura):
    autorizado = json.loads((ROOT/'proyecto.json').read_text())['supabase_project_ref']
    if captura['project_ref'] != autorizado:
        raise ValueError('Captura de otro proyecto: operacion detenida')
    vistas = captura['vistas']
    indices = {}
    for vista in VISTAS:
        filas = vistas[vista]
        if not filas:
            raise ValueError(f'Vista vacia: {vista}')
        indices[vista] = {clave(f):f for f in filas}
        if len(indices[vista]) != len(filas):
            raise ValueError(f'Vista con claves duplicadas: {vista}')
    if not (set(indices[VISTAS[0]]) == set(indices[VISTAS[1]]) == set(indices[VISTAS[2]])):
        raise ValueError('Las vistas no tienen las mismas claves')
    tablero = []
    for fila in vistas['v_radiografia']:
        llave = clave(fila)
        crecimiento = indices['v_crecimiento'][llave]
        ranking = indices['v_ranking'][llave]
        base = crecimiento['accesos_hace_un_anio']
        tablero.append(dict(fila,
            accesos_hace_un_anio=base,
            accesos_comparables=fila['accesos_totales'] if base is not None else None,
            crecimiento_interanual_pct=crecimiento['crecimiento_interanual_pct'],
            ranking_velocidad=ranking['ranking_velocidad'], ranking_accesos=ranking['ranking_accesos']))
    destino = ROOT/'exports'
    destino.mkdir(exist_ok=True)
    for nombre, filas in {**vistas,'tablero':tablero}.items():
        escribir_csv(destino/f'{nombre}.csv',list(filas[0]),filas)
    reporte = {'capturado_en_utc':captura['capturado_en_utc'],
               'filas':{k:len(v) for k,v in {**vistas,'tablero':tablero}.items()},
               'ultimo_periodo':max((f['anio'],f['trimestre']) for f in tablero),
               'advertencia':'Los CSV son una foto: el tablero no se actualiza solo.'}
    (ROOT/'reportes'/'exportacion.json').write_text(json.dumps(reporte,indent=2),encoding='utf-8')
    print(json.dumps(reporte,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--desde-captura',action='store_true',help='Usar las vistas reales ya guardadas sin red')
    args = parser.parse_args()
    captura = json.loads((ROOT/'data'/'vistas_snapshot.json').read_text(encoding='utf-8')) if args.desde_captura else obtener_vistas()
    exportar(captura)
