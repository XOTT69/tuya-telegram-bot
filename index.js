import express from "express";
import fetch from "node-fetch";

const app = express();

let lastPing = Date.now();
let isOnline = true;

const TELEGRAM_TOKEN = process.env.TELEGRAM_TOKEN;
const CHAT_ID = process.env.CHAT_ID;

function sendTelegram(text) {
  const url = `https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage?chat_id=${CHAT_ID}&text=${encodeURIComponent(text)}`;
  fetch(url).catch(() => {});
}

app.get("/ping", (req, res) => {
  lastPing = Date.now();

  if (!isOnline) {
    sendTelegram("⚡ Світло зʼявилось");
    isOnline = true;
  }

  res.send("OK");
});

setInterval(() => {
  if (Date.now() - lastPing > 120000 && isOnline) {
    sendTelegram("❌ Світло зникло");
    isOnline = false;
  }
}, 30000);

app.listen(process.env.PORT || 3000, () => {
  console.log("Server started");
});
