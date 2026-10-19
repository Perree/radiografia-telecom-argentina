# Paso 7: calidad de datos

## a) Qué hacemos y por qué

Revisamos que los datos cargados mantengan valores y relaciones coherentes.
Una consulta puede funcionar y aun así mostrar cifras equivocadas si su carga perdió o duplicó datos.

## b) Qué hicimos

`src/calidad.py` ejecutó **40 controles, sin incidencias detectadas**, sobre una captura
extraída de nuestra base. El reporte es `reportes/reporte_calidad.csv`.
Los 61 ceros publicados se registran como información, no como errores.

## c) Qué controla el código

| Control | Qué busca | Para qué importa en una empresa |
|---|---|---|
| Tabla no vacía | Una carga que no trajo observaciones | Evitar presentar un tablero vacío como caída real del negocio |
| Nulos obligatorios | Identificadores o mediciones faltantes | Poder asignar cada cifra al lugar y período correctos |
| Duplicados de clave | Una misma observación cargada más de una vez | Evitar inflar volúmenes y crecimiento |
| Rangos | Trimestres inválidos, cantidades negativas/no enteras y velocidades negativas/no finitas | Detectar formatos mal interpretados o registros imposibles |
| Claves foráneas | Provincia, período o tecnología que no existe | Evitar mediciones huérfanas y pérdidas en cruces |
| Cobertura y continuidad | Combinaciones o trimestres faltantes | Distinguir un dato ausente de un valor cero |
| Suma contra total publicado | Diferencias entre tecnologías y total de ENACOM | Identificar inconsistencias sin decidir por cuenta propia cuál cifra es correcta |
| CSV contra base | Claves y valores diferentes después de cargar | Demostrar que la carga conservó la información |
| API contra base | Diferencias en las 24 velocidades del último trimestre | Contrastar dos formas oficiales de acceder a la publicación |

`revisar()` produce una fila por control. La columna `errores` cuenta incidencias,
`estado` distingue OK/ERROR/INFO y `detalle` describe la regla.
Si hay errores, el programa termina con código 1 para detener un pipeline automático.

Las restricciones de la base ya impiden algunos errores. El script los comprueba igualmente
y agrega controles entre fuentes que una clave foránea no resuelve.

Cuatro pruebas adicionales modifican copias **en memoria** para comprobar que el script
detecta un nulo, un duplicado, una cantidad negativa y una referencia inexistente.
Esos fallos de prueba nunca se enviaron a Supabase ni se usaron en los hallazgos.

Un reporte limpio no demuestra que los proveedores hayan declarado todos los accesos reales:
demuestra que los datos disponibles cumplen las reglas revisadas.
Los NULL de crecimiento del primer año son esperables y no se confunden con nulos inválidos en las tablas de mediciones.

## d) Analogía

Una factura puede tener todos sus casilleros completos y una suma incorrecta.
Por eso revisamos estructura, relaciones y cifras: son controles distintos.

## e) En una entrevista

“Implementé controles de calidad y concilié los CSV con la base por clave y valor.
No detecté incidencias en esta descarga y validé los controles con fallos deliberados en copias locales.”
