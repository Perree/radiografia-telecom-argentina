"""Fallos deliberados en copias en memoria; nunca se cargan a la base."""

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from calidad import revisar


@unittest.skipUnless((ROOT/'data'/'base_snapshot.json').exists(),'Requiere la captura real de nuestra base')
class ControlesCalidad(unittest.TestCase):
    def setUp(self):
        self.datos = json.loads((ROOT/'data'/'base_snapshot.json').read_text(encoding='utf-8'))

    def errores(self,control,tabla):
        return next(f['errores'] for f in revisar(self.datos) if f['control']==control and f['tabla']==tabla)

    def test_detecta_nulo_sin_crashear(self):
        self.datos['tablas']['acceso'][0]['cantidad'] = None
        self.assertEqual(self.errores('nulos_obligatorios','acceso'),1)

    def test_detecta_duplicado(self):
        self.datos['tablas']['velocidad'].append(copy.deepcopy(self.datos['tablas']['velocidad'][0]))
        self.assertEqual(self.errores('claves_duplicadas','velocidad'),1)

    def test_detecta_fk_rota(self):
        self.datos['tablas']['acceso'][0]['provincia_id'] = -1
        self.assertEqual(self.errores('fk_provincia','acceso'),1)

    def test_detecta_cantidad_negativa(self):
        self.datos['tablas']['acceso'][0]['cantidad'] = -1
        self.assertEqual(self.errores('rango_numerico','acceso'),1)


if __name__ == '__main__':
    unittest.main()
