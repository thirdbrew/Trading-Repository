import setup
import pandas as pd
import pandas_ta_classic as ta
from oandapyV20 import API
from datetime import datetime, timezone
import time
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.orders as orders

client = API(access_token=setup.OANDA_API_KEY, environment="live")

#Variables for the instrument and timeframe
timeframe = "M1"
instrument = "EUR_USD"

def get_candles(tf):
    params = {
        "granularity": tf,
        "price": "A" #Ask price
    }

    r = instruments.InstrumentsCandles(instrument=instrument, params=params)
    candles = client.request(r)['candles']

    data =[] 
    for c in candles:
        if c['complete']:
            data.append({
                "time": c['time'],
                "open": c['ask']['o'],
                "high": c['ask']['h'],
                "low": c['ask']['l'],
                "close": c['ask']['c']
            })

    df = pd.DataFrame(data)
    df['time'] = pd.to_datetime(df['time'])
    return df

def calculate_indicators(df):
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # EMA
    df["EMA_5"] = df["close"].ewm(span=5, adjust=False).mean()
    df["EMA_8"] = df["close"].ewm(span=8, adjust=False).mean()

    # ATR - stop loss
    prev_close = df["close"].shift(1)
    true_range = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    df["ATR_14"] = true_range.rolling(window=14).mean()

    return df

#Place and order
def place_order(stop_loss, take_profit):
    print(f"Placing order with stop loss: {stop_loss} and take profit: {take_profit}")
    data = {
        "order": {
            "instrument": instrument,
            "units": "100",  # Buy 100 units
            "type": "MARKET",
            "stopLossOnFill": {"price": stop_loss},
            "takeProfitOnFill": {"price": take_profit}
        }
    }
    r = orders.OrderCreate(setup.OANDA_ACCOUNT_ID, data=data)
    client.request(r)

def ema_crossover(df):
    tp_ratio = 1.5

    #Check if crossover
    last_candle = df.iloc[-1]
    prev_candle = df.iloc[-2]

    if last_candle["EMA_5"] > last_candle["EMA_8"] and prev_candle["EMA_5"] < prev_candle["EMA_8"]:
        print("Buy singal: EMA crossover")
        entry_price = last_candle["close"]
        stop_loss = entry_price - last_candle["ATR_14"]
        stop_distance = entry_price - stop_loss
        take_profit = entry_price + (stop_distance * tp_ratio)
        place_order(stop_loss, take_profit)
    else:
        print("No crossover")

def run_bot():
    print("Starting trading bot...")
    price = get_candles(timeframe)
    price = calculate_indicators(price)
    ema_crossover(price)

def run_bot_continuously():
    last_checked = None
    while True:
        current_time = datetime.now(timezone.utc)
        if current_time.second < 10:
            if last_checked != current_time.minute:
                print("Checking for trade signals")
                price = get_candles(timeframe)
                price = calculate_indicators(price)
                ema_crossover(price)
                last_checked = current_time.minute
        time.sleep(1)

run_bot_continuously()