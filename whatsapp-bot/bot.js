/*
 * Chatbot de WhatsApp conectado al agente Haceb (whatsapp-web.js).
 *
 * Vincula TU número de WhatsApp y responde a quien te escriba con las
 * respuestas fundamentadas del agente. El agente debe estar corriendo en
 * http://localhost:5000 (arráncalo con:  python -m channels.whatsapp).
 *
 * ADVERTENCIA: automatiza WhatsApp Web de forma no oficial. Va contra los
 * términos de WhatsApp; el número podría ser baneado. Usa un número de
 * repuesto, no tu personal.
 *
 * Uso:
 *   cd whatsapp-bot && npm install && npm start
 *   Escanea el QR que aparece:  WhatsApp > Dispositivos vinculados > Vincular
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const qrimg = require('qrcode');
const path = require('path');

const AGENTE = process.env.AGENTE_URL || 'http://localhost:5000/message';
const AGENTE_AUDIO = process.env.AGENTE_AUDIO_URL || 'http://localhost:5000/audio';

// Usa el Chrome del sistema (no baja Chromium). Ajusta la ruta si tu Chrome
// está en otro lado, o instala Chromium con: npx puppeteer browsers install chrome
const fs = require('fs');
const CHROMES = [
  process.env.CHROME_PATH,
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome',
].filter(Boolean);
const chromePath = CHROMES.find((p) => { try { return fs.existsSync(p); } catch { return false; } });

const client = new Client({
  authStrategy: new LocalAuth({ clientId: 'haceb' }),
  puppeteer: {
    headless: true,
    executablePath: chromePath,       // si es undefined, usa el Chromium de puppeteer
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  },
});

client.on('qr', (qr) => {
  console.log('\n================  ESCANEA ESTE QR  ================');
  console.log('WhatsApp en el celular > Dispositivos vinculados > Vincular un dispositivo\n');
  qrcode.generate(qr, { small: true });
  // Tambien lo guarda como imagen nitida (qr.png) para escanear mas facil.
  qrimg.toFile(path.join(__dirname, 'qr.png'), qr, { width: 480, margin: 2 }, (e) => {
    if (!e) console.log('>> QR tambien guardado en whatsapp-bot/qr.png');
  });
});

client.on('authenticated', () => console.log('>> Autenticado. Cargando...'));
client.on('ready', () => {
  console.log('\n>> ✅ Agente Haceb CONECTADO a WhatsApp. Esperando mensajes...\n');
});
client.on('auth_failure', (m) => console.error('Fallo de autenticación:', m));
client.on('disconnected', (r) => console.error('Desconectado:', r));

client.on('message', async (msg) => {
  // Ignora estados, grupos y mensajes propios.
  if (msg.isStatus || msg.from.endsWith('@g.us') || msg.fromMe) return;

  const esVoz = msg.type === 'ptt' || msg.type === 'audio';
  const body = (msg.body || '').trim();
  if (!esVoz && !body) return;

  try {
    try { const chat = await msg.getChat(); await chat.sendStateTyping(); } catch (_) {}

    let data;
    if (esVoz) {
      // Nota de voz: descargar y mandar a Whisper (endpoint /audio del agente).
      console.log(`<- ${msg.from}: [nota de voz]`);
      const media = await msg.downloadMedia();
      if (!media || !media.data) {
        await msg.reply('No pude descargar tu audio. ¿Me lo escribes?');
        return;
      }
      const resp = await fetch(AGENTE_AUDIO, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from: msg.from, audio: media.data, mime: media.mimetype }),
      });
      data = await resp.json();
      if (data.transcripcion) console.log(`   (dijo: ${data.transcripcion.slice(0, 70)})`);
    } else {
      console.log(`<- ${msg.from}: ${body}`);
      const resp = await fetch(AGENTE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from: msg.from, body }),
      });
      data = await resp.json();
    }

    const reply = (data && data.reply) || 'No pude responder en este momento.';
    await msg.reply(reply);   // responde en el mismo chat (soporta formato @lid)
    console.log(`-> ${msg.from}: ${reply.slice(0, 60)}...`);
  } catch (e) {
    console.error('error al responder:', (e && (e.stack || e.message)) || e);
    try { await msg.reply('Tuve un problema técnico. Intenta de nuevo en un momento.'); } catch (_) {}
  }
});

console.log('Iniciando WhatsApp... (la primera vez baja Chromium, puede tardar)');
client.initialize();
