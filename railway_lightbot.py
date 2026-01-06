from flask import Flask, request
from datetime import datetime
import os
import telebot

app = Flask(__name__)

BOT_TOKEN = '8537850530:AAGyzyYAz4Bx25iPt2_gF9oqdwpCHxepRqw'
CHANNEL_ID = -100356208428
bot = telebot.TeleBot(BOT_TOKEN)

light_status = None
light_change_time = None

print("🚀 Bot initialized")

@app.route('/', methods=['GET'])
def index():
    return {'status': 'ok'}, 200

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200

@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    print("📨 Telegram webhook received")
    try:
        json_data = request.get_json()
        print(f"Data: {json_data}")
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return {'ok': True}, 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return {'ok': False}, 500

@bot.message_handler(commands=['start'])
def start(message):
    print(f"Start command from {message.chat.id}")
    bot.reply_to(message, "🚀 Light Monitor Bot\n/status - статус світла")

@bot.message_handler(commands=['status'])
def status_command(message):
    global light_status, light_change_time
    print(f"Status command from {message.chat.id}")
    
    status_str = '💡 ВКЛ ✅' if light_status is True else ('🌑 ВИМКЛ ❌' if light_status is False else '❓ Невідомо')
    last_change_str = light_change_time.strftime('%H:%M:%S') if light_change_time else 'Ніколи'
    msg = f"📊 Світло: {status_str}\n⏰ Остання зміна: {last_change_str}"
    
    bot.reply_to(message, msg)

@app.route('/webhook', methods=['POST'])
def tuya_webhook():
    global light_status, light_change_time
    
    try:
        data = request.json
        print(f"📨 Tuya webhook: {data}")
        
        if data.get('bizCode') == 'statusReport':
            properties = data.get('data', {}).get('properties', [])
            
            for prop in properties:
                if prop.get('code') in ['switch', 'power', 'state', 'switch_1']:
                    is_light_on = bool(prop.get('value'))
                    current_time = datetime.now()
                    
                    if light_status != is_light_on:
                        light_status = is_light_on
                        light_change_time = current_time
                        
                        msg = f"✅ Світло вкл!" if is_light_on else f"❌ Світло вимкл!"
                        bot.send_message(CHANNEL_ID, msg)
                        print(f"💡 Light changed: {msg}")
                    
                    return {'code': 0}, 200
        
        return {'code': 0}, 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return {'code': -1}, 500

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Light Monitor Bot Starting")
    print(f"Bot Token: ✅")
    print(f"Channel ID: {CHANNEL_ID}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8080, debug=False)
