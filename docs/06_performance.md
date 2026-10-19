# Paso 6: medir un índice

## a) Qué hacemos y por qué

Medimos una consulta que filtra fibra desde 2025, suma sus accesos y ordena los resultados.
Es relativamente costosa dentro de esta tabla; no simulamos millones de registros.
Un índice permite encontrar más directamente las filas de un filtro, pero tiene un costo de espacio y mantenimiento.

## b) Qué se ejecutó

Se actualizaron las estadísticas con `ANALYZE telecom.acceso`, se hizo calentamiento
y tres mediciones antes y después del índice, sin forzar al motor a usarlo.

| Medición | Antes, ms | Después, ms |
|---|---:|---:|
| 1 | 1,082 | 0,528 |
| 2 | 0,952 | 0,527 |
| 3 | 1,032 | 0,532 |
| Mediana | **1,032** | **0,528** |

Diferencia de medianas: **0,504 ms**. Es una mejora medible en este ensayo,
pero muy pequeña en tiempo absoluto. No es una promesa de rendimiento ni de experiencia de usuario.
Los tiempos excluyen la latencia de Internet y no representan concurrencia de producción.

## c) Leer el SQL y el plan

| Línea | Qué hace |
|---|---|
| `SELECT provincia_id,anio,trimestre,SUM(cantidad)` | Elige los grupos y suma los accesos. |
| `FROM telecom.acceso` | Consulta las 6.000 filas de accesos por tecnología. |
| `WHERE tecnologia_codigo='fibra_optica' AND anio>=2025` | Selecciona la tecnología y el período. |
| `GROUP BY provincia_id,anio,trimestre` | Calcula el resultado de cada provincia y trimestre. |
| `ORDER BY anio,trimestre,accesos_fibra DESC` | Ordena cronológicamente y por cantidad dentro del período. |
| `EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON)` | Ejecuta la consulta y devuelve el plan real, tiempos y acceso a bloques de memoria/disco. |
| `CREATE INDEX IF NOT EXISTS idx_acceso_tecnologia_anio` | Crea el índice didáctico si no existe. |
| `ON telecom.acceso(tecnologia_codigo,anio,trimestre)` | Organiza la búsqueda empezando por las columnas del filtro. |

Antes apareció `Seq Scan`: recorrió la tabla y descartó 5.856 filas para devolver 144.
Después aparecieron `Bitmap Index Scan` y `Bitmap Heap Scan`: usó el índice para localizar
las filas y luego recuperar sus datos. El agregado y el ordenamiento siguen siendo necesarios.

Las claves primarias ya tienen sus propios índices. El que agregamos tiene otro orden de columnas,
orientado a este filtro. No haríamos un índice por cada columna automáticamente.

Resultados completos: `reportes/planes_performance.json`. Resumen:
`reportes/performance_resumen.json`. `src/medir.py` permite repetir el ensayo.
Para repetirlo con el índice ya creado, `--reiniciar-indice` elimina y recrea únicamente
ese índice de este proyecto. No borra filas.

## d) Analogía

El índice de un libro te lleva a páginas concretas. Si querés leer gran parte del libro,
recorrerlo puede ser más conveniente. Postgres también elige según cuánto espera leer.

## e) En una entrevista

“Comparé planes y tiempos antes y después de un índice alineado con el filtro.
La mediana bajó de 1,032 a 0,528 ms, aunque el volumen pequeño limita su relevancia práctica.”
