-- Una consulta relativamente costosa para ESTA tabla: filtra y agrega varias filas.
-- No representa millones de registros ni una carga de produccion.
SELECT provincia_id, anio, trimestre, SUM(cantidad) AS accesos_fibra
FROM telecom.acceso
WHERE tecnologia_codigo = 'fibra_optica' AND anio >= 2025
GROUP BY provincia_id, anio, trimestre
ORDER BY anio, trimestre, accesos_fibra DESC;
