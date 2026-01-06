import time
import threading
import hmac
import hashlib
import json
import requests
import os

import telebot

# Tuya Cloud (з твоїх даних)
ACCESS_ID = os.getenv("TUYA_ACCESS_ID", "wu7fdvygqw7s353j4cvy")
ACCESS_KEY = os.getenv("TUYA_ACCESS_KEY", "e20b8ba7bcf440a0b0c31be29a06c4e7")
DEVICE_ID = os.getenv("TUYA_DEVICE_ID", "bfa671762a871e5405rvq4")
REGION = os.getenv("TUYA_REGION", "eu-central")

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "8599538983:AAFSIclFO9CSrK9GLf7-tp4qI3k0KYso7Ns")
CHAT_ID = int(os.getenv("CHAT_ID", "-1003562080428"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# Tuya Cloud API endpoints
CLOUD_BASE = "https://openapi.tuya.com.cn"  # для eu-central

print(f"[INIT] ACCESS_ID: {ACCESS_ID[:10]}...")
print(f"[INIT] DEVICE_ID: {DEVICE_ID}")
print(f"[INIT] REGION: {REGION}")
print(f"[INIT] BOT_TOKEN: {BOT_TOKEN[:20]}...")


def get_headers(method, path, body=""):
    """Генерує Tuya Cloud API headers з підписом."""
    timestamp = str(int(time.time() * 1000))
    sign_str = method + "\n" + path + "\n" + "" + "\n" + body
    sign = hmac.new(
        ACCESS_KEY.encode("utf-8"),
        sign_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest().upper()

    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "t": timestamp,
        "Content-Type": "application/json",
    }
    return headers


def get_device_status():
    """Читає статус пристрою з Cloud API."""
    path = f"/v1.0/devices/{DEVICE_ID}/status"
    method = "GET"
    
    try:
        headers = get_headers(method, path)
        url = CLOUD_BASE + path
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                dps = {}
                for item in data.get("result", []):
                    code = item.get("code")
                    value = item.get("value")
                    dps[code] = value
                print(f"[STATUS] DPS: {dps}")
                return dps.get("switch_1")  # True/False
        else:
            print(f"[ERROR] Status {resp.status_code}: {resp.text}")
        return None
    except Exception as e:
        print(f"[ERROR] get_device_status: {e}")
        return None


def set_device_switch(state: bool):
    """Уміцяє / вимикає розетку через Cloud API."""
    path = f"/v1.0/devices/{DEVICE_ID}/commands"
    method = "POST"
    body = json.dumps({"commands": [{"code": "switch_1", "value": state}]})
    
    try:
        headers = get_headers(method, path, body)
        url = CLOUD_BASE + path
        resp = requests.post(url, headers=headers, data=body, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            ok = data.get("success", False)
            print(f"[SET_SWITCH] {state}: {ok}")
            return ok
        else:
            print(f"[ERROR] Status {resp.status_code}: {resp.text}")
        return False
    except Exception as e:
        print(f"[ERROR] set_device_switch: {e}")
        return False


def format_duration(seconds: float) -> str:
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    parts = []
    if h:
        parts.append(f"{h} год")
    if m:
        parts.append(f"{m} хв")
    if s or not parts:
        parts.append(f"{s} с")
    return " ".join(parts)


@bot.message_handler(commands=["on"])
def cmd_on(message):
    ok = set_device_switch(True)
    text = "Розетку увімкнено ✅" if ok else "Не зміг увімкнути розетку ❌"
    bot.send_message(CHAT_ID, text)


@bot.message_handler(commands=["off"])
def cmd_off(message):
    ok = set_device_switch(False)
    text = "Розетку вимкнено ✅" if ok else "Не зміг вимкнути розетку ❌"
    bot.send_message(CHAT_ID, text)


@bot.message_handler(commands=["status"])
def cmd_status(message):
    st = get_device_status()
    if st is None:
        text = "Статус: помилка під'єднання до Cloud API ❌"
    else:
        text = f"Стан: {'ON' if st else 'OFF'}"
    bot.send_message(CHAT_ID, text)


def watch_power():
    print("[WATCH] WATCH THREAD STARTED (Cloud)")
    last_state = None
    none_count = 0
    last_off_ts = None

    while True:
        try:
            st = get_device_status()

            if st is None:
                none_count += 1
                print(f"[WATCH] state is None, count = {none_count}")
                if none_count >= 3 and last_state is not False:
                    last_state = False
                    last_off_ts = time.time()
                    bot.send_message(
                        CHAT_ID,
                        "Світло зникло ❌ (немає доступу до Cloud)",
                    )
            else:
                if none_count >= 3 and last_state is False and st:
                    if last_off_ts is not None:
                        dt = time.time() - last_off_ts
                        dur = format_duration(dt)
                        bot.send_message(
                            CHAT_ID,
                            f"Світло з'явилось ✅ (доступ відновлено, не було {dur})",
                        )
                    else:
                        bot.send_message(
                            CHAT_ID,
                            "Світло з'явилось ✅ (доступ відновлено)",
                        )

                none_count = 0

                if st != last_state:
                    print(f"[WATCH] state changed: {last_state} -> {st}")
                    if st is False:
                        last_off_ts = time.time()
                        bot.send_message(CHAT_ID, "Світло зникло ❌")
                    elif st is True and last_state is False and last_off_ts is not None:
                        dt = time.time() - last_off_ts
                        dur = format_duration(dt)
                        bot.send_message(
                            CHAT_ID,
                            f"Світло з'явилось ✅ (не було {dur})",
                        )
                        last_off_ts = None

                    last_state = st

        except Exception as e:
            print(f"[WATCH] ERROR: {e}")

        time.sleep(10)


if __name__ == "__main__":
    threading.Thread(target=watch_power, daemon=True).start()
    print("[MAIN] CLOUD BOT STARTED")
    bot.infinity_polling()
