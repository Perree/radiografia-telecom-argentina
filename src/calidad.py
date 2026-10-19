"""Controla datos reales de la base y su correspondencia con los CSV de la ingesta."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from decimal import Decimal

from captura import capturar
from carga import leer_csv
from db import ROOT

CLAVES = {
    'provincia': ('provincia_id',), 'periodo': ('anio', 'trimestre'),
    'tecnologia': ('codigo',), 'acceso': ('provincia_id','anio','trimestre','tecnologia_codigo'),
    'velocidad': ('provincia_id','anio','trimestre'),
    'total_publicado': ('provincia_id','anio','trimestre'),
}
REQUERIDOS = {
    'provincia': (*CLAVES['provincia'], 'nombre'), 'periodo': CLAVES['periodo'],
    'tecnologia': ('codigo','nombre'), 'acceso': (*CLAVES['acceso'],'cantidad'),
    'velocidad': (*CLAVES['velocidad'],'mbps'),
    'total_publicado': (*CLAVES['total_publicado'],'cantidad'),
}


def decimal_seguro(valor):
    try:
        numero = Decimal(str(valor))
        return numero if numero.is_finite() else None
    except Exception:
        return None


def revisar(datos):
    autorizado = json.loads((ROOT / 'proyecto.json').read_text(encoding='utf-8'))['supabase_project_ref']
    if datos['project_ref'] != autorizado:
        raise ValueError('La captura no corresponde al proyecto autorizado')
    tablas = datos['tablas']
    controles = []

    def agregar(control, tabla, errores, detalle, estado=None):
        controles.append(dict(control=control, tabla=tabla, errores=errores,
                              estado=estado or ('OK' if errores == 0 else 'ERROR'), detalle=detalle))

    for tabla, columnas in REQUERIDOS.items():
        filas = tablas[tabla] or []
        agregar('tabla_no_vacia', tabla, int(not filas), f'{len(filas)} filas')
        agregar('nulos_obligatorios', tabla,
                sum(f.get(c) is None or f.get(c) == '' for f in filas for c in columnas),
                'Cada campo obligatorio debe tener valor; cero es valido')
        conteo = Counter(tuple(f.get(c) for c in CLAVES[tabla]) for f in filas)
        agregar('claves_duplicadas', tabla, sum(n-1 for n in conteo.values()), 'Clave: '+', '.join(CLAVES[tabla]))
    provincias = {f['provincia_id'] for f in tablas['provincia']}
    nombres = {f['provincia_id']: f['nombre'] for f in tablas['provincia']}
    periodos = {(f['anio'], f['trimestre']) for f in tablas['periodo']}
    tecnologias = {f['codigo'] for f in tablas['tecnologia']}
    agregar('24_jurisdicciones', 'provincia', abs(len(provincias)-24), '23 provincias y CABA')
    agregar('rango_periodo', 'periodo', sum(a < 2014 or t not in (1,2,3,4) for a,t in periodos),
            'Anio >= 2014 y trimestre entre 1 y 4')
    secuencia = {a*4+t for a,t in periodos}
    faltantes = sorted(set(range(min(secuencia),max(secuencia)+1))-secuencia) if secuencia else []
    agregar('continuidad_trimestral', 'periodo', len(faltantes), f'Periodos faltantes: {faltantes}')
    for tabla in ('acceso', 'velocidad', 'total_publicado'):
        filas = tablas[tabla]
        agregar('fk_provincia', tabla, sum(f['provincia_id'] not in provincias for f in filas), 'La provincia referida debe existir')
        agregar('fk_periodo', tabla, sum((f['anio'],f['trimestre']) not in periodos for f in filas), 'El periodo referido debe existir')
        campo = 'mbps' if tabla == 'velocidad' else 'cantidad'
        malos = 0
        for f in filas:
            try:
                v = Decimal(str(f[campo]))
                if not v.is_finite() or v < 0 or (campo == 'cantidad' and v != int(v)):
                    malos += 1
            except Exception:
                malos += 1
        agregar('rango_numerico', tabla, malos, 'No negativo, finito y entero si cuenta accesos; sin tope arbitrario de velocidad')
        claves = {tuple(f[c] for c in CLAVES[tabla]) for f in filas}
        esperadas = {(p,a,t,tec) for p in provincias for a,t in periodos for tec in tecnologias} if tabla=='acceso' else {(p,a,t) for p in provincias for a,t in periodos}
        agregar('cobertura_completa', tabla, len(esperadas-claves), 'Combinaciones esperadas sin observacion; no se rellenan')
    agregar('fk_tecnologia', 'acceso', sum(f['tecnologia_codigo'] not in tecnologias for f in tablas['acceso']), 'La tecnologia referida debe existir')
    suma = defaultdict(int)
    for f in tablas['acceso']:
        valor = decimal_seguro(f['cantidad'])
        if valor is not None:
            suma[(f['provincia_id'],f['anio'],f['trimestre'])] += valor
    diferencias = sum(suma.get((f['provincia_id'],f['anio'],f['trimestre'])) != f['cantidad'] for f in tablas['total_publicado'])
    agregar('suma_vs_total_publicado', 'acceso', diferencias, 'Suma de tecnologias contra total de ENACOM')
    agregar('ceros_publicados', 'acceso', 0, f"{sum(f['cantidad']==0 for f in tablas['acceso'])} cantidades cero conservadas", 'INFO')
    ingesta = json.loads((ROOT/'reportes'/'ingesta_ultima.json').read_text(encoding='utf-8'))
    if ingesta['estado'] not in ('completada','completada_con_observaciones'):
        raise ValueError('La ingesta a comparar no termino correctamente')
    carpeta = (ROOT/ingesta['carpeta_csv']).resolve()
    if not carpeta.is_relative_to(ROOT/'data'/'clean'):
        raise ValueError('Los CSV deben estar dentro de este proyecto')
    for tabla, archivo, campo_csv, campo_db in [
        ('acceso','accesos_tecnologia.csv','accesos','cantidad'),
        ('velocidad','velocidad_historica.csv','mbps','mbps'),
        ('total_publicado','totales_publicados.csv','total_publicado','cantidad'),
    ]:
        fuente = leer_csv(carpeta,archivo)
        def llave_csv(f):
            return (f['provincia'],int(f['anio']),int(f['trimestre'])) + ((f['tecnologia'],) if tabla=='acceso' else ())
        def llave_db(f):
            return (nombres.get(f['provincia_id']),f['anio'],f['trimestre']) + ((f['tecnologia_codigo'],) if tabla=='acceso' else ())
        esperado = {llave_csv(f):Decimal(f[campo_csv]) for f in fuente}
        obtenido = {llave_db(f):decimal_seguro(f[campo_db]) for f in tablas[tabla]}
        distintas = sum(esperado.get(k) != obtenido.get(k) for k in set(esperado)|set(obtenido))
        agregar('csv_vs_base', tabla, distintas, 'Compara claves Y valores: no alcanza con contar filas')
    velocidades = {(nombres.get(f['provincia_id']),f['anio'],f['trimestre']):decimal_seguro(f['mbps']) for f in tablas['velocidad']}
    api = leer_csv(carpeta,'velocidad_api.csv')
    agregar('api_vs_base', 'velocidad', sum(velocidades.get((f['provincia'],int(f['anio']),int(f['trimestre']))) != Decimal(f['mbps']) for f in api),
            f'{len(api)} velocidades de la API contrastadas con la base')
    return controles


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--desde-captura', action='store_true', help='Usar la fotografia local sin consultar la base')
    args = parser.parse_args()
    datos = json.loads((ROOT/'data'/'base_snapshot.json').read_text(encoding='utf-8')) if args.desde_captura else capturar()
    controles = revisar(datos)
    destino = ROOT/'reportes'/'reporte_calidad.csv'
    with destino.open('w',encoding='utf-8-sig',newline='') as archivo:
        escritor = csv.DictWriter(archivo,fieldnames=['control','tabla','errores','estado','detalle'])
        escritor.writeheader()
        escritor.writerows(controles)
    errores = sum(f['errores'] for f in controles if f['estado']=='ERROR')
    print(f'Controles: {len(controles)}. Incidencias: {errores}. Captura: {datos["capturado_en_utc"]}')
    print('Modo: captura local' if args.desde_captura else 'Modo: consulta nueva a la base')
    if errores:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
