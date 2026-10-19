# Fuentes públicas verificadas

Verificación realizada el 19 de octubre de 2026. Productor: ENACOM.
Se consultaron exclusivamente páginas públicas y datos estadísticos agregados.

## Fuentes elegidas

1. Accesos por tecnología y provincia:
   https://indicadores.enacom.gob.ar/DatosAbiertos/Internet/accesos-tecnologias-provincias
   - Respuesta HTTP 200 descargada en `evidencia/accesos.html`.
   - Tabla `datosInternetAccTecProvincias`: 1.200 filas, 24 jurisdicciones,
     50 períodos, desde 2014-T1 hasta 2026-T2.
   - Columnas: Año, Trimestre, Provincia, ADSL, Cablemodem, Fibra Optica,
     Wireless, Otros, Total.
2. Velocidad media de descarga por provincia:
   https://indicadores.enacom.gob.ar/DatosAbiertos/Internet/velocidad-media-provincias
   - Respuesta HTTP 200 descargada en `evidencia/velocidad.html`.
   - Tabla `datosInternetVMDProvincias`: 1.200 filas, 24 jurisdicciones,
     50 períodos, desde 2014-T1 hasta 2026-T2.
   - Columnas: Año, Trimestre, Provincia, Mbps (Media de bajada).
3. API pública de velocidad provincial del último período:
   https://indicadores.enacom.gob.ar/DatosAbiertos.asmx/InternetVMDProvinciasUltimoPeriodo
   - Método GET, respuesta HTTP 200, JSON: `evidencia/velocidad_api.json`.
   - 24 filas del segundo trimestre de 2026. Incluye año y trimestre explícitos.
   - Los 24 valores coinciden con el mismo período de la tabla histórica.
   - El endpoint se encontró en el JavaScript oficial:
     https://indicadores.enacom.gob.ar/Scripts/datos/internet/vmd_provincias.js
   - Operaciones publicadas en:
     https://indicadores.enacom.gob.ar/DatosAbiertos.asmx
   - No se verificó una API con el historial provincial completo.

## Disponibilidad de CSV y adaptación aprobada

El código oficial `https://indicadores.enacom.gob.ar/Scripts/dataTableBuscador.js`
configura botones de exportación CSV en el navegador. Eso no equivale a una URL
de descarga CSV directa. No se logró ejecutar la descarga desde el navegador.
No se verificó un archivo CSV oficial descargable directamente para estas tablas.

Una consulta exploratoria al catálogo Andino devolvió HTTP 500:
`https://portal-andino.datos.gob.ar/api/3/action/package_show?id=enacom-demo-internet-fija`.
Ese error no confirma ni descarta la existencia de la ficha solicitada.

Adaptación autorizada por el usuario: obtener el historial desde el archivo HTML
oficial, convertir las tablas a CSV con Python y consumir además la API real para
contrastar el último período. Esto modifica el requisito de descargar un CSV
original: el CSV sería generado por nuestro programa, sin inventar observaciones.

## Inspección inicial reproducible

Ejecutar desde esta carpeta, con Python 3.12 o superior:

```powershell
python src/verificar_fuentes.py
```

No requiere instalar bibliotecas. Lee las respuestas guardadas y genera
`reportes/verificacion_fuentes.json`. No descarga nuevamente ni modifica valores.
Verifica estructura, períodos, celdas vacías, duplicados por provincia/período
y coincidencia de velocidades entre API y tabla. No reemplaza el control de
calidad integral que construiremos más adelante.

## Interpretación y atribución

- CABA se cuenta como jurisdicción junto a las 23 provincias.
- Accesos no significa personas únicas ni hogares únicos.
- Las velocidades publicadas no se deben presentar como mediciones propias.
- Los agregados no permiten atribuir desempeño a Claro ni a otra empresa.
- Citar ENACOM e incluir el enlace, según la indicación del portal:
  https://indicadores.enacom.gob.ar/
- Los puntos de miles y las comas decimales requieren conversión antes del análisis.

## Estado del proyecto

- Elección de temas y plan: aprobados por el usuario.
- Verificación e inspección inicial: ejecutadas.
- Ingesta y limpieza: ejecutadas con descarga nueva de las tres fuentes oficiales.
- CSV generados: 6.000 filas de accesos por tecnología, 1.200 de totales,
  1.200 de velocidades históricas y 24 de velocidades de la API.
- Sin celdas vacías, duplicados, diferencias de totales ni diferencias API/historial
  en la ejecución verificada. Se conservaron los 61 valores cero de accesos por tecnología.
- Base nueva de Supabase creada con autorización explícita en la organización elegida.
- Referencia exclusiva del proyecto: `onsfufyujspxuhbqoxhd`; región São Paulo; costo cotizado USD 0/mes.
- Se crearon seis tablas, siete claves foráneas y tres vistas SQL; cantidades verificadas en la base.
- Se midió un índice: mediana de 1,032 ms antes y 0,528 ms después, en un conjunto pequeño.
- Se ejecutaron 40 controles de calidad sin incidencias y nueve pruebas de reglas.
- Se exportaron las vistas y se entregó la guía de Looker Studio; no se creó un informe en la cuenta del usuario.
- README y glosario actualizados. El modo local completo se reprodujo con éxito.
- La operación real de base se ejecutó mediante el conector; la autenticación HTTP con token personal no se probó.
- No se instalaron paquetes ni se accedió a otros proyectos o bases existentes.
- Evaluación final: pendiente; se realizará después del paso 9.
