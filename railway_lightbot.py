import telebot
import os
import logging
from threading import Thread
import time
from tuya_iot import TuyaOpenAPI, TuyaDevice
from tuya_iot.device import TuyaDeviceManager

# Конфіг
BOT_TOKEN = os.getenv('BOT_TOKEN')
TUYA_CLIENT_ID = os.getenv('TUYA_CLIENT_ID')
TUYA_CLIENT_SECRET = os.getenv('TUYA_CLIENT_SECRET')
TUYA_DEVICE_ID = os.getenv('TUYA_DEVICE_ID', 'bfa671762a871e5405rvq4')
TUYA_REGION = os.getenv('TUYA_REGION', 'eu')

bot = telebot.TeleBot(BOT_TOKEN)
api = None
device = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== ІНІЦІАЛІЗАЦІЯ API =====
def init_tuya_api():
    global api, device
    try:
        logger.info("[INIT] Initializing Tuya API...")
        api = TuyaOpenAPI(endpoint='https://openapi.tuya.com.cn', client_id=TUYA_CLIENT_ID, secret=TUYA_CLIENT_SECRET, region=TUYA_REGION)
        logger.info("[INIT] Tuya API initialized successfully")
        
        # Отримуємо інформацію про пристрій
        device_info = api.get(f'/v1.0/devices/{TUYA_DEVICE_ID}')
        logger.info(f"[INIT] Device info: {device_info}")
    except Exception as e:
        logger.error(f"[INIT] Failed to initialize API: {e}")
        api = None

# ===== КОНТРОЛЬ ПРИСТРОЮ =====
def turn_on():
    try:
        if api:
            commands = {'commands': [{'code': 'switch_led', 'value': True}]}
            result = api.post(f'/v1.0/devices/{TUYA_DEVICE_ID}/commands', commands)
            if result:
                logger.info("[ACTION] Light turned ON")
                return True
    except Exception as e:
        logger.error(f"[ERROR] turn_on failed: {e}")
    return False

def turn_off():
    try:
        if api:
            commands = {'commands': [{'code': 'switch_led', 'value': False}]}
            result = api.post(f'/v1.0/devices/{TUYA_DEVICE_ID}/commands', commands)
            if result:
                logger.info("[ACTION] Light turned OFF")
                return True
    except Exception as e:
        logger.error(f"[ERROR] turn_off failed: {e}")
    return False

def get_status():
    try:
        if api:
            result = api.get(f'/v1.0/devices/{TUYA_DEVICE_ID}/status')
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
    
    # Ініціалізація Tuya API
    init_tuya_api()
    
    # Запуск монітора
    monitor = Thread(target=watch_thread, daemon=True)
    monitor.start()
    
    logger.info("[MAIN] Bot polling started")
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"[ERROR] Bot error: {e}")
