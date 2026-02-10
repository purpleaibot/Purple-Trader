import pandas as pd
import pandas_ta as ta
from sqlalchemy import desc
from core.database import SessionLocal, Candle
import logging

logger = logging.getLogger(__name__)

def get_candles_df(symbol, interval, limit=500):
    """Fetch candles from DB and return as DataFrame."""
    session = SessionLocal()
    try:
        # Fetch in descending order (newest first) then reverse for TA
        candles = session.query(Candle).filter_by(symbol=symbol, interval=interval)\
            .order_by(desc(Candle.timestamp)).limit(limit).all()
        
        if not candles:
            return pd.DataFrame()

        data = [{
            'timestamp': c.timestamp,
            'open': c.open,
            'high': c.high,
            'low': c.low,
            'close': c.close,
            'volume': c.volume
        } for c in candles]
        
        df = pd.DataFrame(data)
        df = df.sort_values('timestamp').reset_index(drop=True)
        return df
    finally:
        session.close()

def calculate_trend(df):
    """
    Daily Trend: Bullish if Price > EMA 200.
    """
    if df.empty or len(df) < 200:
        return "NEUTRAL"

    df.ta.ema(length=200, append=True)
    # Check last closed candle
    last_close = df['close'].iloc[-1]
    last_ema200 = df['EMA_200'].iloc[-1]
    
    if last_close > last_ema200:
        return "BULLISH"
    elif last_close < last_ema200:
        return "BEARISH"
    return "NEUTRAL"

def calculate_momentum(df):
    """
    4H Momentum: Bullish if RSI(14) > 50.
    """
    if df.empty or len(df) < 14:
        return "NEUTRAL"

    df.ta.rsi(length=14, append=True)
    last_rsi = df['RSI_14'].iloc[-1]
    
    if last_rsi > 50:
        return "BULLISH"
    elif last_rsi < 50:
        return "BEARISH"
    return "NEUTRAL"

def calculate_trigger(df):
    """
    1H Trigger: 
    - MACD Line crosses above Signal Line (Golden Cross)
    - Price > EMA 50 (Trend Filter on Trigger TF)
    """
    if df.empty or len(df) < 50:
        return "HOLD"

    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    df.ta.ema(length=50, append=True)

    # MACD columns: MACD_12_26_9, MACDh_12_26_9 (hist), MACDs_12_26_9 (signal)
    macd = df['MACD_12_26_9']
    signal = df['MACDs_12_26_9']
    close = df['close']
    ema50 = df['EMA_50']
    
    # Check cross on last candle
    # Current: iloc[-1], Previous: iloc[-2]
    curr_macd = macd.iloc[-1]
    prev_macd = macd.iloc[-2]
    curr_signal = signal.iloc[-1]
    prev_signal = signal.iloc[-2]
    curr_close = close.iloc[-1]
    curr_ema50 = ema50.iloc[-1]
    
    # Bullish Cross: Prev MACD < Prev Signal AND Curr MACD > Curr Signal
    bullish_cross = (prev_macd <= prev_signal) and (curr_macd > curr_signal)
    
    if bullish_cross and (curr_close > curr_ema50):
        return "BUY"
    
    # Bearish logic could be added here
    
    return "HOLD"

def check_signal(symbol):
    """
    Hierarchical Check: D1 (Trend) -> 4H (Momentum) -> 1H (Trigger)
    """
    # 1. D1 Trend
    df_d1 = get_candles_df(symbol, '1d')
    trend = calculate_trend(df_d1)
    if trend != "BULLISH":
        return "HOLD", f"Trend is {trend}"

    # 2. 4H Momentum
    df_4h = get_candles_df(symbol, '4h')
    momentum = calculate_momentum(df_4h)
    if momentum != "BULLISH":
        return "HOLD", f"Momentum is {momentum}"

    # 3. 1H Trigger
    df_1h = get_candles_df(symbol, '1h')
    trigger = calculate_trigger(df_1h)
    
    if trigger == "BUY":
        return "BUY", "All conditions met"
    
    return "HOLD", "Waiting for trigger"
