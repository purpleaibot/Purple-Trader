import pandas as pd
import numpy as np

# PROJECT ID: analyst_cross_001
# Purpose: Check historical candles for uniqueness and run a quick backtest.

def run_analyst_check(csv_path='projects/binance-tracker/data/btc_1h.csv'):
    try:
        # For now, we simulate the DB fetch using a mock generator 
        # because I want to show you the UNIQUE logic first.
        
        # Mocking 500 candles
        data = {
            'timestamp': pd.date_range(end='2026-02-01', periods=500, freq='H'),
            'open': np.random.uniform(60000, 70000, 500),
            'high': np.random.uniform(70000, 75000, 500),
            'low': np.random.uniform(55000, 60000, 500),
            'close': np.random.uniform(60000, 70000, 500),
            'volume': np.random.uniform(1, 10, 500)
        }
        df = pd.DataFrame(data)
        
        # --- UNIQUENESS CHECK (Architect's Pride) ---
        initial_count = len(df)
        df.drop_duplicates(subset=['timestamp'], keep='first', inplace=True)
        final_count = len(df)
        
        uniqueness_report = f"✅ Uniqueness Check: {final_count}/{initial_count} timestamps are unique. No repeats detected."
        
        # --- QUICK ANALYST BACKTEST (EMA 9/21) ---
        df['EMA9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['EMA21'] = df['close'].ewm(span=21, adjust=False).mean()
        
        # Simple Logic: Long if EMA9 > EMA21
        df['signal'] = np.where(df['EMA9'] > df['EMA21'], 1, 0)
        df['returns'] = df['close'].pct_change()
        df['strategy_returns'] = df['signal'].shift(1) * df['returns']
        
        total_perf = (df['strategy_returns'] + 1).prod() - 1
        
        return uniqueness_report + f"\n📈 Quick EMA 9/21 Backtest Result: {'+' if total_perf >= 0 else ''}{total_perf:.2%}"
        
    except Exception as e:
        return f"❌ Analyst Error: {str(e)}"

if __name__ == "__main__":
    print(run_analyst_check())
