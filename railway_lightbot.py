import telebot
import os
import logging
from threading import Thread
import time
import requests
import hmac
import hashlib
import json

# Конфіг
BOT_TOKEN = os.getenv('BOT_TOKEN')
TUYA_CLIENT_ID = os.getenv('TUYA_CLIENT_ID')
TUYA_CLIENT_SECRET = os.getenv('TUYA_CLIENT_SECRET')
TUYA_DEVICE_ID = os.getenv('TUYA_DEVICE_ID', 'bfa671762a871e5405rvq4')
TUYA_REGION = os.getenv('TUYA_REGION', 'eu')

bot = telebot.TeleBot(BOT_TOKEN)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== TUYA API HELPER (ПРАВИЛЬНА) =====
def get_tuya_sign(method, path, body=''):
    """Генеруємо правильний підпис для Tuya API"""
    timestamp = str(int(time.time() * 1000))
    
    # Рядок для підпису
    if body:
        string_to_sign = method + '\n' + path + '\n' + body + '\n' + timestamp
    else:
        string_to_sign = method + '\n' + path + '\n' + '' + '\n' + timestamp
    
    # HMAC-SHA256 підпис
    sign = hmac.new(
        TUYA_CLIENT_SECRET.encode(),
        string_to_sign.encode(),
        hashlib.sha256
    ).hexdigest().upper()
    
    return sign, timestamp

def call_tuya_api(method, path, body=None):
    """Викликаємо Tuya API з правильною аутентифікацією"""
    try:
        sign, timestamp = get_tuya_sign(method, path, json.dumps(body) if body else '')
        
        headers = {
            'client_id': TUYA_CLIENT_ID,
            'sign': sign,
            't': timestamp,
            'sign_method': 'HMAC-SHA256',
            'Content-Type': 'application/json'
        }
        
        url = f'https://openapi.tuya.com.cn{path}'
        
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=15)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=body, timeout=15)
        else:
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"[TUYA] Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"[TUYA] API call failed: {e}")
        return None

# ===== КОНТРОЛЬ ПРИСТРОЮ =====
def turn_on():
    try:
        body = {'commands': [{'code': 'switch_led', 'value': True}]}
        result = call_tuya_api('POST', f'/v1.0/devices/{TUYA_DEVICE_ID}/commands', body)
        if result and result.get('success'):
            logger.info("[ACTION] Light turned ON")
            return True
    except Exception as e:
        logger.error(f"[ERROR] turn_on failed: {e}")
    return False

def turn_off():
    try:
        body = {'commands': [{'code': 'switch_led', 'value': False}]}
        result = call_tuya_api('POST', f'/v1.0/devices/{TUYA_DEVICE_ID}/commands', body)
        if result and result.get('success'):
            logger.info("[ACTION] Light turned OFF")
            return True
    except Exception as e:
        logger.error(f"[ERROR] turn_off failed: {e}")
    return False

def get_status():
    try:
        result = call_tuya_api('GET', f'/v1.0/devices/{TUYA_DEVICE_ID}/status')
        if result and result.get('success'):
            logger.info(f"[STATUS] Device state: {result}")
            return result
    except Exception as e:
        logger.error(f"[ERROR] get_status failed: {e}")
    return None

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
    if turn_on():
        bot.reply_to(message, "💡 Light is ON")
    else:
        bot.reply_to(message, "❌ Failed to turn on")

@bot.message_handler(commands=['off'])
def handle_off(message):
    if turn_off():
        bot.reply_to(message, "💡 Light is OFF")
    else:
        bot.reply_to(message, "❌ Failed to turn off")

@bot.message_handler(commands=['status'])
def handle_status(message):
    state = get_status()
    if state:
        data = state.get('data', {})
        bot.reply_to(message, f"📊 Status: {data}")
    else:
        bot.reply_to(message, "❌ Cannot get status")

# ===== ФОНОВИЙ МОНІТОР =====
def watch_thread():
    logger.info("[WATCH] Watch thread started")
    count = 0
    while True:
        try:
            count += 1
            state = get_status()
            if state:
                logger.info(f"[WATCH] Status check #{count}: OK")
            time.sleep(60)
        except Exception as e:
            logger.error(f"[WATCH] Error: {e}")
            time.sleep(60)

# ===== MAIN =====
if __name__ == '__main__':
    logger.info("[INIT] Bot starting...")
    logger.info(f"[INIT] BOT_TOKEN: {BOT_TOKEN[:20]}...")
    logger.info(f"[INIT] TUYA_CLIENT_ID: {TUYA_CLIENT_ID}")
    logger.info(f"[INIT] TUYA_REGION: {TUYA_REGION}")
    logger.info(f"[INIT] TUYA_DEVICE_ID: {TUYA_DEVICE_ID}")
    
    # Запуск монітора
    monitor = Thread(target=watch_thread, daemon=True)
    monitor.start()
    
    logger.info("[MAIN] Bot polling started")
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"[ERROR] Bot error: {e}")
