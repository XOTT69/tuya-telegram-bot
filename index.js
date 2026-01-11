const express = require("express");
const axios = require("axios");
const app = express();

const TOKEN = process.env.TG_TOKEN;
const CHAT_ID = process.env.TG_CHAT_ID;

let lastPing = Date.now();
let powerState = true;              // зараз світло є
let lastPowerOnTime = Date.now();   // коли востаннє з’явилось світло

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

// Пінг від ESP32
app.get("/ping", (req, res) => {
  const now = Date.now();

  // Якщо до цього було "світла нема", а тепер пінг прийшов → світло з’явилось
  if (!powerState) {
    const outage = now - lastPing;

    sendTelegram(
      `💡 Світло з'явилось\n` +
      `⏱ Не було: ${formatTime(outage)}`
    );

    powerState = true;
    lastPowerOnTime = now;
  }

  lastPing = now;
  res.send("OK");
});

// Перевірка, чи реально пропало світло
setInterval(() => {
  const now = Date.now();

  /*
    ESP пінгує раз у 30 сек.
    90 сек = пропущено 3 пінги підряд → це вже не глюк Wi-Fi, а реальне вимкнення.
  */
  if (powerState && now - lastPing > 120000) {
    powerState = false;

    const worked = now - lastPowerOnTime;
    const timeStr = getTimeStr();

    sendTelegram(
      `🔴 ${timeStr} Світло зникло\n` +
      `🕓 Воно було ${formatTime(worked)}`
    );
  }
}, 5000); // перевіряємо кожні 5 секунд

app.listen(process.env.PORT || 3000, () => {
  console.log("Server started");
});
