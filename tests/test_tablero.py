"""Contrato de los CSV publicos para BI; no usa token, red ni capturas privadas."""

import csv
import sys
import unittest
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECIMALES = Decimal('0.01')


def leer(nombre):
    with (ROOT / 'exports' / nombre).open(encoding='utf-8-sig', newline='') as archivo:
        lector = csv.DictReader(archivo)
        return lector.fieldnames, list(lector)


def clave(fila):
    return fila['provincia'], int(fila['anio']), int(fila['trimestre'])


class ContratoTablero(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.columnas, cls.filas = leer('tablero.csv')
        cls.por_clave = {clave(f): f for f in cls.filas}

    def test_columnas_para_indicadores_y_filtros(self):
        necesarias = {
            'provincia', 'anio', 'trimestre', 'fecha', 'accesos_totales',
            'accesos_fibra', 'porcentaje_fibra', 'mbps', 'accesos_hace_un_anio',
            'accesos_comparables', 'crecimiento_interanual_pct',
        }
        self.assertTrue(necesarias.issubset(self.columnas))
        self.assertEqual(len(self.columnas), len(set(self.columnas)))
        for columna in self.columnas:
            self.assertRegex(columna, r'^[a-z][a-z0-9_]*$')

    def test_clave_provincia_periodo_unica(self):
        self.assertTrue(self.filas)
        self.assertEqual(len(self.filas), len(self.por_clave))

    def test_fecha_iso_corresponde_al_trimestre(self):
        for fila in self.filas:
            with self.subTest(clave=clave(fila)):
                anio, trimestre = int(fila['anio']), int(fila['trimestre'])
                self.assertIn(trimestre, (1, 2, 3, 4))
                fecha = date.fromisoformat(fila['fecha'])
                self.assertEqual(fecha.isoformat(), fila['fecha'])
                self.assertEqual(fecha, date(anio, trimestre * 3 - 2, 1))

    def test_tipos_y_porcentaje_fibra(self):
        for fila in self.filas:
            with self.subTest(clave=clave(fila)):
                total, fibra = int(fila['accesos_totales']), int(fila['accesos_fibra'])
                self.assertGreaterEqual(total, 0)
                self.assertGreaterEqual(fibra, 0)
                self.assertLessEqual(fibra, total)
                mbps = Decimal(fila['mbps'])
                self.assertTrue(mbps.is_finite())
                self.assertGreaterEqual(mbps, 0)
                if total:
                    esperado = (Decimal(100) * fibra / total).quantize(DECIMALES, rounding=ROUND_HALF_UP)
                    self.assertEqual(Decimal(fila['porcentaje_fibra']), esperado)
                else:
                    self.assertEqual(fila['porcentaje_fibra'], '')

    def test_nulos_y_crecimiento_segun_base_real(self):
        permitidos = {'accesos_hace_un_anio', 'accesos_comparables', 'crecimiento_interanual_pct'}
        for fila in self.filas:
            provincia, anio, trimestre = clave(fila)
            with self.subTest(clave=clave(fila)):
                for columna in set(self.columnas) - permitidos:
                    self.assertNotEqual(fila[columna], '')
                anterior = self.por_clave.get((provincia, anio - 1, trimestre))
                if anterior is None:
                    for columna in permitidos:
                        self.assertEqual(fila[columna], '')
                else:
                    base = int(anterior['accesos_totales'])
                    actual = int(fila['accesos_totales'])
                    self.assertEqual(int(fila['accesos_hace_un_anio']), base)
                    self.assertEqual(int(fila['accesos_comparables']), actual)
                    if base:
                        esperado = (Decimal(100) * (actual - base) / base).quantize(DECIMALES, rounding=ROUND_HALF_UP)
                        self.assertEqual(Decimal(fila['crecimiento_interanual_pct']), esperado)
                    else:
                        self.assertEqual(fila['crecimiento_interanual_pct'], '')

    def test_coincidencia_con_las_tres_vistas_exportadas(self):
        for nombre in ('v_radiografia.csv', 'v_crecimiento.csv', 'v_ranking.csv'):
            columnas, filas = leer(nombre)
            self.assertEqual(len(filas), len(self.filas))
            self.assertEqual({clave(f) for f in filas}, set(self.por_clave))
            for fila in filas:
                for columna in columnas:
                    self.assertEqual(fila[columna], self.por_clave[clave(fila)][columna])


if __name__ == '__main__':
    unittest.main()
