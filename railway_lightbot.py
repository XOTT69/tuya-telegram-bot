from flask import Flask, request
from datetime import datetime
import os
from telegram import Bot
from telegram.error import TelegramError

app = Flask(__name__)

# Конфіги
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '-1'))
bot = Bot(token=BOT_TOKEN)

# Зберігаємо час останньої зміни
light_status = None
light_change_time = None

def send_channel_message(message):
    """Відправляє повідомлення в Telegram канал"""
    try:
        bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode='Markdown')
        print(f"✅ Channel message sent: {message}")
    except TelegramError as e:
        print(f"❌ Telegram error: {e}")
    except Exception as e:
        print(f"❌ Error sending message: {e}")

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
            
            # Знаходимо статус світла
            for prop in properties:
                code = prop.get('code')
                value = prop.get('value')
                
                print(f"   Property {code}: {value}")
                
                # Перевіряємо різні можливі коди для світла
                if code in ['switch', 'power', 'state', 'switch_1', 'switch_led']:
                    is_light_on = bool(value)
                    current_time = datetime.now()
                    current_time_str = current_time.strftime('%H:%M:%S')
                    
                    print(f"💡 Light status: {'ON' if is_light_on else 'OFF'}")
                    
                    # Якщо статус змінився
                    if light_status != is_light_on:
                        # Якщо були дані раніше - рахуємо час
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
                        
                        # Оновлюємо статус
                        light_status = is_light_on
                        light_change_time = current_time
                        
                        # Відправляємо нове повідомлення
                        if light_status:
                            status_msg = f"✅ Світло з'явилося! 💡\n⏰ {current_time_str}"
                        else:
                            status_msg = f"❌ Світло зникло! 🌑\n⏰ {current_time_str}"
                        
                        print(f"Sending: {status_msg}")
                        send_channel_message(status_msg)
                    else:
                        print("⚠️  Status didn't change")
                    
                    return {'code': 0, 'msg': 'ok'}, 200
        
        print("⚠️  No statusReport found in webhook")
        return {'code': 0, 'msg': 'ok'}, 200
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {'code': -1, 'msg': str(e)}, 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    status_str = 'ON ✅' if light_status is True else ('OFF ❌' if light_status is False else 'UNKNOWN ❓')
    return {
        'status': 'ok',
        'light_status': status_str,
        'last_change': light_change_time.strftime('%Y-%m-%d %H:%M:%S') if light_change_time else 'Never'
    }, 200

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return {
        'name': 'Light Monitor Bot',
        'status': 'running',
        'version': '1.0',
        'endpoints': ['/webhook', '/health']
    }, 200

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Light Monitor Bot Starting...")
    print(f"Bot Token: {'✅ Set' if BOT_TOKEN else '❌ Not set'}")
    print(f"Channel ID: {CHANNEL_ID}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8080, debug=False)
