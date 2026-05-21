import os
import sys
import logging
import schedule
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from src.data_fetcher import fetch_latest_data
from src.features     import get_latest_features
from src.predictor    import XAUUSDPredictor
from src.notifier     import send_signal, send_startup_message

CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.45"))
INTERVAL_MINUTES     = int(os.getenv("SIGNAL_INTERVAL_MINUTES", "60"))
MODEL_DIR            = os.getenv("MODEL_DIR", "models")

logger.info("Loading models...")
predictor = XAUUSDPredictor(model_dir=MODEL_DIR)
logger.info("Models loaded!")


# ─── Keep Alive ───────────────────────────────────────────────────
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, format, *args):
        pass

def run_keep_alive():
    server = HTTPServer(('0.0.0.0', 8080), KeepAliveHandler)
    server.serve_forever()


# ─── Signal Runner ────────────────────────────────────────────────
def run_signal():
    try:
        logger.info("="*50)
        logger.info("Running signal cycle...")
        df = fetch_latest_data()
        x_flat, x_seq, market_info = get_latest_features(df)
        prediction = predictor.predict(x_flat, x_seq)
        logger.info(f"Signal: {prediction['signal_name']} | Confidence: {prediction['confidence']:.2%} | Harga: ${market_info['close']:,.2f}")
        if prediction["confidence"] >= CONFIDENCE_THRESHOLD or prediction["signal"] != 1:
            send_signal(prediction, market_info)
        else:
            logger.info(f"Signal tidak dikirim — confidence rendah")
    except Exception as e:
        logger.error(f"Error di run_signal: {e}", exc_info=True)


# ─── Command Handlers ─────────────────────────────────────────────
async def cmd_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Menganalisis XAUUSD...")
    try:
        df = fetch_latest_data()
        x_flat, x_seq, market_info = get_latest_features(df)
        prediction = predictor.predict(x_flat, x_seq)
        send_signal(prediction, market_info)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def cmd_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        df = fetch_latest_data()
        price = df['Close'].iloc[-1]
        change = df['Close'].iloc[-1] - df['Close'].iloc[-2]
        pct = change / df['Close'].iloc[-2] * 100
        arrow = "📈" if change >= 0 else "📉"
        await update.message.reply_text(
            f"{arrow} *Harga XAUUSD Terkini*\n\n"
            f"Harga  : `${price:,.2f}`\n"
            f"Perubahan: `{change:+.2f} ({pct:+.2f}%)`",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def cmd_analisis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Menghitung indikator...")
    try:
        df = fetch_latest_data()
        _, _, info = get_latest_features(df)
        rsi = info['rsi']
        rsi_status = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Normal"
        macd_status = "Bullish" if info['macd_hist'] > 0 else "Bearish"
        await update.message.reply_text(
            f"📊 *Analisis Teknikal XAUUSD*\n\n"
            f"Harga  : `${info['close']:,.2f}`\n"
            f"EMA 9  : `${info['ema_9']:,.2f}`\n"
            f"EMA 21 : `${info['ema_21']:,.2f}`\n"
            f"RSI    : `{rsi:.1f}` — {rsi_status}\n"
            f"MACD   : {macd_status}\n"
            f"ATR    : `{info['atr']:.2f}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*XAUUSD AI Signal Bot*\n\n"
        "Perintah yang tersedia:\n"
        "/signal — Prediksi signal sekarang\n"
        "/price — Harga XAUUSD terkini\n"
        "/analisis — Indikator teknikal\n"
        "/help — Tampilkan bantuan ini",
        parse_mode="Markdown"
    )


# ─── Main ─────────────────────────────────────────────────────────
def main():
    # 1. Start keep-alive PERTAMA
    ka_thread = threading.Thread(target=run_keep_alive, daemon=True)
    ka_thread.start()
    logger.info("Keep-alive server running on port 8080")

    logger.info(f"Interval   : setiap {INTERVAL_MINUTES} menit")
    logger.info(f"Confidence : minimal {CONFIDENCE_THRESHOLD:.0%}")

    send_startup_message()

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("signal",   cmd_signal))
    app.add_handler(CommandHandler("price",    cmd_price))
    app.add_handler(CommandHandler("analisis", cmd_analisis))
    app.add_handler(CommandHandler("help",     cmd_help))

    # Scheduler di background
    def run_scheduler():
        run_signal()
        schedule.every(INTERVAL_MINUTES).minutes.do(run_signal)
        while True:
            schedule.run_pending()
            time.sleep(30)

    sched_thread = threading.Thread(target=run_scheduler, daemon=True)
    sched_thread.start()

    logger.info("Bot siap menerima perintah!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()