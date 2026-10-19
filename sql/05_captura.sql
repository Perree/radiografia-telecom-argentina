-- Una consulta captura las seis tablas dentro de la misma fotografia de la base.
-- Cada subconsulta agrega sus filas en JSON; no une tablas y no multiplica datos.
SELECT jsonb_build_object(
    'capturado_en_utc', now(),
    'tablas', jsonb_build_object(
        'provincia', (SELECT jsonb_agg(p ORDER BY provincia_id) FROM telecom.provincia p),
        'periodo', (SELECT jsonb_agg(p ORDER BY anio,trimestre) FROM telecom.periodo p),
        'tecnologia', (SELECT jsonb_agg(t ORDER BY codigo) FROM telecom.tecnologia t),
        'acceso', (SELECT jsonb_agg(a ORDER BY provincia_id,anio,trimestre,tecnologia_codigo) FROM telecom.acceso a),
        'velocidad', (SELECT jsonb_agg(v ORDER BY provincia_id,anio,trimestre) FROM telecom.velocidad v),
        'total_publicado', (SELECT jsonb_agg(t ORDER BY provincia_id,anio,trimestre) FROM telecom.total_publicado t)
    )
) AS captura;
