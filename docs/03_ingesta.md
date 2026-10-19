# Paso 3: ingesta y limpieza

## a) Qué hacemos y por qué

Descargamos las tablas históricas oficiales y consultamos la API del último trimestre.
Conservamos los archivos originales y producimos CSV que puedan cargarse en una base.
La adaptación de HTML a CSV fue aprobada por el usuario.

## b) Qué se ejecutó

`src/ingesta.py` corrió con descargas nuevas el 19/10/2026, sin instalar paquetes.
También se probó la lectura sin red usando los archivos de `evidencia/`.

| Salida | Filas | Una fila representa |
|---|---:|---|
| accesos_tecnologia.csv | 6.000 | Provincia, trimestre y tecnología |
| totales_publicados.csv | 1.200 | Total por provincia y trimestre |
| velocidad_historica.csv | 1.200 | Velocidad por provincia y trimestre |
| velocidad_api.csv | 24 | Velocidad por provincia del último trimestre |

Los históricos van de 2014-T1 a 2026-T2: 50 períodos, con 24 jurisdicciones cada uno.
El reporte de cada ejecución indica su carpeta de salida y la huella SHA-256 de cada original.
La huella sirve para identificar un archivo, no para demostrar la exactitud de sus cifras.

## c) Cómo funciona el código

| Parte | Qué hace |
|---|---|
| `descargar()` | Pide las tres URL públicas y guarda sus bytes sin cambiar los valores. |
| `leer_tabla()` | Ubica una tabla por su identificador HTML y lee encabezados y filas. Si cambia la estructura, avisa. |
| `numero_local()` | Interpreta puntos de miles y comas decimales. Por ejemplo, el valor publicado `3,73` pasa a `3.73`. Rechaza formatos ambiguos. |
| `clave()` | Identifica una observación con año, trimestre y provincia. Verifica período y jurisdicción. |
| `filas_unicas()` | Descarta únicamente copias idénticas. Si la misma clave tiene cifras distintas, detiene la ingesta. |
| `procesar()` | Verifica columnas, convierte cantidades, separa tecnologías en filas y compara totales y velocidades. |
| `escribir_csv()` | Escribe columnas estables con nombres simples y caracteres UTF-8. |
| `ejecutar()` | Coordina todo y registra éxito o error. Cada ejecución tiene una carpeta distinta; si falla, no publica nuevos CSV limpios. |

### Problemas observados y decisiones

- **Encabezados:** `Año` pasa a `anio`; `Fibra Optica` se identifica como `fibra_optica`.
  Se conservan los nombres originales en los archivos crudos.
- **Formatos numéricos:** el HTML utiliza puntos de miles y comas decimales.
  La API ya devuelve números; no se le aplica la conversión regional del HTML.
- **Columnas por tecnología:** pasan a filas. Por eso las 1.200 observaciones originales
  se convierten en 6.000 filas: cinco tecnologías por observación. No son nuevas conexiones.
- **Vacíos y duplicados:** no se detectaron en esta descarga. No se rellenó ni eliminó ninguna observación.
- **Ceros:** se conservaron 61 cantidades cero por tecnología. Un cero no demuestra falta de información.
- **Totales:** las 1.200 sumas de tecnologías coinciden con los totales publicados.
  Guardamos ambas cifras igualmente para poder detectar diferencias en futuras descargas.
- **API limitada:** devuelve 24 filas de 2026-T2. Se usa para contraste, no se agrega al historial
  como si fueran observaciones nuevas. Coincidió en las 24 velocidades.
- **Velocidad histórica:** el mínimo observado fue 2,57 Mbps y el máximo 372,42 Mbps.
  Eso describe el archivo; no significa que toda conexión individual tenga esas velocidades.

No se imputan valores, se interpolan períodos ni se reemplazan observaciones por estimaciones.
La evaluación completa de calidad y de claves foráneas corresponde al paso 7, después de cargar la base.

### Verificación realizada

Cinco pruebas de reglas: separadores numéricos, rechazo de formatos inesperados,
duplicados idénticos, duplicados contradictorios y selección de la tabla HTML correcta.
Los ejemplos artificiales de las pruebas están identificados como tales y no se usan en el análisis.

## d) Analogía

Es como pasar recibos a una planilla: guardás el recibo original y transcribís los importes
con un formato común. Si dos recibos con el mismo número dicen montos diferentes,
revisás el problema antes de elegir uno arbitrariamente.

## e) Cómo lo diría en una entrevista

“Integré datos públicos desde tablas web y una API, normalicé sus formatos y conservé
los originales para poder rastrear cada transformación. Validé duplicados y contrasté
totales, sin imputar ni modificar cifras de la fuente.”
