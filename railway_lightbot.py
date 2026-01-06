import telebot
import os
import logging
from flask import Flask, request
from threading import Thread
import json

# Конфіг
BOT_TOKEN = os.getenv('BOT_TOKEN')
TUYA_CLIENT_ID = os.getenv('TUYA_CLIENT_ID')
TUYA_CLIENT_SECRET = os.getenv('TUYA_CLIENT_SECRET')
TUYA_DEVICE_ID = os.getenv('TUYA_DEVICE_ID', 'bfa671762a871e5405rvq4')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store device state
device_state = {'switch_led': False, 'online': False}

# ===== TELEGRAM КОМАНДИ =====
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 
        "🏠 Light Control Bot\n"
        "/on - Turn light ON\n"
        "/off - Turn light OFF\n"
        "/status - Check status")

@bot.message_handler(commands=['on'])
def handle_on(message):
    # Відправляємо Telegram повідомлення про намір
    # Реальна зміна прийде через Webhook від Tuya
    bot.reply_to(message, "⏳ Sending /on command...")
    logger.info(f"[CMD] /on requested by {message.from_user.id}")

@bot.message_handler(commands=['off'])
def handle_off(message):
    bot.reply_to(message, "⏳ Sending /off command...")
    logger.info(f"[CMD] /off requested by {message.from_user.id}")

@bot.message_handler(commands=['status'])
def handle_status(message):
    status_text = f"📊 Light Status:\n"
    status_text += f"State: {'ON 💡' if device_state['switch_led'] else 'OFF 🌑'}\n"
    status_text += f"Online: {'Yes ✅' if device_state['online'] else 'No ❌'}"
    bot.reply_to(message, status_text)

# ===== WEBHOOK ENDPOINT =====
@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Tuya надсилає сюди JSON з інформацією про зміни пристрою
    """
    try:
        data = request.get_json()
        logger.info(f"[WEBHOOK] Received: {data}")
        
        # Обновляємо стан з Tuya
        device_id = data.get('deviceId')
        status = data.get('status')  # List of device updates
        
        if status:
            for item in status:
                code = item.get('code')  # 'switch_led', 'online' тощо
                value = item.get('value')
                
                if code == 'switch_led':
                    device_state['switch_led'] = value
                    logger.info(f"[UPDATE] Light: {value}")
                elif code == 'online':
                    device_state['online'] = value
                    logger.info(f"[UPDATE] Online: {value}")
        
        return {'success': True, 'msg': 'ok'}, 200
    except Exception as e:
        logger.error(f"[WEBHOOK ERROR] {e}")
        return {'success': False, 'msg': str(e)}, 400

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200

# ===== TELEGRAM POLLING =====
def telegram_polling():
    logger.info("[TELEGRAM] Polling started")
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"[TELEGRAM ERROR] {e}")

# ===== MAIN =====
if __name__ == '__main__':
    logger.info("[INIT] Bot starting...")
    logger.info(f"[INIT] BOT_TOKEN: {BOT_TOKEN[:20]}...")
    logger.info(f"[INIT] TUYA_CLIENT_ID: {TUYA_CLIENT_ID}")
    
    # Запусти Telegram polling в окремому потоці
    polling_thread = Thread(target=telegram_polling, daemon=True)
    polling_thread.start()
    
    # Запусти Flask для Webhook
    logger.info("[FLASK] Starting webhook server on :8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
