"""Descarga fuentes oficiales, valida formatos y exporta CSV, sin paquetes externos."""

import argparse
import csv
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.request import Request, urlopen

from verificar_fuentes import leer_tabla

ROOT = Path(__file__).resolve().parents[1]
FUENTES = {
    'accesos.html': 'https://indicadores.enacom.gob.ar/DatosAbiertos/Internet/accesos-tecnologias-provincias',
    'velocidad.html': 'https://indicadores.enacom.gob.ar/DatosAbiertos/Internet/velocidad-media-provincias',
    'velocidad_api.json': 'https://indicadores.enacom.gob.ar/DatosAbiertos.asmx/InternetVMDProvinciasUltimoPeriodo',
}
TECNOLOGIAS = {
    'ADSL': 'adsl', 'Cablemodem': 'cablemodem', 'Fibra Optica': 'fibra_optica',
    'Wireless': 'inalambrico', 'Otros': 'otros',
}
PROVINCIAS = {
    'Buenos Aires', 'CABA', 'Catamarca', 'Chaco', 'Chubut', 'Córdoba',
    'Corrientes', 'Entre Ríos', 'Formosa', 'Jujuy', 'La Pampa', 'La Rioja',
    'Mendoza', 'Misiones', 'Neuquén', 'Río Negro', 'Salta', 'San Juan',
    'San Luis', 'Santa Cruz', 'Santa Fe', 'Santiago Del Estero',
    'Tierra Del Fuego', 'Tucumán',
}


def texto(valor):
    if not isinstance(valor, str):
        raise ValueError('Se esperaba texto')
    return ' '.join(unicodedata.normalize('NFC', valor).split())


def numero_local(valor, entero=False):
    """Interpreta solo el formato publicado: punto de miles, coma decimal."""
    valor = texto(valor)
    patron = r'(?:\d{1,3}(?:\.\d{3})+|\d+)'
    if not entero:
        patron += r'(?:,\d+)?'
    if not re.fullmatch(patron, valor):
        raise ValueError(f'Formato numerico inesperado: {valor!r}')
    convertido = Decimal(valor.replace('.', '').replace(',', '.'))
    return int(convertido) if entero else convertido


def clave(fila):
    anio = numero_local(str(fila['Año']), entero=True)
    trimestre = numero_local(str(fila['Trimestre']), entero=True)
    provincia = texto(fila['Provincia'])
    if not 2014 <= anio <= datetime.now(timezone.utc).year or trimestre not in (1, 2, 3, 4):
        raise ValueError('Anio o trimestre fuera del rango esperado')
    if provincia not in PROVINCIAS:
        raise ValueError(f'Jurisdiccion no reconocida: {provincia!r}')
    return anio, trimestre, provincia


def filas_unicas(filas, origen, reporte):
    """Descarta copias identicas; ante valores contradictorios, detiene el proceso."""
    unicas = {}
    for fila in filas:
        llave = clave(fila)
        if llave in unicas:
            if fila != unicas[llave]:
                raise ValueError(f'Duplicado contradictorio en {origen}, clave {llave}')
            reporte['duplicados_identicos_descartados'][origen] += 1
        else:
            unicas[llave] = fila
    return unicas


def descargar(carpeta):
    """Guarda exactamente los bytes recibidos. Nunca reutiliza una descarga fallida."""
    for archivo, url in FUENTES.items():
        solicitud = Request(url, headers={'User-Agent': 'RadiografiaTelecom/1.0 (proyecto educativo)'})
        with urlopen(solicitud, timeout=45) as respuesta:
            if respuesta.status != 200:
                raise ValueError(f'HTTP inesperado: {respuesta.status}')
            contenido = respuesta.read()
            if not contenido:
                raise ValueError(f'Respuesta vacia: {url}')
            (carpeta / archivo).write_bytes(contenido)


def escribir_csv(destino, columnas, filas):
    # UTF-8 con marca inicial ayuda a que Excel reconozca correctamente los acentos.
    with destino.open('w', encoding='utf-8-sig', newline='') as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas)


def procesar(carpeta, reporte):
    accesos = leer_tabla('accesos.html', 'datosInternetAccTecProvincias', carpeta)
    velocidades = leer_tabla('velocidad.html', 'datosInternetVMDProvincias', carpeta)
    api = json.loads((carpeta / 'velocidad_api.json').read_text(encoding='utf-8-sig'))
    if not isinstance(api, list) or not api:
        raise ValueError('La API no devolvio una lista con datos')
    esperadas_a = {'Año', 'Trimestre', 'Provincia', *TECNOLOGIAS, 'Total'}
    esperadas_v = {'Año', 'Trimestre', 'Provincia', 'Mbps (Media de bajada)'}
    esperadas_api = {'Id', 'Año', 'Trimestre', 'Provincia', 'Mbps'}
    for nombre, filas, columnas in [('accesos', accesos, esperadas_a),
                                       ('velocidad', velocidades, esperadas_v),
                                       ('api', api, esperadas_api)]:
        if any(set(fila) != columnas for fila in filas):
            raise ValueError(f'Cambio en las columnas de {nombre}: revisar la fuente')
        reporte['filas_originales'][nombre] = len(filas)
        reporte['celdas_vacias'][nombre] = sum(v is None or v == '' for f in filas for v in f.values())
    a = filas_unicas(accesos, 'accesos', reporte)
    v = filas_unicas(velocidades, 'velocidad', reporte)
    j = filas_unicas(api, 'api', reporte)
    largos, totales, limpias_v, limpias_api = [], [], [], []
    for llave, fila in sorted(a.items()):
        anio, trimestre, provincia = llave
        base = dict(anio=anio, trimestre=trimestre, provincia=provincia)
        valores = {nombre: numero_local(fila[columna], entero=True)
                   for columna, nombre in TECNOLOGIAS.items()}
        total = numero_local(fila['Total'], entero=True)
        suma = sum(valores.values())
        totales.append(dict(base, total_publicado=total, suma_tecnologias=suma))
        if total != suma:
            reporte['diferencias_totales'].append(dict(base, total_publicado=total,
                                                       suma_tecnologias=suma, diferencia=total-suma))
        for tecnologia, cantidad in valores.items():
            largos.append(dict(base, tecnologia=tecnologia, accesos=cantidad))
    valores_v = {}
    for llave, fila in sorted(v.items()):
        velocidad = numero_local(fila['Mbps (Media de bajada)'])
        valores_v[llave] = velocidad
        limpias_v.append(dict(anio=llave[0], trimestre=llave[1], provincia=llave[2], mbps=velocidad))
    for llave, fila in sorted(j.items()):
        # JSON ya usa punto decimal; no aplicamos la conversion regional del HTML.
        valor = fila['Mbps']
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ValueError(f'La API devolvio una velocidad no numerica: {llave}')
        velocidad = Decimal(str(valor))
        if not velocidad.is_finite() or velocidad < 0:
            raise ValueError(f'Velocidad invalida en la API: {llave}')
        limpias_api.append(dict(anio=llave[0], trimestre=llave[1], provincia=llave[2], mbps=velocidad))
        if llave not in valores_v or valores_v[llave] != velocidad:
            reporte['diferencias_api'].append(dict(anio=llave[0], trimestre=llave[1], provincia=llave[2],
                                                   mbps_api=str(velocidad),
                                                   mbps_tabla=str(valores_v.get(llave))))
    reporte['claves_sin_correspondencia'] = {
        'solo_accesos': sorted(set(a) - set(v)), 'solo_velocidad': sorted(set(v) - set(a)),
    }
    for nombre, filas in [('accesos', a), ('velocidad', v), ('api', j)]:
        conteos = Counter((llave[0], llave[1]) for llave in filas)
        reporte['cobertura'][nombre] = {
            'primer_periodo': min(conteos), 'ultimo_periodo': max(conteos),
            'cantidad_periodos': len(conteos),
            'periodos_con_menos_de_24_jurisdicciones': [p for p, n in sorted(conteos.items()) if n < 24],
        }
    return {
        'accesos_tecnologia.csv': (['anio', 'trimestre', 'provincia', 'tecnologia', 'accesos'], largos),
        'totales_publicados.csv': (['anio', 'trimestre', 'provincia', 'total_publicado', 'suma_tecnologias'], totales),
        'velocidad_historica.csv': (['anio', 'trimestre', 'provincia', 'mbps'], limpias_v),
        'velocidad_api.csv': (['anio', 'trimestre', 'provincia', 'mbps'], limpias_api),
    }


def ejecutar(desde=None):
    momento = datetime.now(timezone.utc).isoformat()
    identificador = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    carpeta = ROOT / 'data' / 'raw' / identificador
    carpeta.mkdir(parents=True)
    reporte = {
        'ejecucion': identificador, 'consultado_en_utc': momento,
        'modo': 'copia_local' if desde else 'descarga', 'estado': 'iniciada',
        'filas_originales': {}, 'celdas_vacias': {}, 'cobertura': {},
        'duplicados_identicos_descartados': {'accesos': 0, 'velocidad': 0, 'api': 0},
        'diferencias_totales': [], 'diferencias_api': [], 'fuentes': [],
    }
    try:
        if desde:
            origen = (ROOT / desde).resolve()
            if not origen.is_relative_to(ROOT):
                raise ValueError('Solo se permite leer archivos dentro de este proyecto')
            reporte['origen_local'] = str(origen.relative_to(ROOT))
            reporte['nota_fecha'] = 'La fecha es del procesamiento; no de la descarga original.'
            for archivo in FUENTES:
                (carpeta / archivo).write_bytes((origen / archivo).read_bytes())
        else:
            descargar(carpeta)
        for archivo, url in FUENTES.items():
            contenido = (carpeta / archivo).read_bytes()
            reporte['fuentes'].append(dict(url=url, archivo=str((carpeta / archivo).relative_to(ROOT)),
                                           bytes=len(contenido), sha256=hashlib.sha256(contenido).hexdigest()))
        resultados = procesar(carpeta, reporte)
        # Solo publicamos CSV si todas las fuentes pudieron interpretarse.
        salida = ROOT / 'data' / 'clean' / identificador
        salida.mkdir(parents=True)
        for nombre, (columnas, filas) in resultados.items():
            escribir_csv(salida / nombre, columnas, filas)
        reporte['csv'] = {n: len(f) for n, (_, f) in resultados.items()}
        reporte['carpeta_csv'] = str(salida.relative_to(ROOT))
        reporte['estado'] = 'completada_con_observaciones' if (
            reporte['diferencias_totales'] or reporte['diferencias_api'] or
            any(reporte['claves_sin_correspondencia'].values())) else 'completada'
    except Exception as error:
        reporte['estado'] = 'fallida'
        reporte['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        reportes = ROOT / 'reportes'
        reportes.mkdir(exist_ok=True)
        contenido = json.dumps(reporte, ensure_ascii=False, indent=2)
        (reportes / f'ingesta_{identificador}.json').write_text(contenido, encoding='utf-8')
        (reportes / 'ingesta_ultima.json').write_text(contenido, encoding='utf-8')
    print(json.dumps({k: reporte[k] for k in ['estado', 'csv', 'carpeta_csv']}, ensure_ascii=False, indent=2))
    print('Diferencias de totales:', len(reporte['diferencias_totales']))
    print('Diferencias API/historial:', len(reporte['diferencias_api']))
    return reporte


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--desde', help='Carpeta local relativa al proyecto; omite la descarga.')
    args = parser.parse_args()
    try:
        ejecutar(args.desde)
    except Exception as error:
        print(f'Ingesta detenida: {error}. Revisa reportes/ingesta_ultima.json', file=sys.stderr)
        sys.exit(1)
