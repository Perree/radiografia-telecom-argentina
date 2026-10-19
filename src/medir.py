"""Mide la consulta antes/despues del unico indice didactico de este proyecto."""

import argparse
import json
from statistics import median
from db import ROOT, archivo_sql, consultar


def resumir(planes):
    def nodos(plan):
        return [plan['Node Type']] + [tipo for hijo in plan.get('Plans',[]) for tipo in nodos(hijo)]
    return {
        'mediana_antes_ms': median(p['Execution Time'] for p in planes['antes']),
        'mediana_despues_ms': median(p['Execution Time'] for p in planes['despues']),
        'planes_antes': nodos(planes['antes'][0]['Plan']),
        'planes_despues': nodos(planes['despues'][0]['Plan']),
        'nota': 'Tres mediciones por etapa; tiempo de ejecucion del servidor, sin latencia de red. No prueba carga de produccion.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solo-resumir', action='store_true', help='Resume los planes reales ya guardados, sin conectarse')
    parser.add_argument('--reiniciar-indice', action='store_true', help='Recrea solo idx_acceso_tecnologia_anio para repetir la medicion')
    args = parser.parse_args()
    destino = ROOT/'reportes'/'planes_performance.json'
    if args.solo_resumir:
        planes = json.loads(destino.read_text(encoding='utf-8'))
    else:
        existe = consultar("SELECT to_regclass('telecom.idx_acceso_tecnologia_anio') IS NOT NULL AS existe")[0]['existe']
        if existe and not args.reiniciar_indice:
            raise ValueError('El indice ya existe. Usa --reiniciar-indice para medir nuevamente antes/despues.')
        if existe:
            consultar('DROP INDEX telecom.idx_acceso_tecnologia_anio;')
        consultar('ANALYZE telecom.acceso;')
        consulta = 'EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)\n' + archivo_sql('03_consulta_performance.sql')
        consultar(consulta)  # Calentamiento: no se incluye en las tres mediciones.
        planes = {'consulta':consulta,'antes':[],'despues':[]}
        for _ in range(3):
            planes['antes'].append(consultar(consulta)[0]['QUERY PLAN'][0])
        consultar(archivo_sql('04_indice.sql'))
        for _ in range(3):
            planes['despues'].append(consultar(consulta)[0]['QUERY PLAN'][0])
        destino.write_text(json.dumps(planes,ensure_ascii=False,indent=2),encoding='utf-8')
    resumen = resumir(planes)
    (ROOT/'reportes'/'performance_resumen.json').write_text(json.dumps(resumen,indent=2),encoding='utf-8')
    print(json.dumps(resumen,indent=2))


if __name__ == '__main__':
    main()
