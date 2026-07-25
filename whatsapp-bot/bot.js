/*
 * Chatbot de WhatsApp conectado al agente Haceb — con Baileys.
 *
 * Baileys descifra los medios (notas de voz) nativamente en Node, sin navegador.
 * Por eso maneja bien texto Y audio, a diferencia de whatsapp-web.js (cuya
 * descarga de medios se rompe con el WhatsApp Web actual).
 *
 * El agente debe estar corriendo en http://localhost:5000
 * (arráncalo con:  python -m channels.whatsapp).
 *
 * ADVERTENCIA: automatiza WhatsApp de forma no oficial; el número puede ser
 * baneado. Usa un número de repuesto.
 *
 * Uso:  cd whatsapp-bot && npm install && npm start   (escanea el QR)
 */

const {
  default: makeWASocket,
  useMultiFileAuthState,
  downloadMediaMessage,
  fetchLatestBaileysVersion,
  DisconnectReason,
} = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const qrcode = require('qrcode-terminal');
const qrimg = require('qrcode');
const path = require('path');

const AGENTE = process.env.AGENTE_URL || 'http://localhost:5000/message';
const AGENTE_AUDIO = process.env.AGENTE_AUDIO_URL || 'http://localhost:5000/audio';

let logger;
try {
  logger = require('pino')({ level: 'silent' });
} catch (_) {
  logger = undefined;
}

async function main() {
  const { state, saveCreds } = await useMultiFileAuthState(
    path.join(__dirname, 'baileys_auth')
  );
  const { version } = await fetchLatestBaileysVersion();

  const sock = makeWASocket({
    version,
    auth: state,
    logger,
    printQRInTerminal: false,
    markOnlineOnConnect: false,
    syncFullHistory: false,
  });

  sock.ev.on('creds.update', saveCreds);

  sock.ev.on('connection.update', (u) => {
    const { connection, lastDisconnect, qr } = u;
    if (qr) {
      console.log('\n================  ESCANEA ESTE QR  ================');
      console.log('WhatsApp > Dispositivos vinculados > Vincular un dispositivo\n');
      qrcode.generate(qr, { small: true });
      qrimg.toFile(path.join(__dirname, 'qr.png'), qr, { width: 480, margin: 2 }, (e) => {
        if (!e) console.log('>> QR tambien en whatsapp-bot/qr.png\n');
      });
    }
    if (connection === 'open') {
      console.log('\n>> ✅ Agente Haceb CONECTADO a WhatsApp (Baileys). Esperando mensajes...\n');
    }
    if (connection === 'close') {
      const code =
        lastDisconnect && lastDisconnect.error instanceof Boom
          ? lastDisconnect.error.output.statusCode
          : 0;
      if (code === DisconnectReason.loggedOut) {
        console.log('Sesion cerrada. Borra la carpeta baileys_auth y vuelve a escanear.');
      } else {
        console.log('Conexion cerrada, reconectando...');
        main();
      }
    }
  });

  sock.ev.on('messages.upsert', async ({ messages, type }) => {
    if (type !== 'notify') return;
    for (const msg of messages) {
      const from = msg.key && msg.key.remoteJid;
      try {
        if (!msg.message || msg.key.fromMe || !from) continue;
        if (from.endsWith('@g.us') || from === 'status@broadcast') continue;

        const m = msg.message.ephemeralMessage
          ? msg.message.ephemeralMessage.message
          : msg.message;
        const text =
          m.conversation || (m.extendedTextMessage && m.extendedTextMessage.text) || '';
        const audio = m.audioMessage;

        await sock.sendPresenceUpdate('composing', from);

        let data;
        if (audio) {
          console.log(`<- ${from}: [nota de voz]`);
          const buffer = await downloadMediaMessage(
            msg, 'buffer', {}, { logger, reuploadRequest: sock.updateMediaMessage }
          );
          const b64 = Buffer.from(buffer).toString('base64');
          const resp = await fetch(AGENTE_AUDIO, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ from, audio: b64, mime: audio.mimetype || 'audio/ogg' }),
          });
          data = await resp.json();
          if (data.transcripcion) console.log(`   (dijo: ${data.transcripcion.slice(0, 70)})`);
        } else if (text.trim()) {
          console.log(`<- ${from}: ${text}`);
          const resp = await fetch(AGENTE, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ from, body: text }),
          });
          data = await resp.json();
        } else {
          continue;
        }

        const reply = (data && data.reply) || 'No pude responder en este momento.';
        await sock.sendMessage(from, { text: reply });
        console.log(`-> ${from}: ${reply.slice(0, 60)}...`);
      } catch (e) {
        console.error('error:', (e && (e.stack || e.message)) || e);
        try {
          if (from) await sock.sendMessage(from, { text: 'Tuve un problema tecnico. Intenta de nuevo.' });
        } catch (_) {}
      }
    }
  });
}

console.log('Iniciando WhatsApp (Baileys)...');
main().catch((e) => console.error('No se pudo iniciar:', e));
