-- VISTA 1: una fila por provincia y trimestre.
-- security_invoker respeta los permisos de quien consulta la vista.
CREATE OR REPLACE VIEW telecom.v_radiografia WITH (security_invoker = true) AS
-- WITH define una CTE: un resultado intermedio con nombre, dentro de esta consulta.
WITH resumen AS (
    SELECT provincia_id, anio, trimestre,
           SUM(cantidad) AS accesos_totales,
           -- FILTER suma solo las filas de fibra; las otras tecnologias aportan cero.
           COALESCE(SUM(cantidad) FILTER (WHERE tecnologia_codigo = 'fibra_optica'), 0) AS accesos_fibra
    FROM telecom.acceso
    -- Agrupamos antes de unir: evitamos repetir la velocidad una vez por tecnologia.
    GROUP BY provincia_id, anio, trimestre
)
SELECT r.provincia_id, p.nombre AS provincia, r.anio, r.trimestre,
       -- La fecha permite que el tablero reconozca cada trimestre.
       make_date(r.anio, r.trimestre * 3 - 2, 1) AS fecha,
       r.accesos_totales, r.accesos_fibra,
       -- 100.0 evita division entera; NULLIF evita dividir por cero.
       ROUND(100.0 * r.accesos_fibra / NULLIF(r.accesos_totales, 0), 2) AS porcentaje_fibra,
       v.mbps,
       t.cantidad AS total_publicado,
       r.accesos_totales - t.cantidad AS diferencia_total
FROM resumen r
-- JOIN vincula la medicion con el nombre guardado una sola vez.
JOIN telecom.provincia p ON p.provincia_id = r.provincia_id
-- LEFT JOIN conserva los accesos aunque falte una velocidad; se veria como NULL.
LEFT JOIN telecom.velocidad v
  ON v.provincia_id = r.provincia_id AND v.anio = r.anio AND v.trimestre = r.trimestre
LEFT JOIN telecom.total_publicado t
  ON t.provincia_id = r.provincia_id AND t.anio = r.anio AND t.trimestre = r.trimestre;

-- VISTA 2: compara cada provincia con el mismo trimestre del anio anterior.
CREATE OR REPLACE VIEW telecom.v_crecimiento WITH (security_invoker = true) AS
WITH anterior AS (
    SELECT provincia_id, provincia, anio, trimestre, fecha, accesos_totales,
           -- LAG mira cuatro filas hacia atras, sin eliminar las filas actuales.
           LAG(accesos_totales, 4) OVER (
               PARTITION BY provincia_id ORDER BY anio, trimestre
           ) AS accesos_base,
           -- Verificamos que cuatro filas realmente equivalgan a cuatro trimestres.
           LAG(anio * 4 + trimestre, 4) OVER (
               PARTITION BY provincia_id ORDER BY anio, trimestre
           ) AS periodo_base
    FROM telecom.v_radiografia
)
SELECT provincia_id, provincia, anio, trimestre, fecha, accesos_totales,
       -- Si falta el periodo correcto, mostramos NULL en vez de comparar mal.
       CASE WHEN periodo_base = anio * 4 + trimestre - 4
            THEN accesos_base END AS accesos_hace_un_anio,
       CASE WHEN periodo_base = anio * 4 + trimestre - 4
            THEN ROUND(100.0 * (accesos_totales - accesos_base) / NULLIF(accesos_base, 0), 2)
       END AS crecimiento_interanual_pct
FROM anterior;

-- VISTA 3: ranking independiente para cada trimestre.
CREATE OR REPLACE VIEW telecom.v_ranking WITH (security_invoker = true) AS
SELECT provincia_id, provincia, anio, trimestre, fecha, accesos_totales, porcentaje_fibra, mbps,
       -- PARTITION BY reinicia el ranking en cada periodo; DESC pone el mayor primero.
       -- En un empate, RANK asigna el mismo puesto y deja un salto en el siguiente.
       RANK() OVER (PARTITION BY anio, trimestre ORDER BY mbps DESC NULLS LAST) AS ranking_velocidad,
       RANK() OVER (PARTITION BY anio, trimestre ORDER BY accesos_totales DESC) AS ranking_accesos
FROM telecom.v_radiografia;

REVOKE ALL ON telecom.v_radiografia, telecom.v_crecimiento, telecom.v_ranking FROM PUBLIC, anon, authenticated;
