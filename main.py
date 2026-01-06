import requests
import time
from telegram import Bot
import asyncio

TOKEN = '8599538983:AAFSIclFO9CSrK9GLf7-tp4qI3k0KYso7Ns'
CHAT_ID = '-1003562080428'
TUYA_CLIENT_ID = 'wu7fdvygqw7s353j4cvy'
TUYA_CLIENT_SECRET = 'e20b8ba7bcf440a0b0c31be29a06c4e7'
DEVICE_ID = 'bfa671762a871e5405rvq4'

bot = Bot(token=TOKEN)

def get_tuya_token():
    ts = str(int(time.time()))
    sign_str = f"GET\n/v1.0/token?grant_type=1\n\n{ts}"
    signature = hmac_sha256(sign_str, TUYA_CLIENT_SECRET)
    headers = {
        'client_id': TUYA_CLIENT_ID,
        't': ts,
        'sign': signature,
        'sign_method': 'HMAC-SHA256'
    }
    r = requests.get('https://openapi.tuya.com/v1.0/token?grant_type=1', headers=headers)
    return r.json()['result']['access_token']

def get_device_status(token):
    ts = str(int(time.time()))
    sign_str = f"GET\n/v1.0/devices/{DEVICE_ID}\n\n{ts}"
    signature = hmac_sha256(sign_str, TUYA_CLIENT_SECRET)
    headers = {
        'Authorization': f'Bearer {token}',
        't': ts,
        'sign': signature
    }
    r = requests.get(f'https://openapi.tuya.com/v1.0/devices/{DEVICE_ID}', headers=headers)
    return r.json()['result']

def hmac_sha256(message, secret):
    import hmac
    import hashlib
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

async def main():
    while True:
        try:
            token = get_tuya_token()
            device = get_device_status(token)
            is_on = device['dps']['1']
            power = device['dps']['17']
            msg = f"✅ СВІТЛО Є ({power}W)" if is_on else "🔴 СВІТЛО НЕМА"
            await bot.send_message(CHAT_ID, msg)
            print(msg)
        except Exception as e:
            print(f"Error: {e}")
        await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main())
