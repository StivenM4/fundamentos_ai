from __future__ import annotations

import datetime
import json
import os
import re
import sys
import unicodedata
import uuid
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
import pandas as pd

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "SoporteAIBD")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "12345")


class UniversalDbConnection:
    """Wrapper para lanzar consultas sin importar qué driver de PostgreSQL esté instalado en el entorno."""

    def __init__(self, raw_conn: Any, driver: str):
        self.raw_conn = raw_conn
        self.driver = driver
        self._in_transaction = False

    def begin(self) -> None:
        """Abre una transacción explícita en la sesión actual."""
        if self.driver == "pg8000":
            try:
                self.raw_conn.run("BEGIN;")
            except Exception:
                pass
        self._in_transaction = True

    def commit(self) -> None:
        """Confirma los cambios pendientes de la transacción en la base de datos."""
        if self.driver == "pg8000":
            if self._in_transaction:
                try:
                    self.raw_conn.run("COMMIT;")
                except Exception:
                    pass
                self._in_transaction = False
        elif self.driver in ("psycopg2", "psycopg"):
            self.raw_conn.commit()
            self._in_transaction = False

    def rollback(self) -> None:
        """Hace rollback inmediato si alguna sentencia revienta durante la transacción."""
        if self.driver == "pg8000":
            if self._in_transaction:
                try:
                    self.raw_conn.run("ROLLBACK;")
                except Exception:
                    pass
                self._in_transaction = False
        elif self.driver in ("psycopg2", "psycopg"):
            try:
                self.raw_conn.rollback()
            except Exception:
                pass
            self._in_transaction = False

    def __enter__(self) -> UniversalDbConnection:
        self.begin()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()

    def run(self, sql: str, params: Optional[Union[tuple, list, dict]] = None) -> List[List[Any]]:
        if self.driver == "pg8000":
            if params:
                res = self.raw_conn.run(sql, **params if isinstance(params, dict) else params)
            else:
                res = self.raw_conn.run(sql)
            return res if res is not None else []
        elif self.driver in ("psycopg2", "psycopg"):
            cur = self.raw_conn.cursor()
            try:
                adapted_sql = sql
                if params and isinstance(params, dict):
                    for k in params.keys():
                        adapted_sql = re.sub(rf":{k}\b", f"%({k})s", adapted_sql)
                cur.execute(adapted_sql, params)
                if cur.description:
                    rows = [list(r) for r in cur.fetchall()]
                    if not self._in_transaction:
                        self.raw_conn.commit()
                    return rows
                if not self._in_transaction:
                    self.raw_conn.commit()
                return []
            except Exception:
                if not self._in_transaction:
                    try:
                        self.raw_conn.rollback()
                    except Exception:
                        pass
                raise
            finally:
                cur.close()
        raise RuntimeError(f"Driver desconocido: {self.driver}")

    def close(self) -> None:
        try:
            self.raw_conn.close()
        except Exception:
            pass


_DETECTED_DRIVER: Optional[str] = None


def _connect_pg8000() -> UniversalDbConnection:
    import pg8000.native
    c = pg8000.native.Connection(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT,
        timeout=5,
    )
    return UniversalDbConnection(c, "pg8000")


def _connect_psycopg2() -> UniversalDbConnection:
    import psycopg2
    c = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        connect_timeout=5,
    )
    return UniversalDbConnection(c, "psycopg2")


def _connect_psycopg() -> UniversalDbConnection:
    import psycopg
    c = psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        connect_timeout=5,
    )
    return UniversalDbConnection(c, "psycopg")


_DRIVER_FACTORIES: Dict[str, Any] = {
    "pg8000": _connect_pg8000,
    "psycopg2": _connect_psycopg2,
    "psycopg": _connect_psycopg,
}


def get_db_connection() -> Optional[UniversalDbConnection]:
    """Intenta conectar a "PostgreSQL 18" probando en orden "pg8000", "psycopg2" o "psycopg", y guarda en caché el driver que funcione."""
    global _DETECTED_DRIVER

    if _DETECTED_DRIVER and _DETECTED_DRIVER in _DRIVER_FACTORIES:
        try:
            return _DRIVER_FACTORIES[_DETECTED_DRIVER]()
        except Exception:
            _DETECTED_DRIVER = None

    for driver_name, factory in _DRIVER_FACTORIES.items():
        try:
            conn = factory()
            _DETECTED_DRIVER = driver_name
            return conn
        except Exception:
            continue

    return None


def save_visual_capture_audit(
    saved_filename: str,
    clase_detectada: str,
    confianza: float,
) -> None:
    """Guarda el registro de auditoría de la imagen en "PostgreSQL" y en "SQLite" con modo WAL para no generar bloqueos."""
    import sqlite3
    from pathlib import Path
    clean_conf = float(round(confianza, 4))
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    conn = get_db_connection()
    if conn:
        try:
            conn.run(
                "CREATE TABLE IF NOT EXISTS servicedesk.capturas_tickets ("
                "id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, "
                "archivo VARCHAR(255) NOT NULL, "
                "clase_detectada VARCHAR(100) NOT NULL, "
                "confianza NUMERIC(5, 4) NOT NULL, "
                "timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);"
            )
            conn.run(
                "CREATE INDEX IF NOT EXISTS idx_capturas_pg_timestamp ON servicedesk.capturas_tickets (timestamp DESC);"
            )
            conn.run(
                "INSERT INTO servicedesk.capturas_tickets (archivo, clase_detectada, confianza) "
                "VALUES (:archivo, :clase, :conf);",
                {"archivo": saved_filename, "clase": clase_detectada, "conf": clean_conf},
            )
        except Exception as exc:
            print(f"Advertencia registrando captura en PostgreSQL: {exc}")
        finally:
            conn.close()

    try:
        project_root = Path(__file__).resolve().parents[1]
        db_path = project_root / "artifacts" / "imagenes.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path, timeout=10.0) as con:
            # Tolerancia a bloqueos y concurrencia ágil en SQLite
            con.execute("PRAGMA journal_mode = WAL;")
            con.execute("PRAGMA foreign_keys = ON;")
            con.execute("PRAGMA busy_timeout = 10000;")
            con.execute("PRAGMA synchronous = NORMAL;")
            con.execute(
                "CREATE TABLE IF NOT EXISTS capturas_tickets("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "archivo TEXT NOT NULL, "
                "clase_detectada TEXT NOT NULL, "
                "confianza REAL NOT NULL, "
                "timestamp DATETIME NOT NULL)"
            )
            con.execute(
                "CREATE INDEX IF NOT EXISTS idx_capturas_sqlite_timestamp ON capturas_tickets(timestamp DESC);"
            )
            con.execute(
                "INSERT INTO capturas_tickets(archivo, clase_detectada, confianza, timestamp) VALUES (?, ?, ?, ?)",
                (saved_filename, clase_detectada, clean_conf, now_iso),
            )
            con.commit()
    except Exception as exc:
        print(f"Advertencia registrando captura en SQLite: {exc}")


def execute_query(sql: str, params: Optional[Union[tuple, list, dict]] = None) -> Optional[List[List[Any]]]:
    """Lanza una consulta SQL directa contra "PostgreSQL 18" y retorna la lista de filas."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        rows = conn.run(sql, params)
        return rows
    except Exception:
        return None
    finally:
        conn.close()


def check_db_health() -> Dict[str, Any]:
    """Verifica si la base de datos "PostgreSQL 18" está viva tirando un "SELECT version();"."""
    conn = get_db_connection()
    if conn is None:
        return {
            "connected": False,
            "engine": "PostgreSQL 18",
            "database": DB_NAME,
            "host": DB_HOST,
            "port": DB_PORT,
            "error": "No se pudo establecer conexión con PostgreSQL 18.",
        }
    try:
        rows = conn.run("SELECT version();")
        version_str = str(rows[0][0]) if rows and rows[0] else "PostgreSQL 18"
        return {
            "connected": True,
            "engine": "PostgreSQL 18",
            "version": version_str,
            "database": DB_NAME,
            "host": DB_HOST,
            "port": DB_PORT,
            "driver": conn.driver,
        }
    except Exception as exc:
        return {
            "connected": False,
            "engine": "PostgreSQL 18",
            "database": DB_NAME,
            "host": DB_HOST,
            "port": DB_PORT,
            "error": str(exc),
        }
    finally:
        conn.close()


def load_tickets_data(require_db: bool = False) -> Optional[pd.DataFrame]:
    """Carga los tickets históricos desde "servicedesk.tickets_soporte" en PostgreSQL 18.
    
    Devuelve un DataFrame con ["texto", "categoria", "prioridad", "incidente"].
    """
    conn = get_db_connection()
    if conn is None:
        if require_db:
            raise ConnectionError(
                f"Error al conectar con PostgreSQL 18 en {DB_HOST}:{DB_PORT}/{DB_NAME} para cargar tickets."
            )
        return None

    try:
        rows = conn.run(
            "SELECT texto, categoria, prioridad, incidente "
            "FROM servicedesk.tickets_soporte "
            "ORDER BY id ASC;"
        )
        if rows and len(rows) > 0:
            df = pd.DataFrame(rows, columns=["texto", "categoria", "prioridad", "incidente"])
            # Sanitizamos espacios y unificamos texto a minúsculas
            df["texto"] = df["texto"].astype(str).str.strip()
            df["categoria"] = df["categoria"].astype(str).str.strip().str.lower()
            df["prioridad"] = df["prioridad"].astype(str).str.strip().str.lower()
            df["incidente"] = df["incidente"].astype(str).str.strip().str.lower()
            return df
    except Exception as exc:
        if require_db:
            raise RuntimeError(f"Error consultando servicedesk.tickets_soporte: {exc}")
    finally:
        conn.close()

    if require_db:
        raise RuntimeError("La tabla servicedesk.tickets_soporte no contiene registros.")
    return None


def load_knowledge_base_docs(require_db: bool = False) -> Optional[List[str]]:
    """Carga los runbooks y manuales operativos desde "servicedesk.articulos_sop_runbooks" en PostgreSQL 18."""
    conn = get_db_connection()
    if conn is None:
        if require_db:
            raise ConnectionError(
                f"Error al conectar con PostgreSQL 18 en {DB_HOST}:{DB_PORT}/{DB_NAME} para base de conocimiento."
            )
        return None

    try:
        rows = conn.run(
            "SELECT CASE "
            "  WHEN titulo IS NOT NULL AND contenido NOT LIKE '%' || substring(titulo from 1 for 20) || '%' "
            "  THEN titulo || ': ' || contenido "
            "  ELSE COALESCE(contenido, titulo) "
            "END "
            "FROM servicedesk.articulos_sop_runbooks "
            "ORDER BY id ASC;"
        )
        if rows and len(rows) > 0:
            docs = [str(r[0]).strip().replace("\r\n", " ").replace("\n", " ") for r in rows if r[0] and str(r[0]).strip()]
            if len(docs) >= 8:
                return docs
    except Exception as exc:
        if require_db:
            raise RuntimeError(f"Error consultando servicedesk.articulos_sop_runbooks: {exc}")
    finally:
        conn.close()

    if require_db:
        raise RuntimeError("La tabla servicedesk.articulos_sop_runbooks no contiene suficientes artículos (mínimo 8).")
    return None


def query_knowledge_manuals(
    query: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Optional[Tuple[int, List[Dict[str, Any]]]]:
    """Consulta los manuales de "servicedesk.articulos_sop_runbooks" con filtro de búsqueda y paginación con "limit" y "offset"."""
    conn = get_db_connection()
    if conn is None:
        return None

    try:
        where_sql = "activo = TRUE"
        params = {}
        if query and str(query).strip():
            params["q"] = f"%{str(query).strip()}%"
            where_sql += " AND (titulo ILIKE :q OR contenido ILIKE :q OR runbook_codigo ILIKE :q)"

        count_rows = conn.run(f"SELECT COUNT(*) FROM servicedesk.articulos_sop_runbooks WHERE {where_sql};", params if params else None)
        total_count = int(count_rows[0][0]) if count_rows and count_rows[0] else 0

        fetch_params = dict(params)
        fetch_params["limit"] = int(limit)
        fetch_params["offset"] = int(offset)

        fetch_sql = (
            f"SELECT id, runbook_codigo, titulo, contenido, precauciones_criticas "
            f"FROM servicedesk.articulos_sop_runbooks "
            f"WHERE {where_sql} "
            f"ORDER BY id ASC "
            f"LIMIT :limit OFFSET :offset;"
        )
        rows = conn.run(fetch_sql, fetch_params)
        manuals: List[Dict[str, Any]] = []
        if rows:
            for r in rows:
                manuals.append({
                    "id": r[0],
                    "code": str(r[1]),
                    "title": str(r[2]),
                    "content": str(r[3]),
                    "precautions": str(r[4]) if r[4] is not None else None,
                    "category": None,
                    "source": "PostgreSQL 18 (servicedesk.articulos_sop_runbooks)",
                })
        return total_count, manuals
    except Exception as exc:
        print(f"Error consultando articulos_sop_runbooks: {exc}")
        return None
    finally:
        conn.close()


def load_cases_data(require_db: bool = False) -> Optional[List[str]]:
    """Carga los casos de prueba de IA guardados en "servicedesk.casos_ia" en PostgreSQL 18."""
    conn = get_db_connection()
    if conn is None:
        if require_db:
            raise ConnectionError(
                f"Error al conectar con PostgreSQL 18 en {DB_HOST}:{DB_PORT}/{DB_NAME} para casos IA."
            )
        return None

    try:
        rows = conn.run("SELECT descripcion FROM servicedesk.casos_ia ORDER BY id ASC;")
        if rows and len(rows) > 0:
            cases = [str(r[0]).strip() for r in rows if r[0] and str(r[0]).strip()]
            if len(cases) >= 20:
                return cases
    except Exception as exc:
        if require_db:
            raise RuntimeError(f"Error consultando servicedesk.casos_ia: {exc}")
    finally:
        conn.close()

    if require_db:
        raise RuntimeError("La tabla servicedesk.casos_ia no contiene suficientes casos (mínimo 20).")
    return None


def normalize_discipline_name(name: str, code: Optional[str] = None) -> str:
    """Normaliza nombres y códigos de disciplinas de IA al formato estándar de "semana03_taxonomia"."""
    if code:
        code_clean = str(code).strip().upper()
        code_map = {
            "NLP": "Procesamiento de lenguaje natural",
            "CV": "Visión por computador",
            "ML_PRED": "Aprendizaje predictivo",
            "REC_SYS": "Sistemas de recomendación",
            "EXP_SYS": "Sistemas expertos",
            "GEN_AI": "IA generativa",
            "ROBOTICA": "Robótica",
            "ROB": "Robótica",
        }
        if code_clean in code_map:
            return code_map[code_clean]

    if not name:
        return name

    decomposed = unicodedata.normalize("NFKD", str(name))
    unaccented = "".join(c for c in decomposed if unicodedata.category(c) != "Mn").lower().strip()

    name_map = {
        "procesamiento de lenguaje natural": "Procesamiento de lenguaje natural",
        "vision por computador": "Visión por computador",
        "aprendizaje predictivo": "Aprendizaje predictivo",
        "sistemas de recomendacion": "Sistemas de recomendación",
        "sistemas expertos": "Sistemas expertos",
        "ia generativa": "IA generativa",
        "robotica": "Robótica",
        "robtica": "Robótica",
    }
    if unaccented in name_map:
        return name_map[unaccented]

    if "lenguaje" in unaccented or "natural" in unaccented or "nlp" in unaccented:
        return "Procesamiento de lenguaje natural"
    if "vision" in unaccented or "computador" in unaccented:
        return "Visión por computador"
    if "predictiv" in unaccented or "aprendizaje" in unaccented:
        return "Aprendizaje predictivo"
    if "recomend" in unaccented:
        return "Sistemas de recomendación"
    if "experto" in unaccented:
        return "Sistemas expertos"
    if "generativ" in unaccented:
        return "IA generativa"
    if "robot" in unaccented:
        return "Robótica"

    return str(name).strip()


def load_taxonomy_rules(
    require_db: bool = False,
) -> Optional[Tuple[Dict[str, Tuple[str, ...]], Dict[str, Tuple[str, ...]]]]:
    """Carga los activadores léxicos y disciplinas desde "servicedesk.taxonomia_activadores" en PostgreSQL 18.
    
    Retorna la tupla "(base_rules, custom_rules)" con diccionarios {"disciplina": tuple_de_activadores}
    canónicos según la ontología de Semana 03.
    """
    conn = get_db_connection()
    if conn is None:
        if require_db:
            raise ConnectionError(
                f"Error al conectar con PostgreSQL 18 en {DB_HOST}:{DB_PORT}/{DB_NAME} para taxonomía."
            )
        return None

    try:
        rows = conn.run(
            "SELECT d.nombre, a.patron_lexico, COALESCE(a.tipo_activador, 'BASE'), COALESCE(a.es_regla_base, TRUE), d.codigo "
            "FROM servicedesk.taxonomia_activadores a "
            "JOIN servicedesk.taxonomia_ia_disciplinas d ON a.disciplina_id = d.id "
            "WHERE d.activo = TRUE "
            "ORDER BY a.id ASC;"
        )
        if rows and len(rows) > 0:
            base_dict: Dict[str, List[str]] = {}
            custom_dict: Dict[str, List[str]] = {}

            for row in rows:
                raw_disciplina = str(row[0]).strip()
                patron = str(row[1]).strip()
                tipo = str(row[2]).strip().upper()
                es_base = bool(row[3])
                codigo = str(row[4]).strip() if len(row) > 4 and row[4] else None

                disciplina = normalize_discipline_name(raw_disciplina, codigo)

                is_custom = (tipo == "CUSTOM") or (not es_base)
                target = custom_dict if is_custom else base_dict

                if disciplina not in target:
                    target[disciplina] = []
                if patron and patron not in target[disciplina]:
                    target[disciplina].append(patron)

            base_rules = {k: tuple(v) for k, v in base_dict.items()}
            custom_rules = {k: tuple(v) for k, v in custom_dict.items()}

            if base_rules or custom_rules:
                return base_rules, custom_rules
    except Exception as exc:
        if require_db:
            raise RuntimeError(f"Error consultando taxonomia en PostgreSQL: {exc}")
    finally:
        conn.close()

    if require_db:
        raise RuntimeError("No se encontraron reglas en servicedesk.taxonomia_activadores.")
    return None


def save_astar_route_to_db(
    ticket_id: Optional[int],
    route_code: str,
    total_cost: int,
    expanded_states: int,
    blind_search_states: int,
    efficiency_pct: float,
    steps: List[Dict[str, Any]],
) -> Optional[int]:
    """Guarda en "servicedesk.rutas_resolucion_astar_s04" y sus pasos la ruta calculada por el algoritmo A*."""
    conn = get_db_connection()
    if conn is None:
        return None

    try:
        conn.begin()
        insert_route_sql = """
            INSERT INTO servicedesk.rutas_resolucion_astar_s04 
            (ticket_id, codigo_ruta, costo_total, estados_explorados, busqueda_ciega_estados, ganancia_eficiencia_pct, meta_alcanzada) 
            VALUES (:ticket_id, :route_code, :total_cost, :expanded_states, :blind_states, :eff_pct, TRUE) 
            RETURNING id;
        """
        route_params = {
            "ticket_id": int(ticket_id) if ticket_id is not None else None,
            "route_code": str(route_code),
            "total_cost": int(total_cost),
            "expanded_states": int(expanded_states),
            "blind_states": int(blind_search_states),
            "eff_pct": float(efficiency_pct),
        }
        res = conn.run(insert_route_sql, route_params)
        if not res or not res[0]:
            conn.rollback()
            return None
        ruta_id = res[0][0]

        insert_step_sql = """
            INSERT INTO servicedesk.pasos_ruta_astar_s04 
            (ruta_id, numero_paso, nodo_id, titulo, descripcion, rol_responsable, costo_acumulado_g, heuristica_h, evaluacion_f, es_meta) 
            VALUES (:ruta_id, :num, :nid, :title, :desc, :role, :g, :h, :f, :is_goal) 
            ON CONFLICT (ruta_id, numero_paso) DO NOTHING;
        """
        for step in steps:
            step_params = {
                "ruta_id": int(ruta_id),
                "num": int(step.get("step_number", 1)),
                "nid": str(step.get("node_id", "")),
                "title": str(step.get("title", "")),
                "desc": str(step.get("description", "")),
                "role": str(step.get("role", "")),
                "g": int(step.get("g", 0)),
                "h": int(step.get("h", 0)),
                "f": int(step.get("f", 0)),
                "is_goal": bool(step.get("is_goal", False)),
            }
            conn.run(insert_step_sql, step_params)

        conn.commit()
        return ruta_id
    except Exception:
        conn.rollback()
        return None
    finally:
        conn.close()


# Tickets de contingencia en memoria por si PostgreSQL se cae o no conecta

_FALLBACK_TICKETS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "numero_ticket": "TCK-2026-00001",
        "titulo": "Fallo de autenticación VPN SSL corporativa tras actualización",
        "descripcion": "El usuario no puede conectar al concentrador VPN corporativo desde red externa tras actualización de certificados y SO.",
        "imagen_url": None,
        "criticidad": "Alta",
        "area_asignada": "Redes",
        "es_incidente": True,
        "estado": "En Proceso",
        "solucion_pasos": "1. Depurar handshake TLS en cliente OpenVPN.\n2. Renovar bundle CA intermedio.\n3. Validar resolución DNS split-tunnel.",
        "sugerencia_ia": {
            "categoria": "redes",
            "confianza": 0.94,
            "runbook": "RB-RED-001",
            "recomendacion": "Revisar logs de enlace y perfiles IKEv2/SSL",
        },
        "created_at": "2026-09-30T10:00:00+00:00",
        "updated_at": "2026-09-30T10:00:00+00:00",
    },
    {
        "id": 2,
        "numero_ticket": "TCK-2026-00002",
        "titulo": "Aprovisionamiento de credenciales y rol de sólo lectura en PostgreSQL",
        "descripcion": "Se solicita acceso read-only al esquema servicedesk para nuevo analista del equipo de inteligencia de negocios.",
        "imagen_url": None,
        "criticidad": "Media",
        "area_asignada": "Base de Datos",
        "es_incidente": False,
        "estado": "Abierto",
        "solucion_pasos": None,
        "sugerencia_ia": {
            "categoria": "accesos",
            "confianza": 0.91,
            "runbook": "RB-SEC-004",
            "recomendacion": "Asignar rol r_readonly y limitar a SELECT en esquema servicedesk",
        },
        "created_at": "2026-09-30T10:05:00+00:00",
        "updated_at": "2026-09-30T10:05:00+00:00",
    },
    {
        "id": 3,
        "numero_ticket": "TCK-2026-00003",
        "titulo": "Error crítico pantalla azul (BSOD) durante inferencia y carga de modelos",
        "descripcion": "La estación de trabajo de analítica sufre caídas de kernel DRIVER_IRQL_NOT_LESS_OR_EQUAL al inicializar aceleración por GPU CUDA.",
        "imagen_url": None,
        "criticidad": "Crítica",
        "area_asignada": "Hardware",
        "es_incidente": True,
        "estado": "Resuelto",
        "solucion_pasos": "1. Ejecutar DDU en modo seguro para limpiar controladores residuales.\n2. Instalar controlador NVIDIA Studio WHQL versión certificada.\n3. Ejecutar pruebas de estrés GPU/VRAM con resultado satisfactorio.",
        "sugerencia_ia": {
            "categoria": "hardware",
            "confianza": 0.98,
            "runbook": "RB-HW-003",
            "recomendacion": "Verificar firmware PCIe y temperatura de operación en carga máxima",
        },
        "created_at": "2026-09-30T10:10:00+00:00",
        "updated_at": "2026-09-30T10:10:00+00:00",
    },
]


def _json_serial_default(obj: Any) -> Any:
    """Serializa modelos Pydantic y fechas para poder meterlos en columnas "JSONB" de PostgreSQL."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return str(obj)


def _to_iso(dt_or_str: Any) -> Optional[str]:
    """Pasa objetos datetime a formato de texto ISO sin complicaciones."""
    if dt_or_str is None:
        return None
    return dt_or_str.isoformat() if hasattr(dt_or_str, "isoformat") else str(dt_or_str)


def _ensure_list(val: Any) -> List[Any]:
    """Garantiza que el valor retornado sea una lista, deserializando el JSON si viene como texto."""
    if not val:
        return []
    if isinstance(val, list):
        return list(val)
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, list) else [parsed]
        except Exception:
            return [val]
    return [val]


def _row_to_ticket_dict(row: Sequence[Any]) -> Dict[str, Any]:
    """Mapea una fila cruda de "servicedesk.tickets_usuario" a un diccionario estructurado para los endpoints."""
    sugerencia = row[10]
    if isinstance(sugerencia, str):
        try:
            sugerencia = json.loads(sugerencia)
        except Exception:
            pass

    # Columnas extendidas de auditoría e inferencia multimodal de IA (posiciones 13 en adelante)
    extra = list(row[13:]) if len(row) > 13 else []
    def get_extra(idx: int, default: Any = None) -> Any:
        return extra[idx] if len(extra) > idx and extra[idx] is not None else default

    criticidad_sugerida = get_extra(0)
    area_sugerida = get_extra(1)
    es_incidente_sugerido = bool(get_extra(2)) if get_extra(2) is not None else None
    confianza = float(get_extra(3)) if get_extra(3) is not None else None
    pasos_solucion = _ensure_list(get_extra(4))
    analisis_causa = get_extra(5)
    tiene_manual = bool(get_extra(6, False))
    manual_titulo = get_extra(7)
    manual_precauciones = get_extra(8)
    manual_checklist = _ensure_list(get_extra(9))
    manual_id = get_extra(10)
    visual_analysis = None

    if isinstance(sugerencia, dict):
        visual_analysis = sugerencia.get("visual_analysis")
        rag_sop = sugerencia.get("rag_sop") if isinstance(sugerencia.get("rag_sop"), dict) else {}
        criticidad_sugerida = criticidad_sugerida or sugerencia.get("criticidad_sugerida") or sugerencia.get("prioridad") or sugerencia.get("priority")
        area_sugerida = area_sugerida or sugerencia.get("area_sugerida") or sugerencia.get("categoria") or sugerencia.get("category")
        if es_incidente_sugerido is None:
            if "es_incidente_sugerido" in sugerencia:
                es_incidente_sugerido = bool(sugerencia["es_incidente_sugerido"])
            else:
                crit_u = (str(criticidad_sugerida) if criticidad_sugerida else "").upper()
                es_incidente_sugerido = bool(crit_u in ("CRÍTICA", "CRITICA", "ALTA") or sugerencia.get("es_incidente", True))
        if confianza is None:
            confianza = sugerencia.get("confianza") if sugerencia.get("confianza") is not None else sugerencia.get("confidence_score")
        if not pasos_solucion:
            if sugerencia.get("pasos_solucion"):
                pasos_solucion = _ensure_list(sugerencia["pasos_solucion"])
            elif isinstance(sugerencia.get("astar_route"), dict) and "steps" in sugerencia["astar_route"]:
                pasos_solucion = [
                    f"[{s.get('role', '')}] {s.get('title', '')}: {s.get('description', '')}".strip()
                    if s.get('role') and s.get('description') else s.get('title', '')
                    for s in sugerencia["astar_route"]["steps"]
                ]
            elif rag_sop.get("checklist"):
                pasos_solucion = _ensure_list(rag_sop["checklist"])
        if not analisis_causa:
            analisis_causa = sugerencia.get("analisis_causa") or sugerencia.get("recomendacion")
            if not analisis_causa and isinstance(sugerencia.get("classification"), dict):
                lex_str = ", ".join(sugerencia["classification"].get("lexical_evidence", []))
                analisis_causa = f"Clasificado en '{area_sugerida}' con severidad '{criticidad_sugerida}'. Activadores: {lex_str}."
        if not tiene_manual:
            tiene_manual = bool(sugerencia.get("tiene_manual") or sugerencia.get("runbook") or (rag_sop.get("similarity_score", 0) > 0))
        manual_titulo = manual_titulo or sugerencia.get("manual_titulo") or rag_sop.get("title")
        manual_precauciones = manual_precauciones or sugerencia.get("manual_precauciones") or rag_sop.get("precautions")
        if not manual_checklist:
            manual_checklist = _ensure_list(sugerencia.get("manual_checklist") or rag_sop.get("checklist", []))
        manual_id = manual_id or sugerencia.get("manual_id") or sugerencia.get("runbook") or rag_sop.get("runbook_id")

    return {
        "id": int(row[0]),
        "numero_ticket": str(row[1]),
        "titulo": str(row[2]),
        "descripcion": str(row[3]),
        "imagen_url": str(row[4]) if row[4] is not None else None,
        "criticidad": str(row[5]),
        "area_asignada": str(row[6]),
        "es_incidente": bool(row[7]),
        "estado": str(row[8]),
        "solucion_pasos": str(row[9]) if row[9] is not None else None,
        "sugerencia_ia": sugerencia,
        "criticidad_sugerida": str(criticidad_sugerida) if criticidad_sugerida else None,
        "area_sugerida": str(area_sugerida) if area_sugerida else None,
        "es_incidente_sugerido": bool(es_incidente_sugerido) if es_incidente_sugerido is not None else None,
        "confianza": float(confianza) if confianza is not None else None,
        "pasos_solucion": list(pasos_solucion) if pasos_solucion else [],
        "analisis_causa": str(analisis_causa) if analisis_causa else None,
        "tiene_manual": bool(tiene_manual) if tiene_manual is not None else False,
        "manual_titulo": str(manual_titulo) if manual_titulo else None,
        "manual_precauciones": str(manual_precauciones) if manual_precauciones else None,
        "manual_checklist": list(manual_checklist) if manual_checklist else [],
        "manual_id": str(manual_id) if manual_id else None,
        "visual_analysis": visual_analysis,
        "created_at": _to_iso(row[11]),
        "updated_at": _to_iso(row[12]),
    }


def _next_ticket_number(conn: Optional[UniversalDbConnection]) -> str:
    """Calcula el consecutivo del ticket con formato "TCK-YYYY-NNNNN" o saca un hash único si falla la secuencia."""
    year = datetime.datetime.now().strftime("%Y")
    if conn:
        try:
            res = conn.run("SELECT COALESCE(MAX(id), 0) + 1 FROM servicedesk.tickets_usuario;")
            if res and res[0] and res[0][0] is not None:
                seq = int(res[0][0])
                num_str = f"TCK-{year}-{seq:05d}"
                chk = conn.run("SELECT 1 FROM servicedesk.tickets_usuario WHERE numero_ticket = :num LIMIT 1;", {"num": num_str})
                if not chk:
                    return num_str
        except Exception:
            pass
    rand_code = uuid.uuid4().hex[:6].upper()
    return f"TCK-{year}-{rand_code}"


def init_tickets_usuario_table() -> bool:
    """Crea el esquema "servicedesk", la tabla "tickets_usuario" con sus índices y mete datos semilla si está vacía."""
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        conn.run("CREATE SCHEMA IF NOT EXISTS servicedesk;")
        create_table_ddl = """
        CREATE TABLE IF NOT EXISTS servicedesk.tickets_usuario (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            numero_ticket VARCHAR(50) NOT NULL UNIQUE,
            titulo VARCHAR(255) NOT NULL,
            descripcion TEXT NOT NULL,
            imagen_url VARCHAR(500) NULL,
            criticidad VARCHAR(50) NOT NULL DEFAULT 'Media' CONSTRAINT chk_tickets_usuario_criticidad CHECK (criticidad IN ('Baja', 'Media', 'Alta', 'Crítica')),
            area_asignada VARCHAR(100) NOT NULL DEFAULT 'Soporte TI' CONSTRAINT chk_tickets_usuario_area CHECK (area_asignada IN ('Soporte TI', 'Hardware', 'Software', 'Redes', 'Accesos', 'Base de Datos', 'Seguridad')),
            es_incidente BOOLEAN NOT NULL DEFAULT TRUE,
            estado VARCHAR(50) NOT NULL DEFAULT 'Abierto' CONSTRAINT chk_tickets_usuario_estado CHECK (estado IN ('Abierto', 'En Proceso', 'Resuelto')),
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
        """
        conn.run(create_table_ddl)
        conn.run("CREATE INDEX IF NOT EXISTS idx_tickets_usuario_created_at ON servicedesk.tickets_usuario (created_at DESC);")
        conn.run("CREATE INDEX IF NOT EXISTS idx_tickets_usuario_keyset ON servicedesk.tickets_usuario (created_at DESC, id DESC);")
        conn.run("CREATE INDEX IF NOT EXISTS idx_tickets_usuario_estado ON servicedesk.tickets_usuario (estado);")
        conn.run("CREATE INDEX IF NOT EXISTS idx_tickets_usuario_numero_ticket ON servicedesk.tickets_usuario (numero_ticket);")

        cnt_rows = conn.run("SELECT COUNT(*) FROM servicedesk.tickets_usuario;")
        cnt = cnt_rows[0][0] if cnt_rows and cnt_rows[0] else 0

        if cnt == 0:
            insert_sql = """
            INSERT INTO servicedesk.tickets_usuario (
                numero_ticket, titulo, descripcion, imagen_url, criticidad, area_asignada, 
                es_incidente, estado, solucion_pasos, sugerencia_ia
            ) VALUES (
                :num, :tit, :des, :img, :cri, :area, :inc, :est, :sol, :sug::jsonb
            );
            """
            for s in _FALLBACK_TICKETS:
                conn.run(insert_sql, {
                    "num": s["numero_ticket"],
                    "tit": s["titulo"],
                    "des": s["descripcion"],
                    "img": s["imagen_url"],
                    "cri": s["criticidad"],
                    "area": s["area_asignada"],
                    "inc": s["es_incidente"],
                    "est": s["estado"],
                    "sol": s["solucion_pasos"],
                    "sug": json.dumps(s["sugerencia_ia"]) if s["sugerencia_ia"] else None,
                })
        return True
    except Exception as exc:
        print(f"Error inicializando servicedesk.tickets_usuario: {exc}")
        return False
    finally:
        conn.close()


def create_ticket_usuario(
    titulo: str,
    descripcion: str,
    imagen_url: Optional[str] = None,
    sugerencia_ia: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Registra un ticket nuevo en "PostgreSQL 18" o en la lista de contingencia si la base no responde."""
    clean_titulo = str(titulo).strip()
    clean_desc = str(descripcion).strip()
    clean_img = str(imagen_url).strip() if imagen_url and str(imagen_url).strip() else None

    conn = get_db_connection()
    if conn is not None:
        try:
            numero_ticket = _next_ticket_number(conn)
            sql = """
            INSERT INTO servicedesk.tickets_usuario (
                numero_ticket, titulo, descripcion, imagen_url,
                criticidad, area_asignada, es_incidente, estado, solucion_pasos, sugerencia_ia
            ) VALUES (
                :num, :tit, :des, :img,
                'Media', 'Soporte TI', TRUE, 'Abierto', NULL, :sug::jsonb
            )
            RETURNING id, numero_ticket, titulo, descripcion, imagen_url, criticidad, area_asignada, 
                      es_incidente, estado, solucion_pasos, sugerencia_ia, created_at, updated_at;
            """
            sug_json = json.dumps(sugerencia_ia, default=_json_serial_default) if sugerencia_ia else None
            rows = conn.run(sql, {
                "num": numero_ticket,
                "tit": clean_titulo,
                "des": clean_desc,
                "img": clean_img,
                "sug": sug_json,
            })
            if rows and len(rows) > 0:
                return _row_to_ticket_dict(rows[0])
        except Exception as exc:
            print(f"Error creando ticket en PostgreSQL: {exc}")
        finally:
            conn.close()

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    new_id = (max((t["id"] for t in _FALLBACK_TICKETS), default=0) + 1)
    fallback_num = f"TCK-{datetime.datetime.now().strftime('%Y')}-{new_id:05d}"
    fb_ticket: Dict[str, Any] = {
        "id": new_id,
        "numero_ticket": fallback_num,
        "titulo": clean_titulo,
        "descripcion": clean_desc,
        "imagen_url": clean_img,
        "criticidad": "Media",
        "area_asignada": "Soporte TI",
        "es_incidente": True,
        "estado": "Abierto",
        "solucion_pasos": None,
        "sugerencia_ia": dict(sugerencia_ia) if sugerencia_ia else None,
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    if sugerencia_ia and isinstance(sugerencia_ia, dict):
        for k, v in sugerencia_ia.items():
            if k not in fb_ticket:
                fb_ticket[k] = v
        if "visual_analysis" in sugerencia_ia:
            fb_ticket["visual_analysis"] = sugerencia_ia["visual_analysis"]
        if "priority" in sugerencia_ia and not fb_ticket.get("criticidad_sugerida"):
            fb_ticket["criticidad_sugerida"] = sugerencia_ia["priority"]
        if "category" in sugerencia_ia and not fb_ticket.get("area_sugerida"):
            fb_ticket["area_sugerida"] = sugerencia_ia["category"]
        if "confidence_score" in sugerencia_ia and not fb_ticket.get("confianza"):
            fb_ticket["confianza"] = float(sugerencia_ia["confidence_score"])
    _FALLBACK_TICKETS.insert(0, fb_ticket)
    return dict(fb_ticket)


def get_tickets_usuario_list() -> List[Dict[str, Any]]:
    """Trae todos los tickets ordenados por fecha de creación descendente."""
    conn = get_db_connection()
    if conn is not None:
        try:
            sql = """
            SELECT id, numero_ticket, titulo, descripcion, imagen_url, criticidad, area_asignada, 
               es_incidente, estado, solucion_pasos, sugerencia_ia, created_at, updated_at
            FROM servicedesk.tickets_usuario
            ORDER BY created_at DESC, id DESC;
            """
            rows = conn.run(sql)
            if rows is not None:
                return [_row_to_ticket_dict(r) for r in rows]
        except Exception as exc:
            print(f"Error obteniendo lista de tickets en PostgreSQL: {exc}")
        finally:
            conn.close()

    return sorted(_FALLBACK_TICKETS, key=lambda x: x.get("created_at", ""), reverse=True)


def get_ticket_usuario_by_id(ticket_id: int | str) -> Optional[Dict[str, Any]]:
    """Busca un ticket por su ID numérico o por su código "numero_ticket"."""
    conn = get_db_connection()
    if conn is not None:
        try:
            params: Dict[str, Any] = {}
            if isinstance(ticket_id, int) or (isinstance(ticket_id, str) and ticket_id.isdigit()):
                where_clause = "id = :tid"
                params["tid"] = int(ticket_id)
            else:
                where_clause = "numero_ticket = :tnum"
                params["tnum"] = str(ticket_id).strip()

            sql = f"""
            SELECT id, numero_ticket, titulo, descripcion, imagen_url, criticidad, area_asignada, 
                   es_incidente, estado, solucion_pasos, sugerencia_ia, created_at, updated_at
            FROM servicedesk.tickets_usuario
            WHERE {where_clause}
            LIMIT 1;
            """
            rows = conn.run(sql, params)
            if rows and len(rows) > 0:
                return _row_to_ticket_dict(rows[0])
            return None
        except Exception as exc:
            print(f"Error consultando ticket {ticket_id} en PostgreSQL: {exc}")
            return None
        finally:
            conn.close()

    for t in _FALLBACK_TICKETS:
        if (str(t["id"]) == str(ticket_id)) or (str(t.get("numero_ticket", "")).strip().upper() == str(ticket_id).strip().upper()):
            return dict(t)
    return None


def update_ticket_usuario(
    ticket_id: int | str,
    titulo: Optional[str] = None,
    descripcion: Optional[str] = None,
    imagen_url: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Actualiza los datos editables por el usuario final (título, descripción o imagen adjunta)."""
    conn = get_db_connection()
    if conn is not None:
        try:
            set_parts = ["updated_at = CURRENT_TIMESTAMP"]
            params: Dict[str, Any] = {}

            if titulo is not None:
                set_parts.append("titulo = :tit")
                params["tit"] = str(titulo).strip()
            if descripcion is not None:
                set_parts.append("descripcion = :des")
                params["des"] = str(descripcion).strip()
            if imagen_url is not None:
                clean_img = str(imagen_url).strip() if imagen_url and str(imagen_url).strip() else None
                set_parts.append("imagen_url = :img")
                params["img"] = clean_img

            if isinstance(ticket_id, int) or (isinstance(ticket_id, str) and ticket_id.isdigit()):
                where_clause = "id = :tid"
                params["tid"] = int(ticket_id)
            else:
                where_clause = "numero_ticket = :tnum"
                params["tnum"] = str(ticket_id).strip()

            update_sql = f"""
            UPDATE servicedesk.tickets_usuario
            SET {", ".join(set_parts)}
            WHERE {where_clause}
            RETURNING id, numero_ticket, titulo, descripcion, imagen_url, criticidad, area_asignada, 
                      es_incidente, estado, solucion_pasos, sugerencia_ia, created_at, updated_at;
            """
            rows = conn.run(update_sql, params)
            if rows and len(rows) > 0:
                return _row_to_ticket_dict(rows[0])
            return None
        except Exception as exc:
            print(f"Error actualizando ticket de usuario en PostgreSQL: {exc}")
            return None
        finally:
            conn.close()

    target = None
    for t in _FALLBACK_TICKETS:
        if (str(t["id"]) == str(ticket_id)) or (str(t.get("numero_ticket", "")).strip().upper() == str(ticket_id).strip().upper()):
            target = t
            break
    if target is None:
        return None
    if titulo is not None:
        target["titulo"] = str(titulo).strip()
    if descripcion is not None:
        target["descripcion"] = str(descripcion).strip()
    if imagen_url is not None:
        target["imagen_url"] = str(imagen_url).strip() if imagen_url and str(imagen_url).strip() else None
    target["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return dict(target)


def update_ticket_tecnico(
    ticket_id: int | str,
    solucion_pasos: Optional[str] = None,
    criticidad: Optional[str] = None,
    area_asignada: Optional[str] = None,
    es_incidente: Optional[bool] = None,
    estado: Optional[str] = None,
    sugerencia_ia: Optional[dict] = None,
) -> Optional[Dict[str, Any]]:
    """Actualiza la gestión técnica del ticket (solución, criticidad, área, estado y payload de IA)."""
    valid_criticidades = {"Baja", "Media", "Alta", "Crítica"}
    valid_areas = {"Soporte TI", "Hardware", "Software", "Redes", "Accesos", "Base de Datos", "Seguridad"}
    valid_estados = {"Abierto", "En Proceso", "Resuelto"}

    clean_criticidad = None
    if criticidad is not None:
        c = criticidad.strip().capitalize()
        if c.lower() in ("critica", "crítica"):
            c = "Crítica"
        for vc in valid_criticidades:
            if c.lower() == vc.lower():
                clean_criticidad = vc
                break
        if clean_criticidad is None:
            clean_criticidad = "Media"

    clean_area = None
    if area_asignada is not None:
        ca = area_asignada.strip()
        for va in valid_areas:
            if ca.lower() == va.lower():
                clean_area = va
                break
        if clean_area is None:
            clean_area = "Soporte TI"

    clean_estado = None
    if estado is not None:
        ce = estado.strip()
        for ve in valid_estados:
            if ce.lower() == ve.lower():
                clean_estado = ve
                break
        if clean_estado is None:
            clean_estado = "Abierto"

    conn = get_db_connection()
    if conn is not None:
        try:
            set_parts = ["updated_at = CURRENT_TIMESTAMP"]
            params: Dict[str, Any] = {}

            if solucion_pasos is not None:
                set_parts.append("solucion_pasos = :sol")
                params["sol"] = str(solucion_pasos).strip()
            if clean_criticidad is not None:
                set_parts.append("criticidad = :cri")
                params["cri"] = clean_criticidad
            if clean_area is not None:
                set_parts.append("area_asignada = :area")
                params["area"] = clean_area
            if es_incidente is not None:
                set_parts.append("es_incidente = :inc")
                params["inc"] = bool(es_incidente)
            if clean_estado is not None:
                set_parts.append("estado = :est")
                params["est"] = clean_estado
            if sugerencia_ia is not None:
                set_parts.append("sugerencia_ia = :sug::jsonb")
                params["sug"] = json.dumps(sugerencia_ia, default=_json_serial_default)
                if "criticidad_sugerida" in sugerencia_ia and sugerencia_ia["criticidad_sugerida"]:
                    set_parts.append("criticidad_sugerida = :cri_sug")
                    params["cri_sug"] = str(sugerencia_ia["criticidad_sugerida"])
                if "area_sugerida" in sugerencia_ia and sugerencia_ia["area_sugerida"]:
                    set_parts.append("area_sugerida = :area_sug")
                    params["area_sug"] = str(sugerencia_ia["area_sugerida"])
                if "es_incidente_sugerido" in sugerencia_ia and sugerencia_ia["es_incidente_sugerido"] is not None:
                    set_parts.append("es_incidente_sugerido = :inc_sug")
                    params["inc_sug"] = bool(sugerencia_ia["es_incidente_sugerido"])
                if "confianza" in sugerencia_ia and sugerencia_ia["confianza"] is not None:
                    set_parts.append("confianza = :conf")
                    params["conf"] = float(sugerencia_ia["confianza"])
                if "pasos_solucion" in sugerencia_ia and sugerencia_ia["pasos_solucion"] is not None:
                    set_parts.append("pasos_solucion = :pasos::jsonb")
                    params["pasos"] = json.dumps(sugerencia_ia["pasos_solucion"], default=_json_serial_default)
                if "analisis_causa" in sugerencia_ia and sugerencia_ia["analisis_causa"]:
                    set_parts.append("analisis_causa = :causa")
                    params["causa"] = str(sugerencia_ia["analisis_causa"])
                if "tiene_manual" in sugerencia_ia and sugerencia_ia["tiene_manual"] is not None:
                    set_parts.append("tiene_manual = :tieneman")
                    params["tieneman"] = bool(sugerencia_ia["tiene_manual"])
                if "manual_titulo" in sugerencia_ia and sugerencia_ia["manual_titulo"]:
                    set_parts.append("manual_titulo = :mantit")
                    params["mantit"] = str(sugerencia_ia["manual_titulo"])
                if "manual_precauciones" in sugerencia_ia and sugerencia_ia["manual_precauciones"]:
                    set_parts.append("manual_precauciones = :manprec")
                    params["manprec"] = str(sugerencia_ia["manual_precauciones"])
                if "manual_checklist" in sugerencia_ia and sugerencia_ia["manual_checklist"] is not None:
                    set_parts.append("manual_checklist = :mancheck::jsonb")
                    params["mancheck"] = json.dumps(sugerencia_ia["manual_checklist"], default=_json_serial_default)
                if "manual_id" in sugerencia_ia and sugerencia_ia["manual_id"]:
                    set_parts.append("manual_id = :manid")
                    params["manid"] = str(sugerencia_ia["manual_id"])

            if isinstance(ticket_id, int) or (isinstance(ticket_id, str) and ticket_id.isdigit()):
                where_clause = "id = :tid"
                params["tid"] = int(ticket_id)
            else:
                where_clause = "numero_ticket = :tnum"
                params["tnum"] = str(ticket_id).strip()

            update_sql = f"""
            UPDATE servicedesk.tickets_usuario
            SET {", ".join(set_parts)}
            WHERE {where_clause}
            RETURNING id, numero_ticket, titulo, descripcion, imagen_url, criticidad, area_asignada, 
                      es_incidente, estado, solucion_pasos, sugerencia_ia, created_at, updated_at,
                      criticidad_sugerida, area_sugerida, es_incidente_sugerido, confianza, pasos_solucion,
                      analisis_causa, tiene_manual, manual_titulo, manual_precauciones, manual_checklist, manual_id;
            """
            rows = conn.run(update_sql, params)
            if rows and len(rows) > 0:
                return _row_to_ticket_dict(rows[0])
            return None
        except Exception as exc:
            print(f"Error actualizando ticket técnico en PostgreSQL: {exc}")
            return None
        finally:
            conn.close()

    target = None
    for t in _FALLBACK_TICKETS:
        if (str(t["id"]) == str(ticket_id)) or (str(t.get("numero_ticket", "")).strip().upper() == str(ticket_id).strip().upper()):
            target = t
            break
    if target is None:
        return None
    if solucion_pasos is not None:
        target["solucion_pasos"] = str(solucion_pasos).strip()
    if clean_criticidad is not None:
        target["criticidad"] = clean_criticidad
    if clean_area is not None:
        target["area_asignada"] = clean_area
    if es_incidente is not None:
        target["es_incidente"] = bool(es_incidente)
    if clean_estado is not None:
        target["estado"] = clean_estado
    if sugerencia_ia is not None:
        target["sugerencia_ia"] = dict(sugerencia_ia)
        for k, v in sugerencia_ia.items():
            target[k] = v
    target["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return dict(target)


# Aliases para mantener compatibilidad con el resto del backend
get_ticket_usuario = get_ticket_usuario_by_id
list_tickets_usuario = get_tickets_usuario_list


def save_guia_ia_ticket_usuario(
    ticket_id: int | str, guia: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Guarda la recomendación generada por la IA en el ticket correspondiente."""
    return update_ticket_tecnico(ticket_id=ticket_id, sugerencia_ia=guia)


