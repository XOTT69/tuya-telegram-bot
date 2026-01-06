import telebot
import os
import logging
from threading import Thread
import time
import hmac
import hashlib
import json
import requests
from datetime import datetime

# Конфіг
BOT_TOKEN = os.getenv('BOT_TOKEN')
TUYA_CLIENT_ID = os.getenv('TUYA_CLIENT_ID')
TUYA_CLIENT_SECRET = os.getenv('TUYA_CLIENT_SECRET')
TUYA_DEVICE_ID = os.getenv('TUYA_DEVICE_ID', 'bfa671762a871e5405rvq4')
TUYA_REGION = os.getenv('TUYA_REGION', 'eu')

# Tuya endpoints
TUYA_HOST = f'https://openapi.tuya{".com" if TUYA_REGION == "us" else ".com.cn" if TUYA_REGION == "eu" else "-iot.tuya.com"}'
TUYA_STATUS_URL = f'{TUYA_HOST}/v1.0/devices/{TUYA_DEVICE_ID}/status'
TUYA_COMMAND_URL = f'{TUYA_HOST}/v1.0/devices/{TUYA_DEVICE_ID}/commands'

bot = telebot.TeleBot(BOT_TOKEN)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== TUYA API HELPER =====
def get_tuya_headers(method, path, body=''):
    """Генеруємо Tuya API headers з підписом"""
    timestamp = str(int(time.time() * 1000))
    
    # Формуємо рядок для підпису
    sign_str = method + '\n' + path + '\n' + '' + '\n' + timestamp
    
    if body:
        sign_str += '\n' + body
    
    # SHA256 HMAC підпис
    signature = hmac.new(
        TUYA_CLIENT_SECRET.encode(),
        sign_str.encode(),
        hashlib.sha256
    ).hexdigest().upper()
    
    return {
        'client_id': TUYA_CLIENT_ID,
        'sign': signature,
        't': timestamp,
        'sign_method': 'HMAC-SHA256',
        'Content-Type': 'application/json'
    }

def turn_on():
    try:
        body = json.dumps({'commands': [{'code': 'switch_led', 'value': True}]})
        headers = get_tuya_headers('POST', f'/v1.0/devices/{TUYA_DEVICE_ID}/commands', body)
        
        response = requests.post(
            TUYA_COMMAND_URL,
            headers=headers,
            data=body,
            timeout=15
        )
        
        if response.status_code == 200:
            logger.info("[ACTION] Light turned ON")
            return True
        else:
            logger.error(f"[ERROR] Tuya API returned {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"[ERROR] turn_on failed: {e}")
    return False

def turn_off():
    try:
        body = json.dumps({'commands': [{'code': 'switch_led', 'value': False}]})
        headers = get_tuya_headers('POST', f'/v1.0/devices/{TUYA_DEVICE_ID}/commands', body)
        
        response = requests.post(
            TUYA_COMMAND_URL,
            headers=headers,
            data=body,
            timeout=15
        )
        
        if response.status_code == 200:
            logger.info("[ACTION] Light turned OFF")
            return True
        else:
            logger.error(f"[ERROR] Tuya API returned {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"[ERROR] turn_off failed: {e}")
    return False

def get_status():
    try:
        headers = get_tuya_headers('GET', f'/v1.0/devices/{TUYA_DEVICE_ID}/status')
        
        response = requests.get(
            TUYA_STATUS_URL,
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"[STATUS] Device state: {data}")
            return data
        else:
            logger.error(f"[ERROR] Tuya API returned {response.status_code}: {response.text}")
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
        bot.reply_to(message, f"📊 Status: {state}")
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
            time.sleep(60)  # Кожну хвилину
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
    bot.infinity_polling()
