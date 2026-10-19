"""Guarda una fotografia de las tablas de nuestro proyecto para controles locales."""

import json
from db import ROOT, archivo_sql, consultar


def capturar():
    datos = consultar(archivo_sql('05_captura.sql'))[0]['captura']
    datos['project_ref'] = json.loads((ROOT/'proyecto.json').read_text(encoding='utf-8'))['supabase_project_ref']
    destino = ROOT / 'data' / 'base_snapshot.json'
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding='utf-8')
    return datos


if __name__ == '__main__':
    datos = capturar()
    print(json.dumps({t: len(filas or []) for t, filas in datos['tablas'].items()}, indent=2))
