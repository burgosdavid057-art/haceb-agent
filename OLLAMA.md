# Correr el agente Haceb en tu Mac con Ollama 🖥️

Guía para levantar el agente **100% local** en tu Mac (M5 Pro), sin cuotas ni
llaves de nube. El modelo corre en tu máquina; los datos no salen de ella.

> Si solo quieres que arranque, salta a **[Arranque rápido](#arranque-rápido)**.
> El resto es el contexto para que entiendas qué estás corriendo.

---

## Qué es esto (contexto en 1 minuto)

Es nuestro proyecto para el hackathon **AgentSprint** (ReshapeX, EAFIT). Es un
**agente de IA de ciclo de vida para electrodomésticos Haceb**: acompaña al
cliente antes de comprar (¿cabe en mi cocina?, ¿cuánto gasta de luz?) y después
(se dañó, ¿lo cubre la garantía?, ¿qué reviso en el manual?).

La idea central, y lo que el jurado premia: **el agente no alucina**. Cada dato
sale de una herramienta sobre el catálogo real de Haceb o de los manuales
oficiales, nunca de la memoria del modelo. Y un segundo agente **audita** cada
respuesta antes de mostrarla. Cuando no hay dato (ej. un repuesto), **se niega a
inventar y escala** a servicio técnico.

Los 5 componentes que el jurado revisa, todos funcionando:
- **RAG con base vectorial** (Chroma + BM25) sobre los manuales
- **Herramientas externas** (9 funciones sobre el catálogo real)
- **Memoria** entre turnos
- **Ingeniería de contexto** (descripciones que enseñan cuándo usar cada tool)
- **Sub-agente validador** que verifica que todo esté fundamentado

**Por qué en tu Mac con Ollama:** cero cuota (los free tier de Gemini y Groq se
agotan), cero costo, y "todo corre local, los datos no salen" es un argumento
fuerte de privacidad para el jurado.

---

## Arranque rápido

Necesitas: **Python 3.10+**, **git** y **[Ollama](https://ollama.com)**.

```bash
# 1. Clonar el repo
git clone <URL_DEL_REPO> haceb-agent
cd haceb-agent

# 2. Dependencias de Python
pip install -r requirements.txt

# 3. Ollama: modelo de CHAT con tool calling (elige según tu RAM)
ollama pull qwen2.5:7b           # ~4.7 GB — recomendado, tool calling sólido
# ollama pull qwen2.5:14b        # ~9 GB  — mejor razonamiento
# ollama pull llama3.3:70b       # ~43 GB — el más fuerte (necesitas ~48GB RAM)

# 4. Ollama: modelo de EMBEDDINGS para el RAG (multilingüe, bueno en español)
ollama pull bge-m3               # ~1.2 GB

# 5. Crear el modelo con ventana de contexto grande horneada (para charlas
#    largas de varios turnos). El Modelfile ya viene en el repo:
ollama create haceb-qwen -f Modelfile
#    (si usas otro modelo base, edita la primera línea del Modelfile)

# 6. Dejar Ollama sirviendo (en otra terminal, o ya corre como app)
ollama serve

# 7. Configurar el .env para usar Ollama
cp .env.example .env
#    edita .env y deja activas estas líneas:
#       OLLAMA_HOST=localhost:11434
#       OLLAMA_MODEL=haceb-qwen
#       OLLAMA_EMBED_MODEL=bge-m3
#       OLLAMA_NUM_CTX=8192

# 7. Construir el índice del RAG con los embeddings locales (~1 min, sin nube)
python build_index.py && python build_vectordb.py

# 8. Levantar la app
streamlit run app.py
```

Se abre en http://localhost:8501. Pruébalo con:
- *"Tengo un hueco de 70 cm de ancho y 190 de alto, la puerta mide 75. ¿Qué nevera me sirve?"*
- *"Se dañó el compresor de mi nevera 9003548, la compré hace 4 años. ¿La cubre la garantía y qué repuesto necesito?"*
- *"Mi nevera 9003548 no enfría bien abajo, ¿qué reviso?"*

---

## Elegir el modelo según tu Mac

El agente usa **tool calling** (function calling), así que el modelo DEBE
soportarlo. Recomendados, de menor a mayor exigencia:

| Modelo | RAM aprox. | Notas |
|---|---|---|
| `llama3.1:8b` | ~6 GB | Rápido, tool calling decente. Buen punto de arranque. |
| `qwen2.5:14b` | ~9 GB | **Recomendado.** Excelente con herramientas. |
| `qwen2.5:32b` | ~20 GB | Razona mejor los casos difíciles. |
| `llama3.3:70b` | ~43 GB | El más fuerte; necesitas bastante RAM unificada. |

Cambias de modelo editando `OLLAMA_MODEL` en el `.env` — no se toca código.

> **Nota:** el agente ya trae una "guarda anti-error" en las herramientas (por
> ejemplo, si el modelo confunde ancho y alto de un espacio, el cálculo lo
> corrige). Así un modelo local más pequeño sigue dando respuestas correctas.

---

## Qué funciona y qué no, sin llaves de nube

Corriendo **solo con Ollama** (sin `GOOGLE_API_KEY`):

| Función | Estado |
|---|---|
| Agente + tool calling (catálogo, espacio, garantía, energía) | ✅ 100% local |
| **RAG semántico** sobre manuales (embeddings bge-m3 + BM25) | ✅ 100% local |
| Sub-agente validador | ✅ 100% local |
| Memoria de conversación (contexto 8192 tokens) | ✅ 100% local |
| **Foto de la placa → producto** (visión) | ⚠️ Necesita una llave de Gemini |

Todo corre en tu máquina sin cuota. Lo único que aún usa la nube es la **foto de
la placa** (visión multimodal): si la quieres, agrega al `.env` una llave gratis
de Gemini (https://aistudio.google.com/apikey):

```bash
GOOGLE_API_KEY=tu_llave_aqui
```

---

## Conectar tu Mac como servidor del equipo (opcional)

Si quieres que el agente corra en TU Mac pero la app la maneje otro del equipo
desde su portátil, expón Ollama a la red local:

```bash
# En tu Mac:
OLLAMA_HOST=0.0.0.0 ollama serve
```

Y en el `.env` del otro (con tu IP local):
```bash
OLLAMA_HOST=192.168.1.50:11434   # <- tu IP en la red
OLLAMA_MODEL=qwen2.5:14b
```

> Ojo: en el wifi del evento puede que no se vean entre máquinas. Si pasa, usen
> el mismo hotspot/router, o [Tailscale](https://tailscale.com) (5 min de setup).

---

## Estructura del proyecto

```
haceb-agent/
├─ app.py                 # interfaz Streamlit (lo que ve el usuario)
├─ ingest.py              # baja catálogo + manuales de Haceb (ya versionados)
├─ build_bm25.py          # arma el índice de búsqueda local (sin llaves)
├─ build_index.py         # embeddings Gemini (opcional, mejora el RAG)
├─ build_vectordb.py      # puebla Chroma desde los embeddings (opcional)
├─ agent/
│  ├─ llm.py              # elige proveedor: Ollama > Groq > Gemini
│  ├─ openai_backend.py   # loop del agente para Ollama/Groq (protocolo OpenAI)
│  ├─ loop.py             # loop del agente para Gemini + prompt del sistema
│  ├─ tools.py            # las 9 herramientas (datos reales, nunca mock)
│  ├─ declarations.py     # esquema de las herramientas (Gemini + OpenAI)
│  ├─ knowledge.py        # RAG: BM25 + semántico
│  ├─ vectordb.py         # base vectorial Chroma
│  ├─ validator.py        # sub-agente auditor
│  ├─ vision.py           # foto de placa → producto (necesita Gemini)
│  └─ catalog.py          # acceso al catálogo
├─ channels/whatsapp.py   # webhook de WhatsApp (opcional)
├─ evals/                 # harness que mide alucinaciones
└─ data/
   ├─ catalog.json        # 47 productos reales (versionado)
   └─ manuals/            # 17 manuales oficiales (versionado)
```

Toda la documentación del proyecto: [README.md](README.md). El guion del pitch:
[PITCH.md](PITCH.md).
