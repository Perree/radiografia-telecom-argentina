# Paso 8: tablero de una página en Looker Studio

## a) Qué vamos a hacer y por qué

Una página debe permitir responder qué cambió, dónde y en qué período.
Vamos a mostrar cuatro indicadores, un ranking y una evolución, con títulos y unidades claros.
Los CSV ya están preparados. El informe de Looker Studio todavía no fue creado en tu cuenta.

## b) Armado en seis pasos

1. **Conectar los datos.** Entrá a [Looker Studio](https://lookerstudio.google.com/),
   creá una fuente con el conector de carga CSV y subí únicamente `exports/tablero.csv`
   a un conjunto nuevo. Conectalo a un informe vacío. Tiene 1.200 filas, una por
   jurisdicción y trimestre. No subas también las otras vistas al mismo conjunto:
   repetirías información. La carga CSV puede aparecer bajo el nombre Data Studio.
   [Instrucciones oficiales](https://docs.cloud.google.com/data-studio/upload-csv-files).

2. **Revisar los campos.** Usá `provincia` como texto y `fecha` como fecha, con formato
   año-mes-día. `anio` y `trimestre` identifican categorías: no son indicadores para sumar.
   Los accesos son números enteros; `mbps` es decimal. Una celda vacía de crecimiento
   debe quedar como dato faltante. Usá dos filtros separados de año y trimestre.
   [Campos calculados](https://cloud.google.com/looker/docs/studio/add-edit-and-troubleshoot-calculated-fields).

3. **Agregar filtros.** Poné una lista de provincias con selección múltiple y controles
   de año y trimestre con selección única. Para comenzar, elegí **2026 y trimestre 2**.
   Los indicadores de volumen son una foto: sumar varios trimestres sumaría conexiones
   observadas repetidas veces. Mostrá el período elegido en el título o junto a los controles.

4. **Crear cuatro tarjetas.** Configuralas con las fórmulas de abajo. Para porcentajes,
   elegí formato porcentaje y dos decimales; las fórmulas devuelven fracciones, no las
   multipliques otra vez por 100. Una tarjeta sin base interanual debe mostrar “sin dato”.
   No uses la suma ni el promedio de los porcentajes provinciales para el total.

   | Indicador | Fórmula | Resultado de control, todas las provincias en 2026-T2 |
   |---|---|---:|
   | Accesos de Internet fijo | `SUM(accesos_totales)` | 13.768.437 |
   | Participación de fibra | `SUM(accesos_fibra) / SUM(accesos_totales)` | 50,12% |
   | Crecimiento interanual | `(SUM(accesos_comparables) - SUM(accesos_hace_un_anio)) / SUM(accesos_hace_un_anio)` | 12,36% |
   | Jurisdicciones incluidas | `COUNT_DISTINCT(provincia)` | 24 |

   Para períodos sin base o denominadores cero, agregá una condición que entregue NULL
   en lugar de dividir. No reemplaces ese resultado por crecimiento cero.

5. **Agregar dos gráficos.** Una tabla muestra provincia, Mbps, puesto de velocidad,
   accesos y porcentaje de fibra, ordenada por puesto. El puesto viene calculado entre
   las 24 jurisdicciones: filtrar provincias no lo recalcula como un ranking del subconjunto.
   Debajo, una serie temporal muestra `SUM(accesos_totales)` por `fecha` para ver la evolución.
   Agrupá los filtros de año/trimestre con las tarjetas y la tabla; dejá la serie fuera
   de ese grupo para que conserve el historial. Verificá el alcance del filtro de provincias.
   Si agregás una tarjeta de velocidad, titulala “Promedio simple entre provincias”:
   `AVG(mbps)` no es la velocidad media nacional informada por ENACOM.

6. **Validar y presentar.** Probá todas las provincias y después Buenos Aires en 2026-T2:
   debe mostrar **5.699.031 accesos**, **48,25% de fibra**, **6,32% interanual** y **326,87 Mbps**
   en la tabla. Revisá que los filtros no dupliquen filas. Agregá fuente ENACOM, período
   de los datos y fecha de exportación (`reportes/exportacion.json`). Los CSV son una foto:
   al actualizar, reemplazá el conjunto o sus archivos anteriores; añadir el historial
   completo de nuevo duplicaría registros.

## c) Qué hace cada parte

`src/exportar.py` extrae las tres vistas reales y guarda sus CSV por separado.
Después comprueba que las claves sean únicas y coincidan, y arma `tablero.csv`
con una fila por provincia y período. `accesos_comparables` solo incluye accesos
con base del año anterior; evita usar un numerador que incluya provincias sin comparación.

Una dimensión describe, como provincia o fecha. Una métrica mide, como accesos.
Un buen tablero explica qué significa cada cifra, permite filtrar y muestra límites;
no obliga a interpretar nombres de columnas ni confunde tamaño con calidad de servicio.

No calculamos clientes únicos, cobertura de hogares, participación de Claro ni causalidad:
las fuentes elegidas no permiten responder esas preguntas.

## d) Analogía

El tablero se parece al de un auto: pocas señales legibles para decidir dónde mirar.
No muestra cada pieza del motor, pero tampoco oculta una luz de advertencia.

## e) En una entrevista

“Preparé una fuente agregada para un tablero, con filtros y porcentajes calculados
desde sus cantidades base. La guía distingue el tamaño del mercado, la mezcla tecnológica
y las velocidades publicadas.”
