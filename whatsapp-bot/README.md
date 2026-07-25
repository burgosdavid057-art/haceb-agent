# Agente Haceb en TU WhatsApp

Conecta el agente a un **WhatsApp real** usando
[whatsapp-web.js](https://wwebjs.dev/): vinculas un número, y quien te escriba
recibe respuestas fundamentadas del agente.

> Se usa whatsapp-web.js (no open-wa): open-wa quedó incompatible con el
> WhatsApp Web actual. whatsapp-web.js es la opción mantenida y estable.

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
WhatsApp ──► bot.js (whatsapp-web.js) ──HTTP──► agente (localhost:5000) ──► respuesta
```

Es el mismo agente de la app web: mismas herramientas, RAG, validador y memoria
por contacto. Escribe **reiniciar** en el chat para borrar la memoria de ese hilo.

## Notas

- Usa el Chrome del sistema (no descarga Chromium). Si tu Chrome está en otra
  ruta, define la variable de entorno `CHROME_PATH`.
- Cada respuesta tarda ~5-15 s (modelo local). Para más velocidad, cambia el
  agente a Groq en el `.env`.
- El QR expira cada ~20 s y se regenera solo hasta que lo escaneas.

## ¿Y si otro maneja el chatbot?

Si un compañero conecta su propio chatbot de WhatsApp, no necesita este bot:
solo apunta al endpoint HTTP del agente. El contrato está en
[CONECTAR.md](CONECTAR.md).
