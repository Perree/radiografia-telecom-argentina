"""Cliente SQL de Management API: solo el proyecto autorizado, sin paquetes externos."""

import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def configurar():
    # Se aceptan lineas KEY=VALUE simples. No se ejecuta el contenido del archivo.
    archivo = ROOT / '.env'
    if archivo.exists():
        for linea in archivo.read_text(encoding='utf-8-sig').splitlines():
            if not linea.strip() or linea.lstrip().startswith('#'):
                continue
            nombre, separador, valor = linea.partition('=')
            if not separador or nombre.strip() not in {'SUPABASE_ACCESS_TOKEN', 'SUPABASE_PROJECT_REF'}:
                raise ValueError('Entrada de .env no admitida; usar .env.example como referencia')
            os.environ.setdefault(nombre.strip(), valor.strip().strip('\"\''))
    autorizado = json.loads((ROOT / 'proyecto.json').read_text(encoding='utf-8'))['supabase_project_ref']
    referencia = os.environ.get('SUPABASE_PROJECT_REF', autorizado)
    if referencia != autorizado:
        raise ValueError('El proyecto indicado no coincide con el autorizado en proyecto.json')
    token = os.environ.get('SUPABASE_ACCESS_TOKEN')
    if not token:
        raise ValueError('Falta SUPABASE_ACCESS_TOKEN en variables de entorno o .env; nunca lo pegues en el codigo')
    return referencia, token


def consultar(sql):
    referencia, token = configurar()
    cuerpo = json.dumps({'query': sql}).encode('utf-8')
    solicitud = Request(f'https://api.supabase.com/v1/projects/{referencia}/database/query',
                        data=cuerpo, method='POST', headers={
                            'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
    try:
        with urlopen(solicitud, timeout=90) as respuesta:
            resultado = json.load(respuesta)
    except HTTPError as error:
        # No mostramos encabezados, tokens ni cadenas de conexion.
        detalle = error.read().decode('utf-8', errors='replace').replace(token, '[OCULTO]')
        raise RuntimeError(f'Supabase HTTP {error.code}: {detalle[:1000]}') from None
    if not isinstance(resultado, list):
        raise ValueError('Formato de respuesta SQL no esperado')
    return resultado


def archivo_sql(nombre):
    return (ROOT / 'sql' / nombre).read_text(encoding='utf-8-sig')
