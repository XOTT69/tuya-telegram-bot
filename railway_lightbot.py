from flask import Flask, request
from datetime import datetime
import os
import telebot
import traceback

app = Flask(__name__)

# ВИКОРИСТАЙТЕ ЗМІННІ ОТОЧЕННЯ НА RAILWAY!
BOT_TOKEN = os.getenv('BOT_TOKEN', '8537850530:AAGyzyYAz4Bx25iPt2_gF9oqdwpCHxepRqw')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '-100356208428'))

bot = telebot.TeleBot(BOT_TOKEN)
light_status = None
light_change_time = None

print("🚀 Bot initialized")

@app.route('/', methods=['GET'])
def index():
    return {'status': 'ok', 'light': light_status}, 200

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200

@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    print("🚀 TELEGRAM WEBHOOK HIT")
    try:
        json_string = request.get_data(as_text=True)
        print(f"📄 RAW JSON: {json_string[:300]}...")
        
        update = telebot.types.Update.de_json(json_string)
        if update and update.message:
            print(f"✅ UPDATE: chat_id={update.message.chat.id}, text='{update.message.text}'")
            bot.process_new_updates([update])
            print("🔄 Handlers processed")
        else:
            print("❌ No valid update.message")
        
        return '', 200
    except Exception as e:
        print(f"💥 ERROR: {e}\n{traceback.format_exc()}")
        return '', 500

@bot.message_handler(commands=['start'])
def start(message):
    print(f"🎉 START: chat_id={message.chat.id}")
    bot.reply_to(message, "🚀 Light Monitor Bot ✅\n/status - статус світла")

@bot.message_handler(commands=['status'])
def status_command(message):
    global light_status, light_change_time
    print(f"📊 STATUS: chat_id={message.chat.id}")
    
    if light_status is True:
        status_str = '💡 ВКЛ ✅'
    elif light_status is False:
        status_str = '🌑 ВИМКЛ ❌'
    else:
        status_str = '❓ Невідомо'
    
    last_change_str = light_change_time.strftime('%d.%m %H:%M:%S') if light_change_time else 'Ніколи'
    msg = f"📊 Світло: {status_str}\n⏰ Остання зміна: {last_change_str}"
    
    bot.reply_to(message, msg)

@app.route('/webhook', methods=['POST'])  # Tuya webhook
def tuya_webhook():
    global light_status, light_change_time
    print("🏠 TUYA WEBHOOK")
    
    try:
        data = request.json
        print(f"Tuya data: {data}")
        
        if data.get('bizCode') == 'statusReport':
            properties = data.get('data', {}).get('properties', [])
            for prop in properties:
                code = prop.get('code')
                if code in ['switch', 'power', 'state', 'switch_1']:
                    is_on = bool(prop.get('value'))
                    now = datetime.now()
                    
                    if light_status != is_on:
                        light_status = is_on
                        light_change_time = now
                        msg = f"💡 Світло УВІМКНУТО!" if is_on else f"🌑 Світло ВИМКНУТО!"
                        bot.send_message(CHANNEL_ID, f"{msg}\n⏰ {now.strftime('%H:%M:%S')}")
                        print(f"🔔 STATUS CHANGED: {msg}")
                    
                    return {'code': 0}, 200
        
        return {'code': 0}, 200
    except Exception as e:
        print(f"Tuya error: {e}")
        return {'code': -1}, 500

if __name__ == '__main__':
    print("🚀 Starting Light Monitor Bot")
    print(f"Channel: {CHANNEL_ID}")
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)), debug=False)
