import requests
import time
import hmac
import hashlib
import asyncio
from telegram import Bot

TOKEN = '8599538983:AAFSIclFO9CSrK9GLf7-tp4qI3k0KYso7Ns'
CHAT_ID = '-1003562080428'
TUYA_CLIENT_ID = 'wu7fdvygqw7s353j4cvy'
TUYA_CLIENT_SECRET = 'e20b8ba7bcf440a0b0c31be29a06c4e7'
DEVICE_ID = 'bfa671762a871e5405rvq4'

bot = Bot(token=TOKEN)

def hmac_sha256(message, secret):
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

def get_tuya_token():
    ts = str(int(time.time() * 1000))
    sign_str = f"GET\n/v1.0/token?grant_type=1\n\n{ts}"
    signature = hmac_sha256(sign_str, TUYA_CLIENT_SECRET)
    headers = {
        'client_id': TUYA_CLIENT_ID,
        't': ts,
        'sign': signature,
        'sign_method': 'HMAC-SHA256'
    }
    r = requests.get('https://openapi.tuya.com/v1.0/token?grant_type=1', headers=headers)
    data = r.json()
    if data.get('success'):
        return data['result']['access_token']
    raise Exception(f"Tuya token error: {data.get('msg', 'Unknown')}")

def get_device_status(token):
    ts = str(int(time.time() * 1000))
    sign_str = f"GET\n/v1.0/devices/{DEVICE_ID}\n\n{ts}"
    signature = hmac_sha256(sign_str, TUYA_CLIENT_SECRET)
    headers = {
        'Authorization': f'Bearer {token}',
        't': ts,
        'sign': signature
    }
    r = requests.get(f'https://openapi.tuya.com/v1.0/devices/{DEVICE_ID}', headers=headers)
    data = r.json()
    if data.get('success'):
        return data['result']
    raise Exception(f"Device error: {data.get('msg', 'Unknown')}")

async def main():
    print("🚀 Tuya Telegram Bot запущено!")
    while True:
        try:
            token = get_tuya_token()
            device = get_device_status(token)
            dps = device.get('dps', {})
            is_on = dps.get('1', False)
            power = dps.get('17', 0)
            voltage = dps.get('20', 0)
            online = device.get('online', False)
            
            status = "✅ СВІТЛО Є" if is_on else "🔴 СВІТЛО НЕМА"
            power_info = f"{power}W | {voltage}V" if is_on else ""
            online_status = "🟢 ОНЛАЙН" if online else "🔴 ОФЛАЙН"
            
            msg = f"{status}\n{power_info}\n{online_status}"
            
            await bot.send_message(CHAT_ID, msg)
            print(f"[{time.strftime('%H:%M:%S')}] Відправлено: {msg}")
        except Exception as e:
            print(f"❌ Error: {e}")
            await bot.send_message(CHAT_ID, f"⚠️ Помилка: {str(e)}")
        
        await asyncio.sleep(60)  # кожну хвилину

if __name__ == '__main__':
    asyncio.run(main())
