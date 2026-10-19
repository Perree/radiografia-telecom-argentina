# Paso 5: SQL de análisis

## a) Qué hacemos y por qué

Una vista es una consulta guardada. Creamos tres para responder preguntas concretas
sin repetir toda la lógica cada vez. Cada resultado tiene una fila por provincia y trimestre.

## b) Qué hicimos

Ejecutamos `sql/02_vistas.sql` en nuestra base. Cada vista devolvió 1.200 filas.
Los ejemplos de abajo se extrajeron de esas vistas, no se inventaron.

## c) Lectura línea por línea de la lógica

En el archivo SQL, los paréntesis cierran bloques y las comas separan columnas.
`AS` asigna un nombre; los prefijos `r.`, `p.`, `v.` y `t.` indican de qué tabla sale el campo.

### Vista 1: `v_radiografia`

Pregunta: ¿cuántos accesos hay, qué parte corresponde a fibra y qué velocidad se informa?

| Línea SQL | Explicación |
|---|---|
| `CREATE OR REPLACE VIEW ... AS` | Guarda o reemplaza la definición de la vista. |
| `WITH resumen AS (` | Abre una CTE, un resultado intermedio con nombre que dura esta consulta. |
| `SELECT provincia_id,anio,trimestre` | Identifica los grupos a calcular. |
| `SUM(cantidad) AS accesos_totales` | Suma todas las tecnologías de cada grupo. |
| `COALESCE(SUM(cantidad) FILTER (...),0)` | Suma solo fibra. Si esa suma no tiene valor, entrega cero; no cambia la fuente. |
| `FROM telecom.acceso` | Lee las mediciones de accesos. |
| `GROUP BY provincia_id,anio,trimestre` | Produce una fila por provincia y período antes del cruce. |
| `SELECT r.provincia_id,p.nombre AS provincia,r.anio,r.trimestre` | Selecciona la identificación y recupera el nombre legible. |
| `make_date(r.anio,r.trimestre*3-2,1)` | Convierte el trimestre en su fecha inicial: T2 empieza el 1 de abril. |
| `r.accesos_totales,r.accesos_fibra` | Conserva las dos cantidades para calcular indicadores correctamente en el tablero. |
| `ROUND(100.0 * ... / NULLIF(...,0),2)` | Calcula el porcentaje de fibra, evita dividir por cero y redondea a dos decimales. |
| `v.mbps` | Agrega la velocidad de esa provincia y período. |
| `t.cantidad AS total_publicado` | Agrega el total original de ENACOM. |
| `r.accesos_totales-t.cantidad` | Calcula la diferencia para poder revisarla. |
| `FROM resumen r` | Usa el resultado de la CTE como base. |
| `JOIN telecom.provincia p ON ...` | Vincula cada identificador con su nombre. |
| `LEFT JOIN telecom.velocidad v` | Conserva los accesos incluso si no hubiera velocidad. |
| `ON ... provincia_id ... anio ... trimestre` | Exige que coincidan las tres partes; unir solo por provincia multiplicaría períodos. |
| `LEFT JOIN telecom.total_publicado t ON ...` | Agrega el total publicado usando la misma clave. |

Ejemplo real, Buenos Aires, 2026-T2: **5.699.031 accesos**, **2.749.932 de fibra**,
**48,25% de fibra** y **326,87 Mbps**. Diferencia con el total publicado: **0**.

### Vista 2: `v_crecimiento`

Pregunta: ¿cuánto cambiaron los accesos respecto del mismo trimestre del año anterior?

| Línea SQL | Explicación |
|---|---|
| `WITH anterior AS (` | Prepara las mediciones y sus valores anteriores. |
| `SELECT provincia_id,provincia,anio,trimestre,fecha,accesos_totales` | Conserva la observación actual. |
| `LAG(accesos_totales,4) OVER (` | Mira cuatro filas atrás, manteniendo la fila actual. Es una función de ventana. |
| `PARTITION BY provincia_id` | Hace el recorrido dentro de cada provincia. |
| `ORDER BY anio,trimestre` | Ordena el recorrido cronológicamente. |
| `) AS accesos_base` | Nombra la cantidad anterior encontrada. |
| `LAG(anio*4+trimestre,4) OVER (...)` | También recupera el período anterior para verificar la distancia temporal. |
| `FROM telecom.v_radiografia` | Parte de los accesos ya agregados. |
| `SELECT ... accesos_totales` | Devuelve la fila actual junto con los nuevos cálculos. |
| `CASE WHEN periodo_base=anio*4+trimestre-4` | Comprueba que la fila encontrada sea realmente del año previo. |
| `THEN accesos_base END` | Devuelve la base si corresponde; en caso contrario queda NULL. |
| `THEN ROUND(100.0*(actual-base)/NULLIF(base,0),2)` | Calcula la variación porcentual y evita dividir por cero. |
| `END AS crecimiento_interanual_pct` | Nombra el indicador. |
| `FROM anterior` | Lee los valores preparados por la CTE. |

Buenos Aires pasó de **5.360.230** accesos en 2025-T2 a **5.699.031** en 2026-T2:
**6,32%** de crecimiento. Hay **96 resultados NULL** en el primer año del historial,
porque no tenemos el año anterior para comparar. No son errores ni crecimiento cero.

### Vista 3: `v_ranking`

Pregunta: ¿qué lugar ocupa cada provincia por velocidad y por cantidad de accesos?

| Línea SQL | Explicación |
|---|---|
| `SELECT ... accesos_totales,porcentaje_fibra,mbps` | Mantiene los indicadores que ayudan a interpretar el puesto. |
| `RANK() OVER (` | Calcula un puesto sin juntar ni eliminar filas. |
| `PARTITION BY anio,trimestre` | Reinicia el ranking en cada período. |
| `ORDER BY mbps DESC NULLS LAST` | Ordena de mayor a menor velocidad y ubica faltantes al final. |
| `) AS ranking_velocidad` | Guarda el puesto de velocidad. En empate, comparte puesto y deja un salto. |
| `RANK() OVER (... ORDER BY accesos_totales DESC)` | Hace lo mismo por tamaño del mercado. |
| `FROM telecom.v_radiografia` | Usa los indicadores por provincia y período. |

En 2026-T2, CABA tiene **372,42 Mbps**, puesto **1** en velocidad y **2** en accesos.
Buenos Aires tiene puesto **2** en velocidad y **1** en accesos. Tamaño y velocidad
son preguntas distintas; esto no atribuye resultados a un operador.

`security_invoker=true` hace que las vistas respeten los permisos de quien consulta.
`REVOKE` mantiene los datos fuera del acceso de los roles web no autorizados.

## d) Analogías

Un JOIN es juntar una lista de pedidos con la agenda de clientes usando su número.
Una CTE es anotar un subtotal antes de hacer la cuenta final. Una ventana permite
mirar las filas vecinas sin perder el detalle. Un ranking es la tabla de posiciones
de un torneo, reiniciada para cada temporada.

## e) En una entrevista

“Agregué antes de unir para evitar duplicar cifras, calculé crecimiento interanual
con LAG y construí rankings independientes por trimestre.”
