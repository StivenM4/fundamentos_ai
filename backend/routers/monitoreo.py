from __future__ import annotations

import logging
import random
from typing import Any, Dict, List, Optional
import numpy as np
from fastapi import APIRouter, HTTPException, status

from backend.database import create_ticket_usuario, update_ticket_tecnico
from backend.schemas import (
    EquipoEjemploItem,
    MonitoreoBaselineResponse,
    MonitoreoRequest,
    MonitoreoResponse,
)
from src.semana07_representaciones import (
    BASELINE_REFERENCIA,
    DESCRIPCION_METRICAS,
    METRICAS_DOMINIO,
    REGLAS_DIAGNOSTICO,
    UMBRAL_CARGA_ALTA,
    UMBRAL_DISTANCIA_ALERTA,
    UMBRAL_ERRORES_PRESENTES,
    UMBRAL_TEMPERATURA_ALTA,
    accepts_01,
    calcular_distancia_telemetria,
    discretizar_telemetria,
    evaluar_reglas_simbolicas,
    evaluar_salud_equipo,
    generar_ticket_soporte,
)

logger = logging.getLogger("servicedesk.monitoreo")

router = APIRouter(
    prefix="/api/monitoreo",
    tags=["Monitoreo - Semana 07"],
)


@router.post(
    "/evaluar",
    response_model=MonitoreoResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluar telemetría de equipo con reconocimiento multimodal de IA",
    description=(
        "Evalúa la salud de un equipo computacional combinando distancia SLA numérica, "
        "inferencia lógica basada en reglas y verificación de secuencia temporal mediante autómata finito determinista (DFA)."
    ),
)
async def evaluar_telemetria_endpoint(request: MonitoreoRequest) -> MonitoreoResponse:
    """Procesa la telemetría del equipo (temperatura, carga y tasa de errores) y dispara ticket en BD si detecta anomalías."""
    try:
        sample = np.array(
            [
                float(request.temperatura_cpu_c),
                float(request.carga_servidor_pct),
                float(request.tasa_errores_min),
            ],
            dtype=float,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Métricas de telemetría inválidas: {exc}",
        )

    # 1. Cálculo de distancia euclidiana frente al vector baseline de SLA
    try:
        distancia = calcular_distancia_telemetria(sample, BASELINE_REFERENCIA)
        distancia_sla = round(float(distancia), 3)
        distancia_alerta = bool(distancia > UMBRAL_DISTANCIA_ALERTA)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el cálculo de distancia euclidiana: {exc}",
        )

    # 2. Inferencia lógica: discretizamos métricas y disparamos reglas simbólicas
    hechos_set = discretizar_telemetria(sample)
    hechos_simbolicos = sorted(list(hechos_set))
    diagnosticos_simbolicos = evaluar_reglas_simbolicas(hechos_set)

    # 3. Análisis sintáctico: autómata DFA evaluando si la secuencia de logs termina en "01"
    secuencia_limpia = request.secuencia_eventos.strip() if request.secuencia_eventos else "0000"
    alerta_automata_01 = bool(accepts_01(secuencia_limpia))

    # 4. Diagnóstico integral: el equipo se marca no saludable si falla cualquier capa
    no_esta_sano = (
        distancia_alerta
        or len(diagnosticos_simbolicos) > 0
        or alerta_automata_01
    )
    esta_sano = not no_esta_sano

    # 5. Si el equipo presenta fallas y se solicitó alerta, abrimos el ticket en base de datos
    ticket_generado: Optional[Dict[str, Any]] = None

    if not esta_sano and request.crear_ticket_si_falla:
        ticket = generar_ticket_soporte(
            equipo_id=request.equipo_id,
            telemetria=sample,
            distancia=distancia,
            diagnosticos=diagnosticos_simbolicos,
            alerta_automata=alerta_automata_01,
            secuencia_logs=secuencia_limpia,
        )

        # Armamos el reporte detallado para que el técnico L2 tenga todo el contexto del incidente
        titulo = f"[Alerta Monitoreo S07] Falla detectada en {request.equipo_id}"
        diag_str = ", ".join(diagnosticos_simbolicos) if diagnosticos_simbolicos else "Desvío numérico de métricas SLA"
        automata_str = (
            f"Detectada anomalía crítica terminada en '01' (secuencia '{secuencia_limpia}')"
            if alerta_automata_01
            else "Secuencia normal (sin patrón de falla DFA)"
        )

        descripcion = (
            f"Alerta automática generada por el módulo de Monitoreo TI (Semana 07: Reconocimiento en IA).\n\n"
            f"Equipo Monitoreado: {request.equipo_id}\n\n"
            f"Telemetría Registrada:\n"
            f"- Temperatura CPU: {request.temperatura_cpu_c:.1f} °C\n"
            f"- Carga Servidor / RAM: {request.carga_servidor_pct * 100:.1f}%\n"
            f"- Tasa de Errores: {request.tasa_errores_min:.1f} err/min\n\n"
            f"Diagnóstico del Motor de Reconocimiento:\n"
            f"- Distancia SLA: {distancia_sla} (Umbral de alerta: {UMBRAL_DISTANCIA_ALERTA})\n"
            f"- Hechos simbólicos activados: {', '.join(hechos_simbolicos) if hechos_simbolicos else 'Ninguno'}\n"
            f"- Conclusiones lógicas inferidas: {diag_str}\n"
            f"- Verificación Autómata DFA: {automata_str}\n\n"
            f"Acción Operativa Recomendada:\n"
            f"{ticket.get('accion_recomendada', 'Inspección preventiva de rutina por desvío de métricas SLA.')}"
        )

        try:
            db_ticket = create_ticket_usuario(
                titulo=titulo,
                descripcion=descripcion,
                imagen_url=None,
            )
            if db_ticket:
                ticket_id_db = db_ticket.get("id")
                numero_ticket_db = db_ticket.get("numero_ticket")
                ticket["ticket_id_db"] = ticket_id_db
                ticket["numero_ticket_db"] = numero_ticket_db

                # Actualizamos el ticket con la categoría, severidad y pasos de contingencia
                try:
                    cat_map = {
                        "hardware": "Hardware",
                        "software": "Software",
                    }
                    prio_map = {
                        "alta": "Alta",
                        "media": "Media",
                        "baja": "Baja",
                        "critica": "Crítica",
                    }
                    mapped_prio = prio_map.get(str(ticket.get("prioridad", "")).lower(), "Alta")
                    mapped_area = cat_map.get(str(ticket.get("categoria", "")).lower(), "Hardware")

                    update_ticket_tecnico(
                        ticket_id=ticket_id_db,
                        solucion_pasos=ticket.get("accion_recomendada"),
                        criticidad=mapped_prio,
                        area_asignada=mapped_area,
                        es_incidente=True,
                        estado="Abierto",
                        sugerencia_ia=ticket,
                    )
                except Exception as meta_exc:
                    logger.warning("No se pudo actualizar metadata técnica del ticket: %s", meta_exc)
        except Exception as exc:
            logger.error("Error persistiendo ticket de soporte para equipo %s: %s", request.equipo_id, exc)

        ticket_generado = ticket

    telemetria_salida = {
        "temperatura_cpu_c": float(request.temperatura_cpu_c),
        "carga_servidor_pct": float(request.carga_servidor_pct),
        "tasa_errores_min": float(request.tasa_errores_min),
    }

    return MonitoreoResponse(
        equipo_id=request.equipo_id,
        telemetria=telemetria_salida,
        distancia_sla=distancia_sla,
        umbral_distancia_alerta=float(UMBRAL_DISTANCIA_ALERTA),
        distancia_alerta=distancia_alerta,
        hechos_simbolicos=hechos_simbolicos,
        diagnosticos_simbolicos=diagnosticos_simbolicos,
        alerta_automata_01=alerta_automata_01,
        secuencia_analizada=secuencia_limpia,
        esta_sano=esta_sano,
        ticket_generado=ticket_generado,
    )


@router.get(
    "/baseline",
    response_model=MonitoreoBaselineResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener configuración de referencia, umbrales y reglas simbólicas",
    description="Retorna el vector baseline de SLA, los umbrales numéricos de discretización y la base de reglas lógicas.",
)
def get_monitoreo_baseline_endpoint() -> MonitoreoBaselineResponse:
    """Entrega los umbrales de SLA, límites de discretización y reglas de diagnóstico del módulo de monitoreo."""
    reglas_formateadas = [
        {
            "premisas": sorted(list(premisas)),
            "conclusion": conclusion,
        }
        for premisas, conclusion in REGLAS_DIAGNOSTICO
    ]

    return MonitoreoBaselineResponse(
        baseline_referencia={
            "temperatura_cpu_c": float(BASELINE_REFERENCIA[0]),
            "carga_servidor_pct": float(BASELINE_REFERENCIA[1]),
            "tasa_errores_min": float(BASELINE_REFERENCIA[2]),
        },
        umbral_distancia_alerta=float(UMBRAL_DISTANCIA_ALERTA),
        umbrales_simbolicos={
            "temperatura_alta": float(UMBRAL_TEMPERATURA_ALTA),
            "carga_alta": float(UMBRAL_CARGA_ALTA),
            "errores_presentes": float(UMBRAL_ERRORES_PRESENTES),
        },
        reglas_simbolicas=reglas_formateadas,
        automata_alerta_patron="Secuencia binaria que concluye con '01' (DFA estado de aceptación q2)",
        metricas_descripcion=DESCRIPCION_METRICAS,
    )


@router.get(
    "/equipos-ejemplo",
    response_model=List[EquipoEjemploItem],
    status_code=status.HTTP_200_OK,
    summary="Obtener los equipos de prueba y casos de referencia oficiales",
    description="Retorna los 3 casos representativos de Semana 07 listos para simulación y validación rápida.",
)
def get_equipos_ejemplo_endpoint() -> List[EquipoEjemploItem]:
    """Devuelve los 3 equipos de referencia (uno sano y dos críticos) para pruebas rápidas en la consola."""
    return [
        EquipoEjemploItem(
            equipo_id="PC-DIRECCION-01",
            temperatura_cpu_c=70.0,
            carga_servidor_pct=0.80,
            tasa_errores_min=2.0,
            secuencia_eventos="0000",
            descripcion_esperada="Equipo dentro de los parámetros de SLA; sin anomalías numéricas, simbólicas ni sintácticas.",
            estado_esperado="SALUDABLE",
        ),
        EquipoEjemploItem(
            equipo_id="WS-DISENO-CAD-03",
            temperatura_cpu_c=72.0,
            carga_servidor_pct=0.85,
            tasa_errores_min=3.0,
            secuencia_eventos="1101",
            descripcion_esperada="Alerta por temperatura y carga alta, errores presentes y secuencia crítica con patrón '01'.",
            estado_esperado="NO SALUDABLE",
        ),
        EquipoEjemploItem(
            equipo_id="SRV-BASE-DATOS-02",
            temperatura_cpu_c=76.5,
            carga_servidor_pct=0.92,
            tasa_errores_min=5.0,
            secuencia_eventos="0001",
            descripcion_esperada="Alerta crítica: Severo desvío de SLA, activación de incidente crítico P1 y patrón DFA '01'.",
            estado_esperado="NO SALUDABLE",
        ),
    ]


@router.get(
    "/random",
    status_code=status.HTTP_200_OK,
    summary="Generar telemetría aleatoria controlada (saludable o anómala)",
    description="Genera muestras sintéticas controladas de telemetría para pruebas de integración del frontend.",
)
def get_random_telemetria_endpoint(tipo: str = "anomalo") -> Dict[str, Any]:
    """Genera una muestra sintética aleatoria de telemetría (tipo "saludable" o "anomalo") para pruebas de carga en frontend."""
    es_saludable = str(tipo).strip().lower() in ("saludable", "normal", "sano", "ok")
    if es_saludable:
        tipo_out = "saludable"
        equipo_id = f"PC-CORP-{random.randint(10, 99)}"
        temp = round(random.uniform(55.0, 68.5), 1)
        carga = round(random.uniform(0.35, 0.75), 2)
        errores = round(random.uniform(0.0, 1.8), 1)
        secuencia = random.choice(["0000", "1100", "0100", "1010", "0010"])
    else:
        tipo_out = "anomalo"
        equipo_id = f"SRV-CRIT-{random.randint(10, 99)}"
        temp = round(random.uniform(73.5, 88.0), 1)
        carga = round(random.uniform(0.85, 0.98), 2)
        errores = round(random.uniform(3.5, 8.5), 1)
        secuencia = random.choice(["1101", "0001", "1001", "0101"])

    return {
        "success": True,
        "tipo": tipo_out,
        "equipo_id": equipo_id,
        "temperatura_cpu_c": temp,
        "carga_servidor_pct": carga,
        "tasa_errores_min": errores,
        "secuencia_logs": secuencia,
        "secuencia_eventos": secuencia,
    }


