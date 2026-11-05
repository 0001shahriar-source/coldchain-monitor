require('dotenv').config();
const nodemailer = require('nodemailer');

// Telegram Alert
async function sendTelegramAlert(message) {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_CHAT_ID;

  if (!token || !chatId) {
    console.log(`[ALERT DISPATCH (Simulated Telegram)]: ${message}`);
    return { success: true, simulated: true };
  }

  try {
    const url = `https://api.telegram.org/bot${token}/sendMessage`;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: chatId,
        text: `🚨 ColdChain Alert:\n${message}`,
        parse_mode: 'Markdown'
      })
    });
    const data = await res.json();
    return { success: data.ok, response: data };
  } catch (err) {
    console.error('[ALERT DISPATCH] Telegram send error:', err.message);
    return { success: false, error: err.message };
  }
}

// Email SMTP Alert
async function sendEmailAlert(subject, text) {
  const host = process.env.SMTP_HOST;
  const user = process.env.SMTP_USER;
  const pass = process.env.SMTP_PASS;
  const to = process.env.ALERT_EMAIL_TO;

  if (!host || !user || !to) {
    console.log(`[ALERT DISPATCH (Simulated Email)] Subject: ${subject} | Body: ${text}`);
    return { success: true, simulated: true };
  }

  try {
    const transporter = nodemailer.createTransport({
      host: host,
      port: process.env.SMTP_PORT || 587,
      secure: false,
      auth: { user, pass }
    });

    const info = await transporter.sendMail({
      from: `"ColdChain Storage Monitor" <${user}>`,
      to: to,
      subject: `🚨 [ColdChain Alert] ${subject}`,
      text: text
    });
    return { success: true, messageId: info.messageId };
  } catch (err) {
    console.error('[ALERT DISPATCH] Email send error:', err.message);
    return { success: false, error: err.message };
  }
}

async function dispatchIncidentAlert(title, details) {
  const fullText = `*Incident:* ${title}\n*Details:* ${details}\n*Time:* ${new Date().toISOString()}`;
  await Promise.allSettled([
    sendTelegramAlert(fullText),
    sendEmailAlert(title, fullText)
  ]);
}

module.exports = {
  sendTelegramAlert,
  sendEmailAlert,
  dispatchIncidentAlert
};

