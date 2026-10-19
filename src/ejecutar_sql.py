"""Ejecuta solamente los archivos de esquema o vistas de este proyecto."""

import argparse
from db import archivo_sql, consultar

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archivo',choices=['01_esquema.sql','02_vistas.sql'])
    args = parser.parse_args()
    consultar(archivo_sql(args.archivo))
    print('Ejecutado:',args.archivo)
