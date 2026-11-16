-- =============================================================================
-- Plantillas DDL y Consultas Analíticas PostgreSQL + JSONB (Encuestas / PDUL)
-- =============================================================================

-- 1. ESQUEMA BASE Y RESTRICCIONES
CREATE TABLE IF NOT EXISTS encuestas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo VARCHAR(255) NOT NULL,
    slug VARCHAR(120) UNIQUE NOT NULL,
    tipo_instrumento VARCHAR(30) NOT NULL DEFAULT 'consulta_ciudadana',
    esquema_formio JSONB NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS respuestas_ciudadanas (
    id BIGSERIAL PRIMARY KEY,
    encuesta_id UUID NOT NULL REFERENCES encuestas(id) ON DELETE RESTRICT,
    client_submission_id UUID UNIQUE,
    cedula VARCHAR(15),
    parroquia VARCHAR(60) NOT NULL,
    zona_od VARCHAR(30),
    datos JSONB NOT NULL,
    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_voto_ciudadano UNIQUE (encuesta_id, cedula),
    CONSTRAINT chk_datos_jsonb_object CHECK (jsonb_typeof(datos) = 'object')
);

-- 2. ÍNDICES DE ALTO RENDIMIENTO
CREATE INDEX IF NOT EXISTS idx_respuestas_datos_gin
    ON respuestas_ciudadanas USING GIN (datos jsonb_path_ops);

CREATE INDEX IF NOT EXISTS idx_respuestas_encuesta_parroquia
    ON respuestas_ciudadanas (encuesta_id, parroquia);

CREATE INDEX IF NOT EXISTS idx_respuestas_encuesta_zona_od
    ON respuestas_ciudadanas (encuesta_id, zona_od);

-- 3. CONSULTA DE CONTEO POR PARROQUIA (Para Mapa Coroplético en Leaflet)
-- Parámetro: :encuesta_id
SELECT
    parroquia,
    COUNT(*) AS total_respuestas,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS porcentaje
FROM respuestas_ciudadanas
WHERE encuesta_id = :encuesta_id
GROUP BY parroquia
ORDER BY total_respuestas DESC;

-- 4. MATRIZ ORIGEN-DESTINO (Sección V: Arreglo 'viajes' dentro de JSONB)
-- Desagrega cada viaje del hogar usando jsonb_array_elements de forma segura
SELECT
    v.viaje->>'zona_od_origen' AS zona_origen,
    v.viaje->>'zona_od_destino' AS zona_destino,
    COUNT(*) AS total_viajes,
    ROUND(AVG(NULLIF(trim(v.viaje->>'tiempo_viaje_min'), '')::NUMERIC), 1) AS tiempo_promedio_min,
    ROUND(AVG(NULLIF(trim(v.viaje->>'costo_viaje_bs'), '')::NUMERIC), 2) AS costo_promedio_bs
FROM respuestas_ciudadanas r
CROSS JOIN LATERAL jsonb_array_elements(
    CASE
        WHEN jsonb_typeof(r.datos->'viajes') = 'array' THEN r.datos->'viajes'
        ELSE '[]'::jsonb
    END
) AS v(viaje)
WHERE r.encuesta_id = :encuesta_id
  AND v.viaje->>'zona_od_origen' IS NOT NULL
  AND v.viaje->>'zona_od_destino' IS NOT NULL
GROUP BY zona_origen, zona_destino
ORDER BY total_viajes DESC;

-- 5. REPARTO MODAL Y MOTIVO DE VIAJE (Para Gráficos Apache ECharts)
SELECT
    v.viaje->>'modo_principal' AS codigo_modo,
    v.viaje->>'motivo_viaje' AS codigo_motivo,
    COUNT(*) AS cantidad_viajes
FROM respuestas_ciudadanas r
CROSS JOIN LATERAL jsonb_array_elements(
    CASE
        WHEN jsonb_typeof(r.datos->'viajes') = 'array' THEN r.datos->'viajes'
        ELSE '[]'::jsonb
    END
) AS v(viaje)
WHERE r.encuesta_id = :encuesta_id
GROUP BY codigo_modo, codigo_motivo
ORDER BY cantidad_viajes DESC;

-- 6. AGREGACIÓN DE PREGUNTAS MULTIRRESPUESTA ('selectboxes' de Form.io)
-- Ejemplo: Sección VIII P2 (actividades_espacios: {"caminar": true, "deporte": false})
SELECT
    kv.key AS opcion,
    COUNT(*) AS seleccionados
FROM respuestas_ciudadanas r
CROSS JOIN LATERAL jsonb_each_text(
    CASE
        WHEN jsonb_typeof(r.datos->'actividades_espacios') = 'object'
        THEN r.datos->'actividades_espacios'
        ELSE '{}'::jsonb
    END
) AS kv(key, value)
WHERE r.encuesta_id = :encuesta_id
  AND kv.value = 'true'
GROUP BY kv.key
ORDER BY seleccionados DESC;

