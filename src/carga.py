"""Genera SQL reproducible desde los CSV y, opcionalmente, lo ejecuta en Supabase."""

import argparse
import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path

from db import ROOT, archivo_sql, consultar
from ingesta import PROVINCIAS, TECNOLOGIAS


def literal(valor):
    return "'" + str(valor).replace("'", "''") + "'"


def leer_csv(carpeta, nombre):
    with (carpeta / nombre).open(encoding='utf-8-sig', newline='') as archivo:
        return list(csv.DictReader(archivo))


def generar():
    reporte = json.loads((ROOT / 'reportes' / 'ingesta_ultima.json').read_text(encoding='utf-8'))
    if reporte['estado'] not in ('completada', 'completada_con_observaciones'):
        raise ValueError('La ultima ingesta no termino; no se puede cargar')
    carpeta = (ROOT / reporte['carpeta_csv']).resolve()
    if not carpeta.is_relative_to(ROOT / 'data' / 'clean'):
        raise ValueError('Carpeta de datos fuera del proyecto')
    accesos = leer_csv(carpeta, 'accesos_tecnologia.csv')
    velocidad = leer_csv(carpeta, 'velocidad_historica.csv')
    totales = leer_csv(carpeta, 'totales_publicados.csv')
    if not accesos or not velocidad or not totales:
        raise ValueError('Hay CSV vacios')
    # Todo se valida antes de generar sentencias. Los textos SQL se escapan.
    for filas, campo in [(accesos, 'accesos'), (velocidad, 'mbps'), (totales, 'total_publicado')]:
        claves = set()
        for fila in filas:
            if fila['provincia'] not in PROVINCIAS or not 1 <= int(fila['trimestre']) <= 4:
                raise ValueError('Provincia o trimestre no valido')
            if int(fila['anio']) < 2014:
                raise ValueError('Anio no valido')
            valor = Decimal(fila[campo])
            if not valor.is_finite() or valor < 0 or (campo != 'mbps' and valor != int(valor)):
                raise ValueError('Cantidad o velocidad no valida')
            llave = (fila['provincia'], fila['anio'], fila['trimestre'], fila.get('tecnologia'))
            if llave in claves:
                raise ValueError('Hay claves duplicadas en el CSV')
            claves.add(llave)
            if 'tecnologia' in fila and fila['tecnologia'] not in TECNOLOGIAS.values():
                raise ValueError('Tecnologia no reconocida')
    nombres = sorted({f['provincia'] for f in accesos + velocidad + totales})
    periodos = sorted({(int(f['anio']), int(f['trimestre'])) for f in accesos + velocidad + totales})
    lotes = [
        'INSERT INTO telecom.provincia(nombre) VALUES ' + ','.join(f'({literal(n)})' for n in nombres)
        + ' ON CONFLICT (nombre) DO NOTHING;',
        'INSERT INTO telecom.periodo(anio,trimestre) VALUES ' + ','.join(f'({a},{t})' for a,t in periodos)
        + ' ON CONFLICT (anio,trimestre) DO NOTHING;',
        'INSERT INTO telecom.tecnologia(codigo,nombre) VALUES '
        + ','.join(f'({literal(codigo)},{literal(nombre)})' for nombre,codigo in TECNOLOGIAS.items())
        + ' ON CONFLICT (codigo) DO UPDATE SET nombre=EXCLUDED.nombre;',
    ]
    for filas, tabla, columna_csv, columna_db in [
        (accesos, 'acceso', 'accesos', 'cantidad'),
        (velocidad, 'velocidad', 'mbps', 'mbps'),
        (totales, 'total_publicado', 'total_publicado', 'cantidad'),
    ]:
        es_acceso = tabla == 'acceso'
        for inicio in range(0, len(filas), 300):
            valores = []
            for fila in filas[inicio:inicio+300]:
                campos = [literal(fila['provincia']), str(int(fila['anio'])), str(int(fila['trimestre']))]
                if es_acceso:
                    campos.append(literal(fila['tecnologia']))
                campos.append(str(Decimal(fila[columna_csv])))
                valores.append('(' + ','.join(campos) + ')')
            extra = ',tecnologia_codigo' if es_acceso else ''
            cte = f'WITH entrada(provincia,anio,trimestre{extra},{columna_db}) AS (VALUES '
            cte += ','.join(valores) + ')\n'
            cte += f'INSERT INTO telecom.{tabla}(provincia_id,anio,trimestre{extra},{columna_db})\n'
            cte += 'SELECT p.provincia_id,e.anio,e.trimestre'
            cte += ',e.tecnologia_codigo' if es_acceso else ''
            cte += f',e.{columna_db} FROM entrada e JOIN telecom.provincia p ON p.nombre=e.provincia\n'
            cte += f'ON CONFLICT (provincia_id,anio,trimestre{extra}) DO UPDATE SET {columna_db}=EXCLUDED.{columna_db};'
            lotes.append(cte)
    destino = ROOT / 'data' / 'carga' / reporte['ejecucion']
    destino.mkdir(parents=True, exist_ok=True)
    for i, lote in enumerate(lotes):
        (destino / f'{i:03}.sql').write_text(lote, encoding='utf-8')
    completa = 'BEGIN;\n' + '\n'.join(lotes) + '\nCOMMIT;'
    (destino / 'carga_completa.sql').write_text(completa, encoding='utf-8')
    resumen = {'ingesta': reporte['ejecucion'], 'carpeta': str(destino.relative_to(ROOT)),
               'lotes': len(lotes), 'filas_esperadas': {'provincia':len(nombres), 'periodo':len(periodos),
               'tecnologia':len(TECNOLOGIAS), 'acceso':len(accesos), 'velocidad':len(velocidad),
               'total_publicado':len(totales)}, 'sha256_sql':hashlib.sha256(completa.encode()).hexdigest(),
               'estado':'generada_no_ejecutada'}
    (ROOT / 'reportes' / 'carga_preparada.json').write_text(json.dumps(resumen, indent=2), encoding='utf-8')
    return completa, resumen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ejecutar', action='store_true', help='Crear esquema y cargar con el token del entorno')
    args = parser.parse_args()
    sql, resumen = generar()
    if args.ejecutar:
        consultar(archivo_sql('01_esquema.sql'))
        consultar(sql)  # Una transaccion: si falla, se revierten todas las inserciones.
        conteos = consultar("SELECT jsonb_build_object(" + ','.join(
            f"'{tabla}',(SELECT count(*) FROM telecom.{tabla})" for tabla in resumen['filas_esperadas']
        ) + ') AS conteos;')[0]['conteos']
        if conteos != resumen['filas_esperadas']:
            raise ValueError('Los conteos de la base no coinciden con la carga; revisar antes de continuar')
        resumen['estado'] = 'ejecutada'
        (ROOT / 'reportes' / 'carga_ejecutada.json').write_text(json.dumps(resumen, indent=2), encoding='utf-8')
    print(json.dumps(resumen, indent=2))


if __name__ == '__main__':
    main()
