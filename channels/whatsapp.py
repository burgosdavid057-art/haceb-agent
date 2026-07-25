"""
Canal WhatsApp para el agente Haceb.

Es un webhook compatible con el sandbox de WhatsApp de Twilio: recibe el mensaje
del usuario, lo pasa por el MISMO agente + validador que la web, y responde en
el formato TwiML que Twilio espera. Es el canal donde de verdad ocurre el
soporte de electrodomesticos en Colombia.

No esta mockeado: procesa un POST real con formato Twilio y produce una
respuesta fundamentada. Se prueba en local con curl (ver abajo) y se conecta a
WhatsApp de verdad con el sandbox de Twilio + un tunel ngrok.

    # Local, sin Twilio:
    python -m channels.whatsapp
    curl -s -X POST localhost:5000/whatsapp \
        --data-urlencode "From=whatsapp:+573001112233" \
        --data-urlencode "Body=mi nevera 9003548 no enfria abajo, que reviso?"

    # En vivo con WhatsApp real:
    #   1) ngrok http 5000
    #   2) en el sandbox de Twilio, "WHEN A MESSAGE COMES IN" -> https://<ngrok>/whatsapp
    #   3) escribe al numero del sandbox desde tu WhatsApp
"""

from __future__ import annotations

import html
from xml.sax.saxutils import escape

from flask import Flask, request, Response

from agent import loop, validator

app = Flask(__name__)

# Memoria por remitente: cada numero de WhatsApp conserva su conversacion.
# En produccion iria a una base; para el demo, en memoria basta.
_memoria: dict[str, list] = {}

# WhatsApp corta mensajes largos; mantenemos las respuestas legibles en el chat.
LIMITE_CHARS = 1400


def _twiml(mensaje: str) -> Response:
    cuerpo = escape(mensaje[:LIMITE_CHARS])
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{cuerpo}</Message></Response>'
    return Response(xml, mimetype="application/xml")


def responder_texto(remitente: str, texto: str) -> str:
    """Corre el agente para un remitente, conservando su memoria."""
    historial = _memoria.get(remitente, [])
    respuesta, traza, historial = loop.responder(texto, historial)
    _memoria[remitente] = historial

    dictamen = validator.validar(respuesta, loop.evidencia_json(traza))
    return validator.aplicar(respuesta, dictamen)


@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    remitente = request.form.get("From", "desconocido")
    cuerpo = (request.form.get("Body") or "").strip()

    if not cuerpo:
        return _twiml("Hola 👋 Soy el asistente de Haceb. Cuéntame qué "
                      "electrodoméstico tienes o qué necesitas.")

    if cuerpo.lower() in ("reiniciar", "reset", "empezar"):
        _memoria.pop(remitente, None)
        return _twiml("Listo, empezamos de nuevo. ¿En qué te ayudo?")

    try:
        respuesta = responder_texto(remitente, cuerpo)
    except Exception as e:
        respuesta = ("Tuve un problema consultando la información. "
                     "Intenta de nuevo o escribe *reiniciar*.")
        app.logger.error("fallo agente: %s", e)

    return _twiml(respuesta)


# Nombres de campo que usan distintos chatbots de WhatsApp para el remitente
# y el texto. El endpoint acepta cualquiera, para conectarse sin fricciones.
_CAMPOS_FROM = ("from", "sender", "phone", "number", "chatId", "chat_id", "wa_id", "author")
_CAMPOS_BODY = ("body", "message", "text", "content", "msg", "prompt")


def _primer_campo(datos: dict, claves) -> str:
    for k in claves:
        v = datos.get(k)
        if isinstance(v, dict):  # a veces viene anidado, ej. {"message":{"text":...}}
            v = v.get("text") or v.get("body") or v.get("content")
        if v:
            return str(v)
    return ""


@app.route("/message", methods=["POST"])
def message():
    """Endpoint JSON para conectar cualquier chatbot de WhatsApp al agente.

    Entrada flexible (acepta from/sender/phone/... y body/message/text/...):
        {"from": "573001112233", "body": "mi nevera no enfria"}
    Salida:
        {"reply": "...", "from": "573001112233"}

    Mantiene memoria por remitente. Escribe 'reiniciar' para limpiarla.
    """
    datos = request.get_json(silent=True) or request.form.to_dict() or {}
    remitente = _primer_campo(datos, _CAMPOS_FROM) or "desconocido"
    cuerpo = _primer_campo(datos, _CAMPOS_BODY).strip()

    def responder(texto):
        # Devuelve varias claves comunes para encajar con distintos chatbots.
        return {"reply": texto, "response": texto, "message": texto, "from": remitente}

    if not cuerpo:
        return responder("Hola 👋 Soy el asistente de electrodomésticos Haceb. "
                         "¿En qué te ayudo con tu equipo?")

    if cuerpo.lower() in ("reiniciar", "reset", "empezar", "/reset"):
        _memoria.pop(remitente, None)
        return responder("Listo, empezamos de nuevo. ¿En qué te ayudo?")

    try:
        texto = responder_texto(remitente, cuerpo)
    except Exception as e:
        app.logger.error("fallo agente: %s", e)
        texto = ("Tuve un problema consultando la información. "
                 "Intenta de nuevo o escribe *reiniciar*.")
    return responder(texto)


DEMO_HTML = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Haceb · WhatsApp (demo)</title>
<style>
 :root{--wa:#075E54;--wa2:#128C7E;--out:#DCF8C6;--bg:#E5DDD5}
 *{box-sizing:border-box;font-family:-apple-system,Segoe UI,Roboto,sans-serif}
 body{margin:0;background:#111;display:flex;justify-content:center}
 .phone{width:100%;max-width:460px;height:100vh;display:flex;flex-direction:column;background:var(--bg)}
 .top{background:var(--wa);color:#fff;padding:12px 14px;display:flex;align-items:center;gap:10px}
 .av{width:38px;height:38px;border-radius:50%;background:var(--wa2);display:grid;place-items:center;font-size:20px}
 .top .n{font-weight:600}.top .s{font-size:12px;opacity:.85}
 .chat{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:8px;
  background-image:linear-gradient(rgba(229,221,213,.6),rgba(229,221,213,.6))}
 .b{max-width:78%;padding:8px 11px;border-radius:9px;font-size:14.5px;line-height:1.4;white-space:pre-wrap;word-wrap:break-word;box-shadow:0 1px .5px rgba(0,0,0,.13)}
 .in{background:#fff;align-self:flex-start;border-top-left-radius:0}
 .out{background:var(--out);align-self:flex-end;border-top-right-radius:0}
 .t{font-size:10px;color:#667;text-align:right;margin-top:2px}
 .bar{display:flex;gap:8px;padding:10px;background:#F0F0F0}
 .bar input{flex:1;border:none;border-radius:22px;padding:11px 15px;font-size:15px;outline:none}
 .bar button{border:none;background:var(--wa2);color:#fff;width:46px;height:46px;border-radius:50%;font-size:20px;cursor:pointer}
 .typing{font-style:italic;color:#667;font-size:13px;align-self:flex-start;padding:2px 6px}
</style></head><body>
<div class="phone">
 <div class="top"><div class="av">🧊</div><div><div class="n">Haceb · Asistente</div><div class="s" id="st">en línea</div></div></div>
 <div class="chat" id="chat"></div>
 <div class="bar"><input id="msg" placeholder="Escribe un mensaje" autocomplete="off">
 <button id="send">➤</button></div>
</div>
<script>
 const chat=document.getElementById('chat'),inp=document.getElementById('msg'),
   btn=document.getElementById('send'),st=document.getElementById('st');
 const FROM='demo-'+Math.random().toString(36).slice(2,8);
 function hora(){const d=new Date();return d.getHours().toString().padStart(2,'0')+':'+d.getMinutes().toString().padStart(2,'0')}
 function burbuja(txt,tipo){const b=document.createElement('div');b.className='b '+tipo;
   b.textContent=txt;const t=document.createElement('div');t.className='t';t.textContent=hora();
   b.appendChild(t);chat.appendChild(b);chat.scrollTop=chat.scrollHeight;return b}
 let typingEl=null;
 function typing(on){st.textContent=on?'escribiendo…':'en línea';
   if(on&&!typingEl){typingEl=document.createElement('div');typingEl.className='typing';typingEl.textContent='escribiendo…';chat.appendChild(typingEl);chat.scrollTop=chat.scrollHeight}
   if(!on&&typingEl){typingEl.remove();typingEl=null}}
 async function enviar(){const txt=inp.value.trim();if(!txt)return;inp.value='';
   burbuja(txt,'out');typing(true);btn.disabled=true;
   try{const r=await fetch('/message',{method:'POST',headers:{'Content-Type':'application/json'},
     body:JSON.stringify({from:FROM,body:txt})});const d=await r.json();
     typing(false);burbuja(d.reply||'(sin respuesta)','in');}
   catch(e){typing(false);burbuja('⚠ No pude conectar con el agente.','in');}
   btn.disabled=false;inp.focus();}
 btn.onclick=enviar;inp.addEventListener('keydown',e=>{if(e.key==='Enter')enviar()});
 setTimeout(()=>burbuja('¡Hola! Soy el asistente de electrodomésticos Haceb 🧊 Pregúntame por una nevera, garantía, si cabe en tu cocina, consumo de energía…','in'),300);
 inp.focus();
</script></body></html>"""


@app.route("/audio", methods=["POST"])
def audio():
    """Recibe una nota de voz (audio en base64), la transcribe con Whisper y
    responde como si fuera un mensaje de texto.

        {"from": "...", "audio": "<base64>", "mime": "audio/ogg"}
        -> {"reply": "...", "transcripcion": "lo que dijo el usuario"}
    """
    import base64

    from agent import transcribe

    datos = request.get_json(silent=True) or {}
    remitente = _primer_campo(datos, _CAMPOS_FROM) or "desconocido"
    b64 = datos.get("audio") or datos.get("data") or ""
    mime = (datos.get("mime") or "audio/ogg").lower()

    if not b64:
        return {"reply": "No recibí el audio. Intenta de nuevo.", "transcripcion": ""}
    if not transcribe.disponible():
        return {"reply": "La transcripción de voz no está disponible en este momento; "
                         "escríbeme el mensaje, por favor.", "transcripcion": ""}
    try:
        crudo = base64.b64decode(b64)
    except Exception:
        return {"reply": "El audio llegó dañado. ¿Puedes reenviarlo?", "transcripcion": ""}

    sufijo = ".ogg" if "og" in mime else ".mp3" if "mp" in mime else ".m4a" if "mp4" in mime or "m4a" in mime else ".wav"
    texto = transcribe.transcribir(crudo, sufijo)
    if not texto:
        return {"reply": "No logré entender el audio. ¿Me lo escribes o lo repites?",
                "transcripcion": ""}

    try:
        respuesta = responder_texto(remitente, texto)
    except Exception as e:
        app.logger.error("fallo agente (audio): %s", e)
        respuesta = "Tuve un problema procesando tu mensaje. Intenta de nuevo."

    return {
        "reply": respuesta, "response": respuesta, "message": respuesta,
        "transcripcion": texto, "from": remitente,
    }


@app.route("/demo", methods=["GET"])
def demo():
    return DEMO_HTML


@app.route("/", methods=["GET"])
def salud():
    return {"servicio": "agente Haceb WhatsApp", "estado": "ok"}


if __name__ == "__main__":
    print("Webhook WhatsApp en http://localhost:5000/whatsapp")
    app.run(host="0.0.0.0", port=5000, debug=False)
