SET search_path TO servicedesk, public;

INSERT INTO servicedesk.prioridades_sla (codigo, nombre, sla_resolucion_minutos, sla_respuesta_minutos, nivel_escalamiento, color_hex) VALUES ('CRITICA', 'Critica (Caida Total)', 60, 15, 4, '#DC2626'), ('ALTA', 'Alta (Afectacion Grave / VPN)', 120, 30, 3, '#EA580C'), ('MEDIA', 'Media (Incidente Parcial)', 240, 60, 2, '#D97706'), ('BAJA', 'Baja (Consulta General)', 480, 120, 1, '#16A34A') ON CONFLICT (codigo) DO NOTHING;

INSERT INTO servicedesk.estados_ticket (codigo, nombre, es_terminal, orden_flujo) VALUES ('ABIERTO', 'Abierto / Recibido', FALSE, 1), ('EN_TRIAJE_IA', 'En Triaje y Diagnostico IA', FALSE, 2), ('ASIGNADO', 'Asignado a Tecnico', FALSE, 3), ('EN_DIAGNOSTICO', 'En Diagnostico', FALSE, 4), ('EN_EJECUCION_SOP', 'En Ejecucion de SOP', FALSE, 5), ('RESUELTO', 'Resuelto / Solucion Aplicada', FALSE, 6), ('CERRADO', 'Cerrado Definitivo', TRUE, 7) ON CONFLICT (codigo) DO NOTHING;

INSERT INTO servicedesk.categorias_ticket (codigo, nombre, descripcion) VALUES ('hardware', 'Hardware y Perifericos', 'Fallas fisicas'), ('software', 'Software y Aplicaciones', 'Fallas en programas'), ('red', 'Redes y Conectividad', 'Fallas en WiFi'), ('accesos', 'Accesos y Credenciales', 'Bloqueos de AD') ON CONFLICT (codigo) DO NOTHING;

INSERT INTO servicedesk.taxonomia_ia_disciplinas (codigo, nombre, descripcion) VALUES ('NLP', 'Procesamiento de lenguaje natural', 'Análisis de texto'), ('CV', 'Visión por computador', 'Inspección de capturas'), ('ML_PRED', 'Aprendizaje predictivo', 'Pronóstico de demanda'), ('REC_SYS', 'Sistemas de recomendación', 'Sugerencia de SOPs'), ('EXP_SYS', 'Sistemas expertos', 'Reglas deterministas'), ('GEN_AI', 'IA generativa', 'Redacción de respuestas'), ('ROBOTICA', 'Robótica', 'Automatización y agentes') ON CONFLICT (codigo) DO UPDATE SET nombre = EXCLUDED.nombre, descripcion = EXCLUDED.descripcion;

INSERT INTO servicedesk.usuarios (nombre, email, rol) VALUES ('Sistema Inteligente IA', 'ai.system@empresa.com', 'SISTEMA_IA'), ('Operador Mesa de Ayuda', 'mesa.ayuda@empresa.com', 'TECNICO_L1') ON CONFLICT (email) DO NOTHING;
