const express = require("express");
const axios = require("axios");
const app = express();

const TOKEN = process.env.TG_TOKEN;
const CHAT_ID = process.env.TG_CHAT_ID;

// Час останнього пінгу від ESP
let lastPing = Date.now();

// true = світло є, false = світла нема
let powerState = true;

// Реальний момент, коли світло востаннє з’явилось
let lastRealPowerOnTime = Date.now();

function sendTelegram(text) {
  return axios.post(`https://api.telegram.org/bot${TOKEN}/sendMessage`, {
    chat_id: CHAT_ID,
    text: text
  });
}

function formatTime(ms) {
  const hours = Math.floor(ms / 3600000);
  const minutes = Math.floor((ms % 3600000) / 60000);

  if (hours > 0) {
    return `${hours} год ${minutes} хв`;
  } else {
    return `${minutes} хв`;
  }
}

function getTimeStr() {
  return new Date().toLocaleTimeString("uk-UA", {
    hour: "2-digit",
    minute: "2-digit"
  });
}

// ---------- ПІНГ ВІД ESP32 ----------
app.get("/ping", (req, res) => {
  const now = Date.now();

  // Якщо до цього світла не було, а тепер пінг прийшов → світло з’явилось
  if (!powerState) {
    const outage = now - lastPing;

    sendTelegram(
      `💡 Світло з'явилось\n` +
      `⏱ Не було: ${formatTime(outage)}`
    );

    powerState = true;
    lastRealPowerOnTime = now; // фіксуємо реальний момент включення
  }

  lastPing = now;
  res.send("OK");
});

// ---------- ПЕРЕВІРКА ЗНИКНЕННЯ СВІТЛА ----------
setInterval(() => {
  const now = Date.now();

  /*
    ESP пінгує раз у 30 сек.
    120 сек = пропущено 4 пінги підряд.
    Це вважаємо реальним зникненням світла.
  */
  if (powerState && now - lastPing > 120000) {
    powerState = false;

    const worked = now - lastRealPowerOnTime;
    const timeStr = getTimeStr();

    sendTelegram(
      `🔴 ${timeStr} Світло зникло\n` +
      `🕓 Воно було ${formatTime(worked)}`
    );
  }
}, 5000); // перевірка кожні 5 секунд

app.listen(process.env.PORT || 3000, () => {
  console.log("Server started");
});
