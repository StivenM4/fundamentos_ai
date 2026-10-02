CREATE SCHEMA IF NOT EXISTS servicedesk;
SET search_path TO servicedesk, public;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 1. Catálogos y Entidades Base
CREATE TABLE IF NOT EXISTS servicedesk.prioridades_sla (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    sla_resolucion_minutos INTEGER NOT NULL,
    sla_respuesta_minutos INTEGER NOT NULL,
    nivel_escalamiento INTEGER NOT NULL DEFAULT 1,
    color_hex VARCHAR(10) NOT NULL DEFAULT '#000000',
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS servicedesk.estados_ticket (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    es_terminal BOOLEAN NOT NULL DEFAULT FALSE,
    orden_flujo INTEGER NOT NULL DEFAULT 1,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS servicedesk.usuarios (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    uuid UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    nombre VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    rol VARCHAR(30) NOT NULL DEFAULT 'EMISOR',
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS servicedesk.estaciones_trabajo (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo_inventario VARCHAR(50) NOT NULL UNIQUE,
    nombre_host VARCHAR(100) NOT NULL UNIQUE,
    direccion_ip INET NULL,
    direccion_mac MACADDR NULL,
    sistema_operativo VARCHAR(100) NOT NULL,
    ubicacion_area VARCHAR(100) NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'OPERATIVO',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS servicedesk.categorias_ticket (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT NULL,
    parent_id BIGINT NULL REFERENCES servicedesk.categorias_ticket (id) ON DELETE RESTRICT,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- 2. Taxonomía de IA y Activadores Semánticos (Semana 03)
CREATE TABLE IF NOT EXISTS servicedesk.taxonomia_ia_disciplinas (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS servicedesk.taxonomia_activadores (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    disciplina_id BIGINT NOT NULL REFERENCES servicedesk.taxonomia_ia_disciplinas (id) ON DELETE CASCADE,
    patron_lexico VARCHAR(150) NOT NULL,
    tipo_activador VARCHAR(50) NOT NULL DEFAULT 'PALABRA_CLAVE',
    es_regla_base BOOLEAN NOT NULL DEFAULT TRUE,
    peso NUMERIC(4, 2) NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS servicedesk.casos_ia (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(32) NOT NULL UNIQUE,
    descripcion TEXT NOT NULL,
    categoria_esperada VARCHAR(60) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Base de Conocimiento y Runbooks RAG (Semana 05)
CREATE TABLE IF NOT EXISTS servicedesk.articulos_sop_runbooks (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    runbook_codigo VARCHAR(50) NOT NULL UNIQUE,
    titulo VARCHAR(255) NOT NULL,
    contenido TEXT NOT NULL,
    precauciones_criticas TEXT NULL,
    categoria_id BIGINT NULL REFERENCES servicedesk.categorias_ticket (id) ON DELETE RESTRICT,
    search_vector tsvector NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tickets de Soporte y Entrenamiento IA (Semana 02)
CREATE TABLE IF NOT EXISTS servicedesk.tickets_soporte (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    numero_ticket VARCHAR(50) NOT NULL UNIQUE,
    asunto VARCHAR(255) NOT NULL,
    texto TEXT NOT NULL,
    descripcion_original TEXT NULL,
    categoria VARCHAR(50) NOT NULL,
    prioridad VARCHAR(30) NOT NULL,
    incidente VARCHAR(10) NOT NULL DEFAULT 'si',
    es_incidente BOOLEAN NOT NULL DEFAULT TRUE,
    categoria_id BIGINT NULL REFERENCES servicedesk.categorias_ticket (id) ON DELETE RESTRICT,
    prioridad_id BIGINT NULL REFERENCES servicedesk.prioridades_sla (id) ON DELETE RESTRICT,
    estado_id BIGINT NULL REFERENCES servicedesk.estados_ticket (id) ON DELETE RESTRICT,
    emisor_id BIGINT NULL REFERENCES servicedesk.usuarios (id) ON DELETE RESTRICT,
    estacion_id BIGINT NULL REFERENCES servicedesk.estaciones_trabajo (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4.1 Tickets reportados por Usuarios
CREATE TABLE IF NOT EXISTS servicedesk.tickets_usuario (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    numero_ticket VARCHAR(50) NOT NULL UNIQUE,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT NOT NULL,
    imagen_url VARCHAR(500) NULL,
    criticidad VARCHAR(50) NOT NULL DEFAULT 'Media',
    area_asignada VARCHAR(100) NOT NULL DEFAULT 'Soporte TI',
    es_incidente BOOLEAN NOT NULL DEFAULT TRUE,
    estado VARCHAR(50) NOT NULL DEFAULT 'Abierto',
    solucion_pasos TEXT NULL,
    sugerencia_ia JSONB NULL,
    criticidad_sugerida VARCHAR(50) NULL,
    area_sugerida VARCHAR(100) NULL,
    es_incidente_sugerido BOOLEAN NULL,
    confianza NUMERIC(5, 4) NULL,
    pasos_solucion JSONB NULL,
    analisis_causa TEXT NULL,
    tiene_manual BOOLEAN NULL DEFAULT FALSE,
    manual_titulo VARCHAR(255) NULL,
    manual_precauciones TEXT NULL,
    manual_checklist JSONB NULL,
    manual_id VARCHAR(50) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 5. Inferencias y Triage IA Supervisado (Semana 02)
CREATE TABLE IF NOT EXISTS servicedesk.inferencias_triaje_s02 (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ticket_id BIGINT NOT NULL REFERENCES servicedesk.tickets_soporte (id) ON DELETE CASCADE,
    categoria_predicha_id BIGINT NULL REFERENCES servicedesk.categorias_ticket (id) ON DELETE RESTRICT,
    prioridad_predicha_id BIGINT NULL REFERENCES servicedesk.prioridades_sla (id) ON DELETE RESTRICT,
    es_incidente BOOLEAN NOT NULL DEFAULT TRUE,
    score_confianza NUMERIC(5, 4) NOT NULL,
    version_modelo VARCHAR(50) NOT NULL DEFAULT 'v1.0.0-semana02',
    features_extraidas_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    ejecutado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 6. Planificación Heurística y Rutas A* (Semana 04)
CREATE TABLE IF NOT EXISTS servicedesk.rutas_resolucion_astar_s04 (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ticket_id BIGINT NULL REFERENCES servicedesk.tickets_soporte (id) ON DELETE CASCADE,
    codigo_ruta VARCHAR(64) NOT NULL UNIQUE,
    costo_total INTEGER NOT NULL,
    estados_explorados INTEGER NOT NULL,
    busqueda_ciega_estados INTEGER NOT NULL DEFAULT 12,
    ganancia_eficiencia_pct NUMERIC(5, 2) NOT NULL DEFAULT 50.0,
    meta_alcanzada BOOLEAN NOT NULL DEFAULT TRUE,
    ejecutado_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS servicedesk.pasos_ruta_astar_s04 (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ruta_id BIGINT NOT NULL REFERENCES servicedesk.rutas_resolucion_astar_s04 (id) ON DELETE CASCADE,
    numero_paso INTEGER NOT NULL,
    nodo_id VARCHAR(64) NOT NULL,
    titulo VARCHAR(120) NOT NULL,
    descripcion TEXT NULL,
    rol_responsable VARCHAR(80) NOT NULL,
    costo_acumulado_g INTEGER NOT NULL,
    heuristica_h INTEGER NOT NULL,
    evaluacion_f INTEGER NOT NULL,
    es_meta BOOLEAN NOT NULL DEFAULT FALSE,
    ejecutado BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_ruta_numero_paso UNIQUE (ruta_id, numero_paso)
);

-- 7. Feedback de Técnicos y Reentrenamiento
CREATE TABLE IF NOT EXISTS servicedesk.feedback_tickets_reentrenamiento (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ticket_id BIGINT NOT NULL REFERENCES servicedesk.tickets_soporte (id) ON DELETE CASCADE,
    usuario_id BIGINT NULL REFERENCES servicedesk.usuarios (id) ON DELETE SET NULL,
    categoria_corregida_id BIGINT NULL REFERENCES servicedesk.categorias_ticket (id) ON DELETE RESTRICT,
    prioridad_corregida_id BIGINT NULL REFERENCES servicedesk.prioridades_sla (id) ON DELETE RESTRICT,
    comentarios_tecnico TEXT NULL,
    marcado_para_reentrenamiento BOOLEAN NOT NULL DEFAULT TRUE,
    exportado_a_dataset BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_feedback TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Índices de Rendimiento y Búsqueda
CREATE INDEX IF NOT EXISTS idx_tickets_categoria ON servicedesk.tickets_soporte (categoria);
CREATE INDEX IF NOT EXISTS idx_tickets_prioridad ON servicedesk.tickets_soporte (prioridad);
CREATE INDEX IF NOT EXISTS idx_tickets_keyset ON servicedesk.tickets_soporte (created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_articulos_search_gin ON servicedesk.articulos_sop_runbooks USING GIN (search_vector);
CREATE INDEX IF NOT EXISTS idx_activadores_disciplina ON servicedesk.taxonomia_activadores (disciplina_id);
CREATE INDEX IF NOT EXISTS idx_feedback_reentrenamiento ON servicedesk.feedback_tickets_reentrenamiento (marcado_para_reentrenamiento, exportado_a_dataset);

-- Trigger para mantenimiento automático de búsqueda semántica y full-text (search_vector)
CREATE OR REPLACE FUNCTION servicedesk.articulos_sop_update_search_vector()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('spanish', coalesce(NEW.titulo, '') || ' ' || coalesce(NEW.contenido, '') || ' ' || coalesce(NEW.precauciones_criticas, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_articulos_sop_search_vector ON servicedesk.articulos_sop_runbooks;
CREATE TRIGGER trg_articulos_sop_search_vector
BEFORE INSERT OR UPDATE ON servicedesk.articulos_sop_runbooks
FOR EACH ROW EXECUTE FUNCTION servicedesk.articulos_sop_update_search_vector();
