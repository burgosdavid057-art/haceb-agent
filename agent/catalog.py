"""
Acceso al catalogo de Haceb ya ingerido.

Toda herramienta del agente lee de aqui. Ningun dato se inventa: si un campo
no existe en la fuente, se devuelve None y el agente debe decirlo.
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "data" / "catalog.json"


def normaliza(texto: str) -> str:
    """minusculas sin tildes, para comparar sin sorpresas"""
    texto = unicodedata.normalize("NFD", (texto or "").lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


@lru_cache(maxsize=1)
def productos() -> list[dict]:
    if not CATALOGO.exists():
        raise FileNotFoundError(
            f"No existe {CATALOGO}. Corre primero:  python ingest.py"
        )
    return json.loads(CATALOGO.read_text(encoding="utf-8"))


def por_referencia(referencia: str) -> dict | None:
    ref = normaliza(referencia).strip()
    for p in productos():
        if normaliza(p["referencia"]) == ref or p["id"] == referencia:
            return p
    # busqueda tolerante: la referencia aparece dentro del nombre
    for p in productos():
        if ref and ref in normaliza(p["nombre"]):
            return p
    return None


def buscar(
    consulta: str = "",
    categoria: str | None = None,
    litros_min: float | None = None,
    precio_max: float | None = None,
    limite: int = 6,
) -> list[dict]:
    """Busqueda por palabras sobre nombre, descripcion y especificaciones.

    litros_min es un filtro SUAVE: si ningun producto alcanza esa capacidad, en
    vez de devolver vacio (que llevaria al agente a decir "no existe"), devuelve
    los de mayor capacidad para que pueda responder "no hay de X litros, la
    mayor es Y". El cliente busca por nombre y tamaño, no por referencia exacta.
    """
    terminos = [t for t in re.split(r"\W+", normaliza(consulta)) if len(t) > 2]
    # Palabras genericas que no deben, por si solas, filtrar el catalogo.
    genericas = {"nevera", "neveras", "lavadora", "lavadoras", "congelador",
                 "congeladores", "electrodomestico", "litros", "litro"}
    utiles = [t for t in terminos if t not in genericas]

    candidatos = []
    for p in productos():
        if categoria and normaliza(categoria) not in normaliza(p["categoria"]):
            continue
        if precio_max and (p["precio"] or 0) > precio_max:
            continue

        heno = normaliza(
            p["nombre"] + " " + p["descripcion"] + " " + " ".join(p["specs"].values())
        )
        # Puntaje: los terminos utiles pesan; los genericos solo desempatan.
        puntaje = sum(2 for t in utiles if t in heno)
        puntaje += sum(1 for t in terminos if t in genericas and t in heno)
        if terminos and puntaje == 0:
            continue
        candidatos.append((puntaje, litros_de(p), p))

    if not candidatos:
        return []

    if litros_min:
        cumplen = [c for c in candidatos if c[1] is not None and c[1] >= litros_min]
        if cumplen:
            cumplen.sort(key=lambda x: (-x[0], -(x[1] or 0)))
            return [c[2] for c in cumplen[:limite]]
        # Nadie alcanza la capacidad pedida: devolver los mas grandes.
        candidatos.sort(key=lambda x: (-(x[1] or 0), -x[0]))
        return [c[2] for c in candidatos[:limite]]

    candidatos.sort(key=lambda x: (-x[0], -(x[2]["precio"] or 0)))
    return [c[2] for c in candidatos[:limite]]


def litros_de(p: dict) -> float | None:
    """Capacidad en litros de un producto, si esta publicada."""
    litros = (
        p["specs"].get("Capacidad neta en litros")
        or p["specs"].get("Capacidad bruta En Litros")
        or p["specs"].get("Capacidad de lavado")
    )
    if not litros:
        return None
    m = re.search(r"(\d+)", str(litros))
    return float(m.group(1)) if m else None


def resumen(p: dict) -> dict:
    """Vista compacta de un producto, la que ve el modelo."""
    return {
        "referencia": p["referencia"],
        "nombre": p["nombre"],
        "categoria": p["categoria"],
        "precio_cop": p["precio"],
        "disponible": p["disponible"],
        "dimensiones_cm": p["dim_cm"],
        "peso_kg": p["peso_kg"],
        "consumo_kwh_mes": p["consumo_kwh_mes"],
        "clase_energetica": p["clase_energetica"],
        "garantia": p["specs"].get("Garantía"),
        "tiene_manual": bool(p.get("manual_file")),
        "url": p["url"],
    }
