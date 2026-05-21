"""
src/notifier.py
Kirim signal ke Telegram.
"""

import os
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


def send_signal(prediction: dict, market_info: dict) -> bool:
    """
    Kirim signal ke Telegram.

    Args:
        prediction  : hasil dari predictor.predict()
        market_info : info market terbaru (harga, indikator)
    """
    token   = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logger.error("TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID tidak ada di .env")
        return False

    signal     = prediction["signal_name"]
    emoji      = prediction["emoji"]
    confidence = prediction["confidence"] * 100
    close      = market_info["close"]
    rsi        = market_info["rsi"]
    macd_hist  = market_info["macd_hist"]
    bb_pct     = market_info["bb_pct"]
    atr        = market_info["atr"]
    now        = datetime.now().strftime("%d %b %Y %H:%M WIB")

    # Analisis indikator
    rsi_status = "Overbought " if rsi > 70 else "Oversold " if rsi < 30 else "Normal "
    macd_status = "Bullish " if macd_hist > 0 else "Bearish "
    bb_status = "Upper Band " if bb_pct > 0.8 else "Lower Band " if bb_pct < 0.2 else "Middle "

    # Format pesan
    message = (
        f"📊 *XAUUSD Signal Update*\n"
        f"{now}\n"
        f"{'─'*30}\n"
        f"Signal     : {emoji} *{signal}*\n"
        f"Confidence : `{confidence:.1f}%`\n"
        f"Harga      : `${close:,.2f}`\n"
        f"{'─'*30}\n"
        f"*Indikator Teknikal*\n"
        f"RSI   : `{rsi:.1f}` — {rsi_status}\n"
        f"MACD  : {macd_status}\n"
        f"BB    : {bb_status}\n"
        f"ATR   : `{atr:.2f}` (volatilitas)\n"
        f"{'─'*30}\n"
        f"Prob SELL : `{prediction['prob_sell']*100:.1f}%`\n"
        f"Prob HOLD : `{prediction['prob_hold']*100:.1f}%`\n"
        f"Prob BUY  : `{prediction['prob_buy']*100:.1f}%`\n"
        f"{'─'*30}\n"
        f"⚠️ _Bukan saran investasi._\n"
        f"_Selalu gunakan risk management._"
    )

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, json={
            "chat_id"    : chat_id,
            "text"       : message,
            "parse_mode" : "Markdown"
        }, timeout=10)

        if resp.status_code == 200:
            logger.info(f"Signal terkirim: {signal} ({confidence:.1f}%)")
            return True
        else:
            logger.error(f"Telegram error: {resp.text}")
            return False

    except Exception as e:
        logger.error(f"Error kirim Telegram: {e}")
        return False


def send_startup_message() -> None:
    """Kirim notifikasi bot aktif."""
    token   = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return

    message = (
        "🤖 *XAUUSD AI Signal Bot Aktif!*\n\n"
        "Bot akan mengirim signal setiap jam.\n"
        "Signal: BUY | SELL | HOLD\n\n"
        "⚠️ _Gunakan sebagai referensi saja._"
    )
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={
            "chat_id"   : chat_id,
            "text"      : message,
            "parse_mode": "Markdown"
        }, timeout=10)
    except Exception:
        pass
