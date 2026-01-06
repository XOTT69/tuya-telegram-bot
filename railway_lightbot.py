from flask import Flask, request
from datetime import datetime
import os
import telebot
from telebot.apihelper import ApiException

app = Flask(__name__)

# Конфіги
BOT_TOKEN = os.getenv('BOT_TOKEN', '8537850530:AAGyzyYAz4Bx25iPt2_gF9oqdwpCHxepRqw')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '-1'))
bot = telebot.TeleBot(BOT_TOKEN)

# Зберігаємо час останньої зміни
light_status = None
light_change_time = None

def send_channel_message(message):
    """Відправляє повідомлення в Telegram канал"""
    try:
        bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode='Markdown')
        print(f"✅ Channel message sent: {message}")
    except Exception as e:
        print(f"❌ Error sending message: {e}")

# ===== TELEGRAM COMMANDS =====
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 Light Monitor Bot\nВикористовуй /status для перевірки світла")

@bot.message_handler(commands=['status'])
def status_command(message):
    global light_status, light_change_time
    
    status_str = '💡 Світло ВКЛ ✅' if light_status is True else ('🌑 Світло ВИМКЛ ❌' if light_status is False else '❓ Невідомо')
    last_change_str = light_change_time.strftime('%H:%M:%S') if light_change_time else 'Ніколи'
    
    msg = f"📊 Light Status:\n{status_str}\n⏰ Остання зміна: {last_change_str}"
    bot.reply_to(message, msg)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.reply_to(message, "Я бот для контролю світла. Використовуй /status або /start")

# ===== FLASK WEBHOOKS =====
@app.route('/webhook', methods=['POST'])
def webhook():
    global light_status, light_change_time
    
    try:
        data = request.json
        print(f"\n📨 Webhook received at {datetime.now()}")
        print(f"Data: {data}\n")
        
        if data.get('bizCode') == 'statusReport':
            device_data = data.get('data', {})
            device_id = device_data.get('deviceId')
            properties = device_data.get('properties', [])
            
            print(f"🔌 Device ID: {device_id}")
            
            for prop in properties:
                code = prop.get('code')
                value = prop.get('value')
                
                print(f"   Property {code}: {value}")
                
                if code in ['switch', 'power', 'state', 'switch_1', 'switch_led']:
                    is_light_on = bool(value)
                    current_time = datetime.now()
                    current_time_str = current_time.strftime('%H:%M:%S')
                    
                    print(f"💡 Light status: {'ON' if is_light_on else 'OFF'}")
                    
                    if light_status != is_light_on:
                        if light_change_time is not None:
                            duration = current_time - light_change_time
                            hours = int(duration.total_seconds() // 3600)
                            minutes = int((duration.total_seconds() % 3600) // 60)
                            seconds = int(duration.total_seconds() % 60)
                            
                            time_str = f"{hours}ч {minutes}м {seconds}с" if hours > 0 else f"{minutes}м {seconds}с"
                            
                            if light_status is True:
                                duration_msg = f"💡 Світло було {time_str}\n⏰ {light_change_time.strftime('%H:%M:%S')} - {current_time_str}"
                            else:
                                duration_msg = f"🌑 Без світла було {time_str}\n⏰ {light_change_time.strftime('%H:%M:%S')} - {current_time_str}"
                            
                            print(f"Sending: {duration_msg}")
                            send_channel_message(duration_msg)
                        
                        light_status = is_light_on
                        light_change_time = current_time
                        
                        if light_status:
                            status_msg = f"✅ Світло з'явилося! 💡\n⏰ {current_time_str}"
                        else:
                            status_msg = f"❌ Світло зникло! 🌑\n⏰ {current_time_str}"
                        
                        print(f"Sending: {status_msg}")
                        send_channel_message(status_msg)
                    
                    return {'code': 0, 'msg': 'ok'}, 200
        
        return {'code': 0, 'msg': 'ok'}, 200
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {'code': -1, 'msg': str(e)}, 500

@app.route('/health', methods=['GET'])
def health():
    status_str = 'ON ✅' if light_status is True else ('OFF ❌' if light_status is False else 'UNKNOWN ❓')
    return {
        'status': 'ok',
        'light_status': status_str,
        'last_change': light_change_time.strftime('%Y-%m-%d %H:%M:%S') if light_change_time else 'Never'
    }, 200

@app.route('/', methods=['GET'])
def index():
    return {
        'name': 'Light Monitor Bot',
        'status': 'running',
        'version': '1.0',
        'endpoints': ['/webhook', '/health']
    }, 200

# ===== START =====
if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Light Monitor Bot Starting...")
    print(f"Bot Token: ✅ Set")
    print(f"Channel ID: {CHANNEL_ID}")
    print("=" * 50)
    
    # Flask для Tuya webhook
    app.run(host='0.0.0.0', port=8080, debug=False)
