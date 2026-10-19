"""Inspecciona las respuestas oficiales guardadas, sin modificar sus valores."""

import json
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TablaHTML(HTMLParser):
    """Lee solamente la tabla identificada; ignora navegación y otras tablas."""

    def __init__(self, identificador):
        super().__init__()
        self.identificador = identificador
        self.activa = False
        self.celda = None
        self.filas = []
        self.encabezados = []

    def handle_starttag(self, tag, attrs):
        if tag == 'table' and dict(attrs).get('id') == self.identificador:
            self.activa = True
        if not self.activa:
            return
        if tag == 'tr':
            self.fila = []
            self.es_encabezado = False
        if tag in ('th', 'td'):
            self.celda = []
            self.es_encabezado |= tag == 'th'

    def handle_data(self, data):
        if self.activa and self.celda is not None:
            self.celda.append(data)

    def handle_endtag(self, tag):
        if not self.activa:
            return
        if tag in ('th', 'td') and self.celda is not None:
            self.fila.append(''.join(self.celda).strip())
            self.celda = None
        if tag == 'tr' and self.fila:
            if self.es_encabezado:
                self.encabezados = self.fila
            else:
                self.filas.append(self.fila)
        if tag == 'table':
            self.activa = False


def leer_tabla(archivo, identificador, carpeta=None):
    parser = TablaHTML(identificador)
    parser.feed(((carpeta or ROOT / 'evidencia') / archivo).read_text(encoding='utf-8-sig'))
    if not parser.encabezados or not parser.filas:
        raise ValueError(f'No se encontro la tabla esperada en {archivo}')
    if any(len(fila) != len(parser.encabezados) for fila in parser.filas):
        raise ValueError(f'Hay filas con distinto numero de columnas en {archivo}')
    return [dict(zip(parser.encabezados, fila)) for fila in parser.filas]


def resumen(filas):
    claves = [(int(f['Año']), int(f['Trimestre']), f['Provincia']) for f in filas]
    conteo = Counter(claves)
    periodos = sorted({c[:2] for c in claves})
    return {
        'filas': len(filas),
        'provincias': sorted({c[2] for c in claves}),
        'primer_periodo': periodos[0],
        'ultimo_periodo': periodos[-1],
        'cantidad_periodos': len(periodos),
        'duplicados_por_provincia_periodo': sum(n - 1 for n in conteo.values()),
        'celdas_vacias': sum(v is None or v == '' for f in filas for v in f.values()),
        'encabezados': list(filas[0]),
    }


def main():
    accesos = leer_tabla('accesos.html', 'datosInternetAccTecProvincias')
    historico = leer_tabla('velocidad.html', 'datosInternetVMDProvincias')
    api = json.loads((ROOT / 'evidencia' / 'velocidad_api.json').read_text(encoding='utf-8-sig'))
    if not isinstance(api, list) or not api:
        raise ValueError('La API no devolvio una lista con datos')
    # Comparamos el mismo periodo y provincia, independientemente del orden.
    velocidades = {(int(f['Año']), int(f['Trimestre']), f['Provincia']):
                   f['Mbps (Media de bajada)'].replace('.', '').replace(',', '.')
                   for f in historico}
    from decimal import Decimal
    diferencias = []
    for fila in api:
        clave = (int(fila['Año']), int(fila['Trimestre']), fila['Provincia'])
        valor = velocidades.get(clave)
        if valor is None or Decimal(valor) != Decimal(str(fila['Mbps'])):
            diferencias.append({'clave': clave, 'api': fila['Mbps'], 'tabla': valor})
    reporte = {
        'accesos_tabla': resumen(accesos),
        'velocidad_historica_tabla': resumen(historico),
        'velocidad_api': resumen(api),
        'diferencias_api_vs_tabla': diferencias,
        'limite': 'API provincial: ultimo periodo. Historial: HTML. CSV directo no verificado.',
    }
    salida = ROOT / 'reportes' / 'verificacion_fuentes.json'
    salida.write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(reporte, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
