-- Un esquema es una carpeta logica dentro de la base.
CREATE SCHEMA IF NOT EXISTS telecom;
-- Ningun usuario web recibe acceso a esta carpeta por defecto.
REVOKE ALL ON SCHEMA telecom FROM PUBLIC, anon, authenticated;

CREATE TABLE IF NOT EXISTS telecom.provincia (
    -- Postgres asigna un numero unico a cada provincia; no es un codigo de INDEC.
    provincia_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    -- NOT NULL exige un valor; UNIQUE impide repetir nombres.
    nombre text NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS telecom.periodo (
    anio smallint NOT NULL CHECK (anio >= 2014),
    trimestre smallint NOT NULL CHECK (trimestre BETWEEN 1 AND 4),
    -- La combinacion de las dos columnas identifica el periodo.
    PRIMARY KEY (anio, trimestre)
);

CREATE TABLE IF NOT EXISTS telecom.tecnologia (
    codigo text PRIMARY KEY,
    nombre text NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS telecom.acceso (
    -- REFERENCES exige que la provincia y tecnologia existan en sus tablas.
    provincia_id bigint NOT NULL REFERENCES telecom.provincia(provincia_id),
    anio smallint NOT NULL,
    trimestre smallint NOT NULL,
    tecnologia_codigo text NOT NULL REFERENCES telecom.tecnologia(codigo),
    -- bigint guarda cantidades enteras; cero es valido.
    cantidad bigint NOT NULL CHECK (cantidad >= 0),
    PRIMARY KEY (provincia_id, anio, trimestre, tecnologia_codigo),
    FOREIGN KEY (anio, trimestre) REFERENCES telecom.periodo(anio, trimestre)
);

CREATE TABLE IF NOT EXISTS telecom.velocidad (
    provincia_id bigint NOT NULL REFERENCES telecom.provincia(provincia_id),
    anio smallint NOT NULL,
    trimestre smallint NOT NULL,
    -- numeric conserva decimales exactos. No redondeamos la fuente al cargar.
    mbps numeric NOT NULL CHECK (mbps >= 0 AND mbps < 'Infinity'::numeric),
    PRIMARY KEY (provincia_id, anio, trimestre),
    FOREIGN KEY (anio, trimestre) REFERENCES telecom.periodo(anio, trimestre)
);

CREATE TABLE IF NOT EXISTS telecom.total_publicado (
    provincia_id bigint NOT NULL REFERENCES telecom.provincia(provincia_id),
    anio smallint NOT NULL,
    trimestre smallint NOT NULL,
    cantidad bigint NOT NULL CHECK (cantidad >= 0),
    PRIMARY KEY (provincia_id, anio, trimestre),
    FOREIGN KEY (anio, trimestre) REFERENCES telecom.periodo(anio, trimestre)
);

-- Proteccion adicional: el acceso se hace con SQL administrativo, no desde una web.
ALTER TABLE telecom.provincia ENABLE ROW LEVEL SECURITY;
ALTER TABLE telecom.periodo ENABLE ROW LEVEL SECURITY;
ALTER TABLE telecom.tecnologia ENABLE ROW LEVEL SECURITY;
ALTER TABLE telecom.acceso ENABLE ROW LEVEL SECURITY;
ALTER TABLE telecom.velocidad ENABLE ROW LEVEL SECURITY;
ALTER TABLE telecom.total_publicado ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON ALL TABLES IN SCHEMA telecom FROM PUBLIC, anon, authenticated;
