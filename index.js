const { default: makeWASocket, useMultiFileAuthState, delay } = require('@whiskeysockets/baileys');
const express = require('express');
const pino = require('pino');
const app = express();

app.use(express.json());

let sock = null;

// دالة تشغيل وربط الواتساب بكود الهاتف
async function connectToWhatsApp(phoneNumber, res) {
    const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys');
    
    sock = makeWASocket({
        auth: state,
        printQRInTerminal: false,
        logger: pino({ level: 'silent' })
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
        const { connection } = update;
        if (connection === 'open') {
            console.log('✅ [WhatsApp] متصل الآن داخلياً وجاهز تماماً للفحص!');
        }
    });

    await delay(3000);
    try {
        let code = await sock.requestPairingCode(phoneNumber);
        res.json({ status: "success", code: code });
    } catch (err) {
        res.json({ status: "error", message: err.message });
    }
}

app.post('/api/request-code', async (req, res) => {
    const { phone } = req.body; 
    await connectToWhatsApp(phone, res);
});

app.post('/api/filter', async (req, res) => {
    const { numbers } = req.body;
    if (!sock) return res.json({ status: "error", message: "الرجاء ربط حساب الواتساب أولاً!" });

    let validNumbers = [];
    let invalidNumbers = [];

    for (let num of numbers) {
        try {
            const [result] = await sock.onWhatsApp(num);
            if (result && result.exists) {
                validNumbers.push(num);
            } else {
                invalidNumbers.push(num);
            }
        } catch (e) {
            invalidNumbers.push(num);
        }
        await delay(400); 
    }

    res.json({ status: "success", active: validNumbers, inactive: invalidNumbers });
});

// التشغيل على البورت 3000 الداخلي المفتوح في الحاوية
app.listen(3000, '127.0.0.1', () => console.log('🚀 [WhatsApp Backend] شغال داخلياً على المنفذ 3000'));
