"""
Entrada multimodal: de una foto al producto.

Nadie se sabe de memoria la referencia de su nevera, pero la placa de datos
esta pegada al equipo. El usuario le toma una foto, Gemini (que ve imagenes)
lee la placa, y de ahi el agente aterriza todo con datos reales del catalogo.

La identificacion tambien se fundamenta: lo que se lee de la imagen se confronta
contra el catalogo. Si la referencia no existe, se dice; no se inventa un match.
"""

from __future__ import annotations

import json
import re

from . import catalog, llm

INSTRUCCIONES_VISION = """\
Eres un lector de placas de datos de electrodomesticos Haceb. Recibes una foto
que puede ser: la placa/etiqueta de datos de un equipo, el electrodomestico
completo, o un espacio de la cocina.

Extrae SOLO lo que se ve en la imagen. No inventes. Si un campo no es legible,
dejalo vacio.

Responde SOLO con JSON valido:
{
  "tipo_imagen": "placa_datos" | "electrodomestico" | "espacio" | "otro",
  "referencia": "codigo/referencia del producto si es visible, ej. 9003548",
  "modelo_texto": "el nombre o modelo que se lea",
  "categoria": "nevera | lavadora | congelador | otro",
  "texto_visible": "otros datos legibles: litros, voltaje, serie...",
  "descripcion": "que se ve, en una frase"
}
"""


def _extraer_json(texto: str) -> dict | None:
    texto = re.sub(r"^```(?:json)?|```$", "", (texto or "").strip(), flags=re.M).strip()
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


def leer_imagen(imagen: bytes, mime: str = "image/jpeg") -> dict:
    """Lee una foto y devuelve lo que Gemini extrajo, sin confrontar aun."""
    from google.genai import types

    r = llm.generar(
        [
            types.Part.from_bytes(data=imagen, mime_type=mime),
            types.Part(text="Lee esta imagen segun las instrucciones."),
        ],
        config=types.GenerateContentConfig(
            system_instruction=INSTRUCCIONES_VISION,
            temperature=0.0,
            response_mime_type="application/json",
        ),
    )
    datos = _extraer_json(r.text or "")
    return datos or {"tipo_imagen": "otro", "descripcion": "no legible"}


def identificar(imagen: bytes, mime: str = "image/jpeg") -> dict:
    """Lee la foto Y confronta contra el catalogo real.

    Devuelve el producto del catalogo si se pudo identificar, o una razon clara
    de por que no. Nunca afirma un match que el catalogo no respalde.
    """
    # La vision usa Gemini (multimodal). Si el agente corre solo con Ollama y no
    # hay llave de Gemini, se degrada con un mensaje claro en vez de reventar.
    if llm.cuantas_llaves() == 0:
        return {
            "identificado": False,
            "lectura": {},
            "motivo": (
                "La lectura de fotos necesita una llave de Gemini "
                "(GOOGLE_API_KEY en el .env). El resto del agente funciona sin "
                "ella. Dime la referencia del equipo (está en la placa de datos)."
            ),
        }

    lectura = leer_imagen(imagen, mime)

    # 1) por referencia exacta
    producto = None
    ref = (lectura.get("referencia") or "").strip()
    if ref:
        producto = catalog.por_referencia(ref)

    # 2) si no, por el texto del modelo
    if producto is None and lectura.get("modelo_texto"):
        candidatos = catalog.buscar(lectura["modelo_texto"], limite=1)
        if candidatos:
            producto = candidatos[0]

    if producto is None:
        return {
            "identificado": False,
            "lectura": lectura,
            "motivo": (
                "Leí la imagen pero no pude confirmar el producto contra el "
                "catálogo de Haceb. Dime la referencia (suele estar en la placa "
                "de datos) o descríbeme el equipo."
            ),
        }

    return {
        "identificado": True,
        "lectura": lectura,
        "producto": catalog.resumen(producto),
        "referencia": producto["referencia"],
    }
