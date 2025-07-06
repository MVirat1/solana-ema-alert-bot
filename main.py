import requests
import pandas as pd
import asyncio
import os
from telegram import Bot
from keep_alive import keep_alive

# === CONFIG ===
TELEGRAM_TOKEN = "7577471609:AAEEqZH_zj3a0KugtsuTogSAycfj0FEFyzQ"
TELEGRAM_USER_ID = "843116130"
EMA_LENGTH = 40
THRESHOLD_PERCENT = 0.5  # ±0.5%
CHECK_INTERVAL_SECONDS = 60

bot = Bot(token=TELEGRAM_TOKEN)

def get_ohlcv(symbol="SOLUSDT", interval="1m", limit=50):
    url = f"https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print("❌ Binance API Error:", response.text)
        return None
    data = response.json()
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['close'] = pd.to_numeric(df['close'])
    return df

async def check_price_near_ema():
    df = get_ohlcv()
    if df is None:
        return

    df['ema'] = df['close'].ewm(span=EMA_LENGTH, adjust=False).mean()
    latest_price = df['close'].iloc[-1]
    latest_ema = df['ema'].iloc[-1]
    diff_percent = abs(latest_price - latest_ema) / latest_ema * 100

    print(f"Price: {latest_price:.2f}, EMA: {latest_ema:.2f}, Diff: {diff_percent:.2f}%")

    if diff_percent <= THRESHOLD_PERCENT:
        msg = (
            f"📈 *SOL/USDT Alert*\n"
            f"Price: {latest_price:.2f}\n"
            f"40 EMA: {latest_ema:.2f}\n"
            f"⚠️ Near EMA (±{THRESHOLD_PERCENT}%)"
        )
        await bot.send_message(chat_id=TELEGRAM_USER_ID, text=msg, parse_mode="Markdown")

async def main_loop():
    while True:
        await check_price_near_ema()
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    keep_alive()
    print("⏳ Bot started (checks every 60s)...")
    asyncio.run(main_loop())
