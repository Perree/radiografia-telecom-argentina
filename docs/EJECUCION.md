# Guía de ejecución

### 1. Requisitos y alcance

Necesitás Python 3.12 o superior y acceso al proyecto nuevo de Supabase. **No hace falta instalar paquetes de Python ni Docker.** El costo cotizado de creación fue USD 0/mes; las condiciones futuras dependen de Supabase.

La referencia pública del único proyecto autorizado está en `proyecto.json`: `onsfufyujspxuhbqoxhd`, región São Paulo. Los programas rechazan una referencia distinta indicada en el entorno. No listan ni consultan otras bases.

Si reproducís el proyecto en otra cuenta, primero creá un proyecto propio vacío con tu autorización de costos y cambiá conscientemente `proyecto.json` y la referencia del entorno. No apuntes a una base existente que tenga otros datos.

### 2. Elegir el intérprete

Abrí una terminal en la carpeta del proyecto. En un equipo con Python disponible:

```powershell
python --version
```

Usá el ejecutable de tu instalación de Python. Si el comando apunta a un alias sin intérprete, elegí una instalación válida antes de continuar.

### 3. Configurar la conexión sin guardar credenciales en el código

Copiá `.env.example` como `.env` y completalo localmente con tu propio token de administración de Supabase. También podés definir las dos variables mediante el entorno. `.env` queda excluido por `.gitignore`.

El token se obtiene en la [configuración de tokens de Supabase](https://supabase.com/dashboard/account/tokens), siguiendo su [documentación de Management API](https://supabase.com/docs/reference/api/introduction). No es la clave pública de la API de datos. No lo compartas en el chat, README o capturas.

Las variables son `SUPABASE_ACCESS_TOKEN` y `SUPABASE_PROJECT_REF`. Los programas solo envían solicitudes a la referencia configurada y autorizada en `proyecto.json`.

**Qué se verificó en esta sesión:** la descarga y transformación se ejecutaron con Python; la creación, carga y consultas reales de Postgres se ejecutaron mediante el conector de Supabase. Los scripts HTTP para repetirlas con un token personal están preparados, pero **no se probó esa autenticación por token personal**, porque no se pidió ni guardó uno.

### 4. Ejecutar el flujo completo con Internet

```powershell
python src/pipeline.py
```

El flujo corre estos comandos en orden y se detiene ante un error:

```powershell
python src/ingesta.py
python src/carga.py --ejecutar
python src/ejecutar_sql.py 02_vistas.sql
python src/medir.py --reiniciar-indice
python src/calidad.py
python src/exportar.py
```

La carga crea las seis tablas si no existen, valida sus cantidades y actualiza las claves ya presentes sin duplicarlas. Usa una transacción para las inserciones. No modifica automáticamente una estructura antigua distinta ni borra observaciones retiradas por la fuente: esas situaciones requieren revisión.

La medición recrea únicamente el índice didáctico `telecom.idx_acceso_tecnologia_anio` para comparar antes/después. No elimina filas. El resto del esquema permanece.

Cada descarga queda en `data/raw/<ejecucion>/` y cada conjunto limpio en `data/clean/<ejecucion>/`. `reportes/ingesta_ultima.json` indica qué carpeta corresponde a la ejecución y si terminó. Los originales conservan su huella SHA-256. La hora del reporte está en UTC.

Los CSV limpios y capturas de la base quedan en `data/`, excluida del repositorio. Pueden regenerarse con el flujo. `evidencia/` conserva una copia inicial pública para practicar sin volver a descargar.

### 5. Revisar resultados y pruebas

```powershell
python -m unittest discover -s tests -v
```

Se ejecutaron nueve pruebas: cinco reglas de ingesta y cuatro fallos deliberados en copias en memoria para comprobar los controles de calidad. No se cargaron datos de prueba a Supabase. Las pruebas que requieren captura se omiten explícitamente si todavía no existe.

| Archivo | Qué revisar |
|---|---|
| `reportes/reporte_calidad.csv` | 40 controles; 0 incidencias en la ejecución verificada |
| `reportes/planes_performance.json` | Planes y tiempos reales antes/después del índice |
| `reportes/performance_resumen.json` | Medianas y estrategias de búsqueda |
| `reportes/hallazgos.json` | Cifras verificadas durante la construcción, no se actualiza automáticamente |
| `reportes/exportacion.json` | Fecha, período y cantidades de las vistas exportadas |
| `exports/tablero.csv` | Fuente combinada para el tablero, sin repetir claves |
| `exports/v_radiografia.csv`, `exports/v_crecimiento.csv`, `exports/v_ranking.csv` | Cada vista exportada por separado |

La mediana de ejecución de la consulta medida bajó de **1,032 ms a 0,528 ms** tras el índice: **0,504 ms** de diferencia. Se midió tres veces en cada etapa. El motor pasó de recorrido completo a búsqueda mediante índice. El volumen de 6.000 filas es pequeño y esos tiempos no incluyen Internet ni prueban una mejora en producción. [Explicación](../docs/06_performance.md).

Si falla la descarga, se conserva el error y no se publican CSV limpios de esa ejecución. Si falla un control, el programa devuelve código 1. No reemplaces silenciosamente el archivo por una copia vieja y la presentes como actual.

### 6. Repetir sin red y armar el tablero

Con los archivos de esta sesión presentes:

```powershell
python src/pipeline.py --sin-red
```

Este modo procesa nuevamente `evidencia/`, genera SQL y usa las capturas y planes reales ya guardados. **No crea, consulta ni actualiza una base.** Si faltan capturas, primero necesitás ejecutar la parte conectada; no genera resultados ficticios.

Para el tablero, seguí la [guía de seis pasos](../GUIA_TABLERO.md). Subí solo `exports/tablero.csv` a un conjunto nuevo de Looker Studio. Las otras vistas son exportaciones alternativas, no archivos para anexar al mismo conjunto.

Los CSV son una foto. Para actualizarlos corré el flujo y reemplazá el conjunto o archivos anteriores: anexar otra vez el historial completo duplicaría filas. No se creó ni publicó un tablero en tu cuenta.

