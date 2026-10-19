"""Ejemplos artificiales para probar reglas; NO son datos del proyecto."""

import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ingesta import filas_unicas, numero_local
from verificar_fuentes import TablaHTML


class ReglasIngesta(unittest.TestCase):
    def test_separadores_regionales(self):
        self.assertEqual(numero_local('1.234.567', entero=True), 1234567)
        self.assertEqual(numero_local('1.234,50'), Decimal('1234.50'))
        self.assertEqual(numero_local('0', entero=True), 0)

    def test_no_adivina_formatos(self):
        for valor in ['', '1.23', '12,5', '-1', 'NaN', 'sin datos']:
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                numero_local(valor, entero=True)

    def test_descarta_solo_duplicados_identicos(self):
        fila = {'Año': '2020', 'Trimestre': '1', 'Provincia': 'CABA', 'valor': '1'}
        reporte = {'duplicados_identicos_descartados': {'prueba': 0}}
        self.assertEqual(len(filas_unicas([fila, fila.copy()], 'prueba', reporte)), 1)
        self.assertEqual(reporte['duplicados_identicos_descartados']['prueba'], 1)

    def test_detiene_duplicado_contradictorio(self):
        fila = {'Año': '2020', 'Trimestre': '1', 'Provincia': 'CABA', 'valor': '1'}
        reporte = {'duplicados_identicos_descartados': {'prueba': 0}}
        with self.assertRaises(ValueError):
            filas_unicas([fila, dict(fila, valor='2')], 'prueba', reporte)

    def test_parser_ignora_otras_tablas_y_conserva_ceros(self):
        parser = TablaHTML('objetivo')
        parser.feed('<table id="otra"><tr><td>ignorar</td></tr></table>'
                    '<table id="objetivo"><tr><th>Valor</th></tr>'
                    '<tr><td><b>0</b></td></tr></table>')
        self.assertEqual(parser.encabezados, ['Valor'])
        self.assertEqual(parser.filas, [['0']])


if __name__ == '__main__':
    unittest.main()
