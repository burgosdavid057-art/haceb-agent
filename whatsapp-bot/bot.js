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
  const body = (msg.body || '').trim();
  if (!body) return;

  console.log(`<- ${msg.from}: ${body}`);
  try {
    try { const chat = await msg.getChat(); await chat.sendStateTyping(); } catch (_) {}

    const resp = await fetch(AGENTE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ from: msg.from, body }),
    });
    const data = await resp.json();
    const reply = data.reply || 'No pude responder en este momento.';

    await msg.reply(reply);   // responde en el mismo chat (soporta formato @lid)
    console.log(`-> ${msg.from}: ${reply.slice(0, 60)}...`);
  } catch (e) {
    console.error('error al responder:', (e && (e.stack || e.message)) || e);
    try { await msg.reply('Tuve un problema técnico. Intenta de nuevo en un momento.'); } catch (_) {}
  }
});

console.log('Iniciando WhatsApp... (la primera vez baja Chromium, puede tardar)');
client.initialize();
