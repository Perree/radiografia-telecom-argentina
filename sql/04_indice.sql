-- El indice comienza por las columnas usadas en el filtro de la consulta medida.
CREATE INDEX IF NOT EXISTS idx_acceso_tecnologia_anio
ON telecom.acceso (tecnologia_codigo, anio, trimestre);
