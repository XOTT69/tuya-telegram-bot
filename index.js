const express = require("express");
const axios = require("axios");
const app = express();

const TOKEN = process.env.TG_TOKEN;
const CHAT_ID = process.env.TG_CHAT_ID;

let lastPing = Date.now();
let powerState = true;

function sendTelegram(text) {
  const url = `https://api.telegram.org/bot${TOKEN}/sendMessage`;
  return axios.post(url, {
    chat_id: CHAT_ID,
    text: text
  });
}

app.get("/ping", (req, res) => {
  const now = Date.now();

  if (!powerState) {
    const outage = now - lastPing;
    sendTelegram(`💡 Світло з'явилось\n⏱ Не було: ${Math.floor(outage / 60000)} хв`);
    powerState = true;
  }

  lastPing = now;
  res.send("OK");
});

setInterval(() => {
  const now = Date.now();
  if (powerState && now - lastPing > 60000) {
    powerState = false;
    sendTelegram("❌ Світло пропало");
  }
}, 10000);

app.listen(process.env.PORT || 3000, () => {
  console.log("Server started");
});
