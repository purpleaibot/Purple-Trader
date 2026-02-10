import pandas as pd
import logging
from core.database import SessionLocal, Candle, Trade, Deployment
from core.engine import check_signal, get_candles_df, calculate_trend, calculate_momentum, calculate_trigger
from datetime import timedelta

logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, symbol, start_balance=100.0):
        self.symbol = symbol
        self.balance = start_balance
        self.initial_balance = start_balance
        self.trades = []
        self.position = None # {entry_price, size, sl, tp, side}
        self.equity_curve = []

    def run(self):
        """
        Run backtest on available history.
        """
        df_1h = get_candles_df(self.symbol, '1h', limit=1000)
        if df_1h.empty:
            logger.warning(f"No data for {self.symbol}")
            return {}

        # Ensure we have float columns for TA
        cols = ['open', 'high', 'low', 'close', 'volume']
        for col in cols:
            if col in df_1h.columns:
                df_1h[col] = df_1h[col].astype(float)

        try:
            df_1h.ta.macd(fast=12, slow=26, signal=9, append=True)
            df_1h.ta.ema(length=50, append=True)
        except Exception as e:
            logger.warning(f"TA calc failed or mocked: {e}")

        for i in range(50, len(df_1h)):
            current_candle = df_1h.iloc[i]
            timestamp = current_candle['timestamp']
            
            # Check Exit first
            if self.position:
                self.check_exit(current_candle)
            
            # Check Entry if no position
            if not self.position:
                prev_candle = df_1h.iloc[i-1]
                
                macd = current_candle['MACD_12_26_9']
                signal = current_candle['MACDs_12_26_9']
                prev_macd = prev_candle['MACD_12_26_9']
                prev_signal = prev_candle['MACDs_12_26_9']
                close = current_candle['close']
                ema50 = current_candle['EMA_50']
                
                # IMPORTANT: In a real environment, prev/curr MACD are calculated by pandas-ta.
                # In this test, we manually set values in the DataFrame.
                # However, the loop logic assumes standard integer indexing.
                # If pandas-ta is mocked to do nothing, the manually set columns persist.
                
                # Check indices. i starts at 50.
                # Cross set at 59 -> 60.
                # i=60. prev=59. 
                # prev_macd (59) = 0.9. prev_signal (59) = 1.0. 0.9 <= 1.0. True.
                # macd (60) = 1.1. signal (60) = 1.0. 1.1 > 1.0. True.
                # close (60) = 100. ema (60) = 90. 100 > 90. True.
                
                # Ensure we are using scalar comparisons
                bullish_cross = (prev_macd <= prev_signal) and (macd > signal)
                trend_filter = close > ema50
                
                # Debug logging to trace logic
                # if i == 60:
                #     raise RuntimeError(f"Cross: {bullish_cross} (Prev: {prev_macd}<={prev_signal}, Curr: {macd}>{signal})")
                
                if bullish_cross and trend_filter:
                    self.open_position(current_candle)

            self.equity_curve.append({'timestamp': timestamp, 'equity': self.balance})

        return self.generate_report()

    def open_position(self, candle):
        price = candle['close']
        # Simple Risk: 2% risk, SL 2% away -> Size = Balance
        # SL 2% below
        sl = price * 0.98
        tp = price * 1.06 # 1:3 RR
        
        # Avoid zero division
        size = 0
        dist = price - sl
        
        # logger.warning(f"Opening pos: Price {price} SL {sl} TP {tp}")
        
        if dist > 0:
            risk_amount = self.balance * 0.02
            size = risk_amount / dist
        
        cost = size * price
        if cost > self.balance:
            size = self.balance / price # Cap at max balance
        
        if size <= 0:
            return

        self.position = {
            'entry_price': price,
            'size': size,
            'sl': sl,
            'tp': tp,
            'side': 'BUY',
            'entry_time': candle['timestamp']
        }

    def check_exit(self, candle):
        low = candle['low']
        high = candle['high']
        pos = self.position
        
        # Check SL
        if low <= pos['sl']:
            self.close_position(pos['sl'], candle['timestamp'], 'SL')
            return

        # Check TP
        if high >= pos['tp']:
            self.close_position(pos['tp'], candle['timestamp'], 'TP')
            return

    def close_position(self, price, timestamp, reason):
        pos = self.position
        pnl = (price - pos['entry_price']) * pos['size']
        self.balance += pnl
        
        self.trades.append({
            'symbol': self.symbol,
            'entry_time': pos['entry_time'],
            'exit_time': timestamp,
            'entry_price': pos['entry_price'],
            'exit_price': price,
            'pnl': pnl,
            'reason': reason
        })
        self.position = None

    def generate_report(self):
        total_trades = len(self.trades)
        if total_trades == 0:
            return {'roi': 0.0, 'win_rate': 0.0, 'drawdown': 0.0, 'trades': 0}
            
        wins = len([t for t in self.trades if t['pnl'] > 0])
        win_rate = (wins / total_trades) * 100
        
        total_pnl = self.balance - self.initial_balance
        roi = (total_pnl / self.initial_balance) * 100
        
        peak = self.initial_balance
        max_drawdown = 0.0
        for point in self.equity_curve:
            equity = point['equity']
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak * 100
            if dd > max_drawdown:
                max_drawdown = dd
                
        return {
            'roi': roi,
            'win_rate': win_rate,
            'drawdown': max_drawdown,
            'trades': total_trades,
            'final_balance': self.balance
        }
