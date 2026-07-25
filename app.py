"""
Interfaz del agente de ciclo de vida Haceb.

    streamlit run app.py

Muestra a proposito el trabajo interno: que herramientas se llamaron, con que
argumentos y con que fuentes. Un agente fundamentado hay que poder auditarlo en
vivo, y es lo que un jurado quiere ver.
"""

from __future__ import annotations

import streamlit as st

from agent import loop, validator, vision

st.set_page_config(page_title="Haceb · Agente de ciclo de vida", page_icon="🧊", layout="centered")

EJEMPLOS = [
    "Tengo un hueco de 70 cm de ancho y 190 de alto, y la puerta mide 75. ¿Qué nevera me sirve?",
    "¿Cuánto me cuesta en luz una nevera de 448 litros en 10 años?",
    "Mi nevera 9003548 no enfría bien en la parte de abajo, ¿qué reviso?",
    "Se dañó el compresor de mi nevera 9003548, la compré hace 6 años. ¿La cubre la garantía?",
    "Estoy entre la 9003548 y la 9003189, ¿cuál me sale más barata en total?",
]


def inicializar():
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []   # lo que se muestra
    if "historial" not in st.session_state:
        st.session_state.historial = []  # memoria que ve el modelo
    if "pendiente" not in st.session_state:
        st.session_state.pendiente = None
    if "foto_procesada" not in st.session_state:
        st.session_state.foto_procesada = None


def procesar_foto(archivo):
    """Identifica el producto desde una foto y arranca la conversacion con el."""
    firma = archivo.name + str(archivo.size)
    if st.session_state.foto_procesada == firma:
        return
    st.session_state.foto_procesada = firma

    with st.spinner("Leyendo la foto…"):
        try:
            datos = archivo.getvalue()
            mime = archivo.type or "image/jpeg"
            res = vision.identificar(datos, mime)
        except Exception as e:
            st.error(f"No pude leer la imagen: {type(e).__name__}")
            return

    if not res.get("identificado"):
        st.warning(res.get("motivo", "No pude identificar el producto en la foto."))
        lect = res.get("lectura", {})
        if lect.get("descripcion"):
            st.caption(f"Lo que vi: {lect['descripcion']}")
        return

    p = res["producto"]
    st.success(f"📷 Identifiqué: **{p['nombre']}** (ref. {res['referencia']})")
    # Arranca la conversacion como si el usuario ya hubiera dado la referencia.
    st.session_state.pendiente = (
        f"Subí una foto de la placa de datos de mi {p['nombre']} "
        f"(referencia {res['referencia']}). Cuéntame qué puedo consultar sobre este equipo."
    )


def barra_lateral():
    with st.sidebar:
        st.markdown("### Cómo funciona")
        st.caption(
            "Este agente no responde de memoria. Cada dato sale de una "
            "herramienta sobre el catálogo público de Haceb o del manual "
            "oficial del producto, y un segundo agente audita la respuesta "
            "antes de mostrarla."
        )
        st.markdown("### 📷 ¿No sabes la referencia?")
        st.caption("Súbele una foto a la placa de datos del equipo y la identifico.")
        foto = st.file_uploader(
            "Foto de la placa", type=["jpg", "jpeg", "png"],
            label_visibility="collapsed",
        )
        if foto is not None:
            st.image(foto, use_container_width=True)
            procesar_foto(foto)
            if st.session_state.pendiente:
                st.rerun()
        st.divider()
        st.markdown("### Pruébalo")
        for i, ej in enumerate(EJEMPLOS):
            if st.button(ej, key=f"ej{i}", use_container_width=True):
                st.session_state.pendiente = ej
                st.rerun()
        st.divider()
        if st.button("Reiniciar conversación", use_container_width=True):
            st.session_state.mensajes = []
            st.session_state.historial = []
            st.rerun()
        st.caption(
            "Datos: catálogo público de Haceb (API VTEX) y manuales de usuario "
            "oficiales. 47 productos · 17 manuales."
        )


def pintar_traza(traza, dictamen):
    if traza and traza.pasos:
        with st.expander(f"🔍 {len(traza.pasos)} consultas a las fuentes", expanded=False):
            for paso in traza.pasos:
                args = ", ".join(f"{k}={v!r}" for k, v in paso["argumentos"].items())
                st.code(f"{paso['herramienta']}({args})", language="python")
            if traza.fuentes:
                st.caption("Fuentes consultadas:")
                for f in traza.fuentes:
                    st.caption(f"· {f}")

    if not dictamen:
        return
    if dictamen.get("verificado") and dictamen.get("fundamentada"):
        st.success("✓ Auditado: todas las afirmaciones respaldadas por las fuentes", icon="✅")
    elif dictamen.get("verificado"):
        sin = dictamen.get("afirmaciones_sin_respaldo") or []
        st.warning(
            "⚠ El auditor no pudo respaldar parte de la respuesta"
            + (f": {sin[0]}" if sin else ""),
            icon="⚠️",
        )
    else:
        st.info("El auditor no pudo revisar esta respuesta.", icon="ℹ️")


def procesar(pregunta: str):
    st.session_state.mensajes.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando el catálogo y los manuales…"):
            try:
                texto, traza, historial = loop.responder(
                    pregunta, st.session_state.historial
                )
                st.session_state.historial = historial
            except Exception as e:
                msg = str(e)
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    st.warning(
                        "⏳ Todas las llaves de API están en su límite de cuota "
                        "por el momento. Espera unos segundos y vuelve a intentar. "
                        "Tip: agrega más llaves en `.env` (una por integrante) para "
                        "que el agente rote entre ellas.",
                        icon="⏳",
                    )
                elif "403" in msg or "PERMISSION_DENIED" in msg:
                    st.warning(
                        "🔑 La llave de API todavía no tiene permiso activo "
                        "(proyecto recién habilitado en Google, propaga en unos "
                        "minutos). Reintenta en un momento.",
                        icon="🔑",
                    )
                else:
                    st.error(f"No pude consultar el modelo: {type(e).__name__}")
                    st.caption(msg[:300])
                return

        with st.spinner("Auditando la respuesta…"):
            dictamen = validator.validar(texto, loop.evidencia_json(traza))

        final = validator.aplicar(texto, dictamen)
        st.markdown(final)
        pintar_traza(traza, dictamen)

    st.session_state.mensajes.append(
        {"rol": "assistant", "texto": final, "traza": traza, "dictamen": dictamen}
    )


def main():
    inicializar()

    st.title("🧊 Agente de ciclo de vida Haceb")
    st.caption(
        "Antes de comprar y después de comprar. Fundamentado en el catálogo "
        "y los manuales reales — nunca en la memoria del modelo."
    )

    barra_lateral()

    for m in st.session_state.mensajes:
        with st.chat_message("user" if m["rol"] == "user" else "assistant"):
            st.markdown(m["texto"])
            if m["rol"] == "assistant":
                pintar_traza(m.get("traza"), m.get("dictamen"))

    pregunta = st.chat_input("¿En qué te ayudo con tu electrodoméstico?")
    if st.session_state.pendiente:
        pregunta = st.session_state.pendiente
        st.session_state.pendiente = None
    if pregunta:
        procesar(pregunta)


if __name__ == "__main__":
    main()
