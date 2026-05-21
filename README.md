# 📊 XAUUSD AI Signal Bot — Tahap 3: Inference

Bot Telegram yang kirim signal BUY/SELL/HOLD XAUUSD secara real-time setiap jam.

---

## 📁 Struktur Project

```
xauusd-inference/
├── bot.py                  # ▶ Entry point utama
├── requirements.txt
├── .env.example            # Template environment variables
├── models/                 # ← Ekstrak xauusd_models.zip ke sini
│   ├── xgb_model.joblib
│   ├── lstm_model.keras
│   ├── scaler.joblib
│   └── metadata.json
├── src/
│   ├── data_fetcher.py     # Fetch data real-time
│   ├── features.py         # Hitung indikator teknikal
│   ├── predictor.py        # Ensemble XGBoost + LSTM
│   └── notifier.py         # Kirim ke Telegram
└── logs/                   # Log otomatis
```

---

## ⚡ Setup

### 1. Ekstrak model
```
Ekstrak xauusd_models.zip → copy semua isi ke folder models/
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup .env
```bash
cp .env.example .env
```

Isi file `.env`:
```
TELEGRAM_BOT_TOKEN=token_dari_botfather
TELEGRAM_CHAT_ID=chat_id_kamu
SIGNAL_INTERVAL_MINUTES=60
CONFIDENCE_THRESHOLD=0.45
```

### 4. Cara dapat TELEGRAM_CHAT_ID
```
1. Buka Telegram
2. Cari @userinfobot
3. Kirim pesan apa saja
4. Bot akan balas dengan ID kamu
```

### 5. Jalankan
```bash
python bot.py
```

---

## 📱 Contoh Signal di Telegram

```
📊 XAUUSD Signal Update
🕐 21 May 2026 15:00 WIB
──────────────────────────────
Signal     : 🟢 BUY
Confidence : 67.3%
Harga      : $4,513.40
──────────────────────────────
📈 Indikator Teknikal
RSI   : 58.2 — Normal ✅
MACD  : Bullish 📈
BB    : Middle ⚪
ATR   : 12.50 (volatilitas)
──────────────────────────────
⚠️ Bukan saran investasi.
```

---

## 🔜 Deploy 24/7 (Oracle Cloud Free)

```bash
# Install PM2
npm install -g pm2

# Jalankan bot
pm2 start bot.py --interpreter python3 --name "xauusd-bot"

# Auto-start saat reboot
pm2 startup
pm2 save
```
