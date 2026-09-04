from __future__ import annotations

from pathlib import Path
from pprint import pprint

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import make_pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
KB_PATH = DATA_DIR / "base_conocimiento.txt"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORT_PATH = REPORTS_DIR / "semana05.md"

DEFAULT_DOCS = [
    "Para un equipo caliente con ventilador ruidoso o alarma de temperatura, limpiar disipadores, verificar pasta termica y revisar flujo de ventilacion.",
    "En caidas de red, internet o fallas de resolucion DNS, verificar cable ethernet, renovar IP con ipconfig /renew y probar ping al gateway o servidor DNS.",
    "Para cuentas bloqueadas o problemas de inicio de sesion, verificar intentos fallidos en Active Directory, desbloquear usuario y restablecer credenciales temporales.",
    "Si el token o codigo MFA no llega al dispositivo movil, validar sincronizacion horaria de Microsoft Authenticator o generar codigo de paso temporal de contingencia.",
    "Cuando una aplicacion como Excel o el ERP se cierra con error inesperado o memoria violada, revisar complementos conflictivos, actualizar version y consultar visor de eventos.",
    "Para impresoras con atascos frecuentes de papel o impresion manchada, retirar residuos del rodillo de alimentacion, revisar nivel de toner y reiniciar cola de impresion.",
    "Si el monitor parpadea, no enciende o emite pantalla negra, verificar cables HDMI o DisplayPort, actualizar controlador de video y probar conexion directa sin dock.",
    "Ante lentitud extrema del sistema operativo o congelamiento, inspeccionar consumo de CPU, memoria y disco en el administrador de tareas y deshabilitar servicios innecesarios.",
    "Si el cliente VPN falla al negociar el tunel o se desconecta intermitentemente, validar certificado digital de seguridad, probar protocolo alternativo y verificar enlace del proveedor.",
    "Para errores de acceso denegado en recursos compartidos de red, verificar membresia en grupos de seguridad NTFS y corroborar la ruta de red SMB asignada.",
]


def load_documents() -> list[str]:
    """Carga los documentos de la base de conocimiento y valida la cantidad mínima."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not KB_PATH.exists():
        KB_PATH.write_text("\n".join(DEFAULT_DOCS), encoding="utf-8")
    docs = [
        line.strip()
        for line in KB_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(docs) < 8:
        raise ValueError(
            "data/base_conocimiento.txt debe contener al menos 8 entradas."
        )
    return docs


RULES = [
    (
        lambda q: "temperatura" in q or "caliente" in q or "ventilador" in q,
        "revisar_ventilacion",
    ),
    (
        lambda q: "red" in q
        or "internet" in q
        or "dns" in q
        or "enlace" in q
        or "vpn" in q,
        "revisar_conectividad",
    ),
    (
        lambda q: "sesion" in q
        or "cuenta" in q
        or "bloquead" in q
        or "contrasena" in q
        or "mfa" in q,
        "revisar_acceso",
    ),
    (
        lambda q: "excel" in q
        or "word" in q
        or "office" in q
        or "powerpoint" in q
        or "ofimatica" in q
        or "teams" in q
        or "outlook" in q
        or "erp" in q
        or "cierra" in q
        or "software" in q
        or "aplicacion" in q
        or "programa" in q,
        "revisar_software",
    ),
    (
        lambda q: "impresora" in q
        or "imprimir" in q
        or "toner" in q
        or "papel" in q,
        "revisar_impresion",
    ),
    (
        lambda q: "pantalla" in q
        or "monitor" in q
        or "video" in q
        or "parpadea" in q,
        "revisar_pantalla",
    ),
]

# 3. Ejemplos de entrenamiento etiquetados (20 ejemplos adaptados al soporte TI)
TRAIN_X = [
    # Hardware
    "el equipo esta muy caliente y el ventilador hace ruido",
    "el monitor parpadea y la pantalla no da video",
    "la impresora atasca el papel y mancha las hojas de impresion",
    "el computador se apago por sobrecalentamiento y no enciende",
    "el teclado y el mouse no responden en los puertos usb",
    # Software
    "excel se cierra inesperadamente al ejecutar una macro",
    "la aplicacion erp arroja error de memoria violada",
    "el sistema contable se congela al emitir las facturas",
    "el navegador muestra un error critico al cargar la plataforma",
    "el software de facturacion se bloqueo antes del cierre diario",
    # Red
    "internet se cae y aparece un fallo en el servidor dns",
    "la conexion vpn se desconecta constantemente al trabajar remoto",
    "perdida masiva de paquetes y lentitud en la red de la oficina",
    "el switch central no asigna direccion ip por dhcp",
    "caida del enlace de fibra optica dejando sin red a la sede",
    # Accesos
    "no puedo iniciar sesion porque mi cuenta de dominio esta bloqueada",
    "olvide mi contrasena de active directory y no puedo ingresar",
    "no llega el codigo del token mfa a mi telefono movil",
    "error de acceso denegado en la carpeta compartida de red",
    "el usuario no tiene permisos suficientes para entrar al aplicativo",
]

TRAIN_Y = [
    "hardware",
    "hardware",
    "hardware",
    "hardware",
    "hardware",
    "software",
    "software",
    "software",
    "software",
    "software",
    "red",
    "red",
    "red",
    "red",
    "red",
    "accesos",
    "accesos",
    "accesos",
    "accesos",
    "accesos",
]

# Consultas de prueba representativas del proyecto de soporte
TEST_QUERIES = [
    "El equipo esta muy caliente y el ventilador hace ruido",
    "Internet se cae y aparece error de conexion DNS",
    "No puedo iniciar sesion con mi cuenta de usuario bloqueada",
    "Excel se cierra de golpe con un error de memoria en la aplicacion",
]


SPANISH_STOP_WORDS = [
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un",
    "para", "con", "no", "una", "su", "al", "lo", "como", "mas", "pero", "sus", "le",
    "ya", "o", "este", "si", "porque", "esta", "entre", "cuando", "muy", "sin", "sobre",
    "tambien", "me", "hasta", "hay", "donde", "quien", "desde", "todo", "nos", "durante",
    "todos", "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante", "ellos", "e",
    "esto", "mi", "antes", "algunos", "unos", "yo", "otro", "otras", "otra", "tanto",
    "esa", "estos", "mucho", "quienes", "nada", "muchos", "cual", "sea", "poco", "ella",
    "estas", "estaba", "estamos", "algunas", "algo", "nosotros",
]

DOCS = load_documents()
vectorizer = TfidfVectorizer(stop_words=SPANISH_STOP_WORDS)
doc_matrix = vectorizer.fit_transform(DOCS)

classifier = make_pipeline(
    TfidfVectorizer(),
    LogisticRegression(max_iter=1000, random_state=42),
)
classifier.fit(TRAIN_X, TRAIN_Y)


def answer(query: str) -> dict:
    """Procesa una consulta con trazabilidad completa (reglas, evidencia, similitud, clase)."""
    q = query.lower()
    fired = [name for condition, name in RULES if condition(q)]
    similarities = cosine_similarity(
        vectorizer.transform([q]),
        doc_matrix,
    )[0]
    best_index = int(similarities.argmax())
    label = str(classifier.predict([q])[0])
    return {
        "reglas": fired,
        "evidencia": DOCS[best_index],
        "similitud": float(similarities[best_index]),
        "clase": label,
    }


def write_report(rows: list[tuple[str, dict]]) -> None:
    """Genera el reporte Markdown reproducible en reports/semana05.md."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Semana 05: Sistema híbrido de soporte TI con trazabilidad",
        "",
        "## 1. Arquitectura y conceptos trabajados",
        "",
        "Este módulo implementa un **sistema híbrido explicable** aplicado al Asistente de soporte TI, articulando los cinco conceptos de la Semana 05:",
        "",
        "1. **Sistemas expertos:** Reglas deterministas ejecutadas con funciones condicionales para acciones inmediatas.",
        "2. **Ingeniería del conocimiento:** Base de conocimiento formalizada en `data/base_conocimiento.txt` con procedimientos técnicos validados.",
        "3. **Recuperación de información:** Vectorización TF-IDF y similitud coseno para recuperar el artículo de soporte más relevante ante una consulta.",
        "4. **Reconocimiento de formas / Clasificación supervisada:** Pipeline de aprendizaje que clasifica el requerimiento en el dominio correspondiente (`hardware`, `software`, `red`, `accesos`).",
        "5. **Tratamiento del lenguaje natural (PLN):** Normalización léxica y extracción de señales semánticas para una interacción explicable.",
        "",
        "---",
        "",
        "## 2. Evidencia de ejecución de consultas de prueba",
        "",
    ]

    for i, (query, result) in enumerate(rows, start=1):
        reglas_str = ", ".join(result["reglas"]) if result["reglas"] else "ninguna"
        lines += [
            f"### Consulta {i}",
            f"- **Entrada:** `{query}`",
            f"- **Regla(s) activada(s):** `{reglas_str}`",
            f"- **Evidencia recuperada:** \"{result['evidencia']}\"",
            f"- **Similitud coseno:** `{result['similitud']:.3f}`",
            f"- **Clase predicha:** `{result['clase']}`",
            "",
            "> **Trazabilidad:**",
            f"> - *Por qué se activó la regla:* La consulta contiene activadores semánticos vinculados a `{reglas_str}`.",
            f"> - *Por qué se recuperó la evidencia:* El cálculo TF-IDF arrojó una similitud de `{result['similitud']:.3f}` frente al documento más afín en la base de conocimiento.",
            f"> - *Por qué se clasificó como `{result['clase']}`:* El modelo supervisado asoció el patrón de términos al perfil de `{result['clase']}`.",
            "",
        ]

    lines += [
        "---",
        "",
        "## 3. Matriz comparativa de trazabilidad",
        "",
        "| Consulta | Regla disparada | Similitud | Clase predicha | Procedimiento recuperado |",
        "|---|---|---:|:---:|---|",
    ]

    for query, result in rows:
        regla = ", ".join(result["reglas"]) if result["reglas"] else "ninguna"
        resumen_ev = result["evidencia"][:55] + "..."
        lines.append(
            f"| {query} | `{regla}` | {result['similitud']:.3f} | `{result['clase']}` | {resumen_ev} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 4. Discusión, ventajas y limitaciones",
        "",
        "### Ventajas del enfoque híbrido",
        "- **Trazabilidad y auditoría:** No se limita a entregar una predicción opaca; detalla la regla activada, el sustento documental recuperado y el grado numérico de coincidencia.",
        "- **Robustez operativa:** Si el clasificador estadístico tiene baja certidumbre o una regla no se activa, la recuperación por similitud coseno garantiza un procedimiento de contingencia.",
        "",
        "### Limitaciones actuales",
        "- Las reglas condicionales dependen de coincidencias literales de subcadenas (`in q`) y no reconocen negaciones complejas.",
        "- La base de conocimiento actual contiene 10 artículos; en producción se conectará a un repositorio dinámico de gestión de incidentes.",
        "",
        "---",
        "",
        "## 5. Reproducción",
        "",
        "```bash",
        "python src/semana05_sistema_hibrido.py",
        "```",
        "",
    ]

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> list[tuple[str, dict]]:
    """Ejecuta las consultas de prueba y muestra los resultados en consola."""
    results = []
    for query in TEST_QUERIES:
        res = answer(query)
        results.append((query, res))
        print(query)
        pprint(res, sort_dicts=False)
        print()

    return results


if __name__ == "__main__":
    main()
