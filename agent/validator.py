"""
Sub-agente validador: la ultima linea de defensa contra las alucinaciones.

Corre despues del agente principal, con un modelo barato y una sola tarea:
comprobar que cada dato concreto de la respuesta aparezca en la evidencia que
devolvieron las herramientas. No reescribe la respuesta ni opina sobre el
estilo; solo dictamina.

Es deliberadamente un agente aparte y no una regla dentro del prompt principal:
un modelo que se autoevalua en el mismo turno tiende a darse la razon.
"""

from __future__ import annotations

import json
import re

from google.genai import types

from . import llm

INSTRUCCIONES = """\
Eres un auditor. Recibes (1) la EVIDENCIA que devolvieron unas herramientas y
(2) una RESPUESTA que un asistente le va a dar a un cliente.

Tu unica tarea: decidir si cada afirmacion concreta de la RESPUESTA esta
respaldada por la EVIDENCIA.

Cuenta como afirmacion concreta: medidas, precios, capacidades, consumo,
años de garantia, referencias de producto, instrucciones de un manual, y
cualquier "si cabe" o "esta cubierto".

NO cuentan: saludos, cortesias, preguntas al usuario, ofrecimientos de ayuda,
ni recomendaciones generales sin cifras.

Se estricto con los numeros: si la respuesta dice 71 cm y la evidencia dice
70 cm, eso es una afirmacion NO respaldada.

REGLA DE DECISION: primero lista las afirmaciones concretas que NO encuentres
respaldadas en la evidencia. Luego, "fundamentada" es true SI Y SOLO SI esa
lista quedo vacia. No marques una respuesta como no fundamentada si no puedes
señalar cual afirmacion especifica falla: lo que no puedas nombrar, se aprueba.

Responde SOLO con un JSON valido, sin texto alrededor:
{
  "afirmaciones_sin_respaldo": ["cita textual de cada afirmacion no respaldada"],
  "fundamentada": true|false,
  "explicacion": "una frase"
}
"""


def _extraer_json(texto: str) -> dict | None:
    texto = re.sub(r"^```(?:json)?|```$", "", texto.strip(), flags=re.M).strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", texto, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def validar(respuesta: str, evidencia_json: str) -> dict:
    """Dictamina si la respuesta esta fundamentada en la evidencia.

    Ante cualquier fallo (sin red, sin cuota, JSON invalido) devuelve
    `verificado: False` en vez de aprobar por defecto: si el auditor no pudo
    trabajar, no se puede afirmar que la respuesta sea confiable.
    """
    if not evidencia_json or evidencia_json == "[]":
        return {
            "verificado": True,
            "fundamentada": False,
            "afirmaciones_sin_respaldo": [],
            "explicacion": "El agente respondio sin consultar ninguna herramienta.",
        }

    # Si el agente corre sobre Groq u Ollama, el validador tambien.
    if llm.proveedor() in ("groq", "ollama"):
        from . import openai_backend
        return openai_backend.validar(respuesta, evidencia_json)

    contenido = (
        f"EVIDENCIA (salida de las herramientas):\n{evidencia_json}\n\n"
        f"RESPUESTA a auditar:\n{respuesta}"
    )
    try:
        r = llm.generar(
            contenido,
            config=types.GenerateContentConfig(
                system_instruction=INSTRUCCIONES,
                temperature=0.0,
                response_mime_type="application/json",
            ),
        )
        datos = _extraer_json(r.text or "")
    except Exception as e:
        return {
            "verificado": False,
            "fundamentada": None,
            "afirmaciones_sin_respaldo": [],
            "explicacion": f"No se pudo validar ({type(e).__name__}).",
        }

    if not isinstance(datos, dict) or "fundamentada" not in datos:
        return {
            "verificado": False,
            "fundamentada": None,
            "afirmaciones_sin_respaldo": [],
            "explicacion": "El validador no devolvio un dictamen legible.",
        }

    sin_respaldo = datos.get("afirmaciones_sin_respaldo") or []
    fundamentada = bool(datos.get("fundamentada"))

    # Reconciliacion: el veredicto y la lista deben ser coherentes. Un auditor
    # que declara "no fundamentada" pero no nombra ninguna afirmacion en falta
    # no tiene un hallazgo — lo que no se puede nombrar, se aprueba. Esto evita
    # falsos negativos que pondrian una alerta sobre una respuesta correcta.
    if not fundamentada and not sin_respaldo:
        fundamentada = True
        explicacion = "Sin afirmaciones sin respaldo identificadas."
    else:
        explicacion = datos.get("explicacion", "")

    return {
        "verificado": True,
        "fundamentada": fundamentada,
        "afirmaciones_sin_respaldo": sin_respaldo,
        "explicacion": explicacion,
    }


AVISO = (
    "\n\n---\n"
    "⚠️ *Parte de esta respuesta no pude respaldarla con las fuentes de Haceb. "
    "Antes de decidir con ella, confirma con servicio tecnico: "
    "01 8000 51 22 22.*"
)


def aplicar(respuesta: str, dictamen: dict) -> str:
    """Marca la respuesta cuando el validador no la respalda."""
    if dictamen.get("verificado") and dictamen.get("fundamentada"):
        return respuesta
    return respuesta + AVISO
