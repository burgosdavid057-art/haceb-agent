# Agente Haceb en TU WhatsApp

Conecta el agente a un **WhatsApp real** usando
[Baileys](https://github.com/WhiskeySockets/Baileys): vinculas un número, y quien
te escriba (texto **o nota de voz**) recibe respuestas fundamentadas del agente.

> Se usa Baileys (no open-wa ni whatsapp-web.js): open-wa quedó incompatible con
> el WhatsApp Web actual, y whatsapp-web.js no puede descargar las notas de voz.
> Baileys descifra los medios nativamente en Node (sin navegador), así que las
> **notas de voz sí funcionan** (se transcriben con Whisper).

## ⚠️ Advertencia

Automatiza WhatsApp Web de forma **no oficial**. Va contra los términos de
WhatsApp; el número **puede ser baneado**. Usa un número de repuesto, NUNCA tu
número personal.

## Cómo conectarlo (lo más fácil)

Requisitos: Python, Node.js y Google Chrome (ya los tienes).

**Doble clic en `iniciar.bat`.** Eso:
1. Arranca el agente (una ventana aparte, no la cierres).
2. Muestra un **código QR** en la consola.

Escanéalo con tu teléfono: **WhatsApp → Ajustes → Dispositivos vinculados →
Vincular un dispositivo**.

Cuando diga `✅ Agente Haceb CONECTADO a WhatsApp`, escríbele al número vinculado
desde **otro** celular y el agente responde. Deja las dos ventanas abiertas.

### A mano (si prefieres)

```bash
# Terminal 1 — el agente
python -m channels.whatsapp
# Terminal 2 — el bot de WhatsApp
cd whatsapp-bot
npm install        # solo la primera vez
npm start          # muestra el QR
```

## Cómo funciona

```
WhatsApp ──► bot.js (Baileys) ──HTTP──► agente (localhost:5000) ──► respuesta
  texto   ─────────────────────► POST /message
  voz     ─► descarga+descifra ─► POST /audio (Whisper transcribe) ─► respuesta
```

Es el mismo agente de la app web: mismas herramientas, RAG, validador, garantías
y memoria por contacto. Escribe **reiniciar** en el chat para borrar la memoria.

## Notas

- **Notas de voz:** se transcriben con Whisper local (faster-whisper). La primera
  tarda un poco más (carga el modelo); luego es rápida.
- Cada respuesta tarda ~5-15 s (modelo local). Para más velocidad, cambia el
  agente a Groq en el `.env`.
- El QR expira y se regenera solo hasta que lo escaneas. La sesión queda guardada
  en `baileys_auth/`, así que solo escaneas una vez.

## ¿Y si otro maneja el chatbot?

Si un compañero conecta su propio chatbot de WhatsApp, no necesita este bot:
solo apunta al endpoint HTTP del agente. El contrato está en
[CONECTAR.md](CONECTAR.md).
