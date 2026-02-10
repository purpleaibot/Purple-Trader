import asyncio
import ccxt.async_support as ccxt
import pandas as pd
from datetime import datetime, timedelta, timezone
from sqlalchemy.dialects.sqlite import insert
from core.database import SessionLocal, Candle
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Harvester:
    def __init__(self):
        self.exchanges = {}
        self.setup_exchanges()

    def setup_exchanges(self):
        """Initialize CCXT exchange instances."""
        exchange_ids = ['binance', 'kucoin', 'gateio']
        for exchange_id in exchange_ids:
            try:
                exchange_class = getattr(ccxt, exchange_id)
                # We can load API keys from env if needed for private endpoints, 
                # but for public data (OHLCV) keys are often optional or less strict limits.
                # However, providing keys increases rate limits.
                config = {
                    'enableRateLimit': True,
                    'options': {'defaultType': 'spot'} 
                }
                
                # Check for keys in env
                api_key = os.getenv(f"{exchange_id.upper()}_API_KEY")
                secret = os.getenv(f"{exchange_id.upper()}_SECRET")
                password = os.getenv(f"{exchange_id.upper()}_PASSWORD") # For KuCoin

                if api_key and secret:
                    config['apiKey'] = api_key
                    config['secret'] = secret
                    if password:
                        config['password'] = password
                
                self.exchanges[exchange_id] = exchange_class(config)
                logger.info(f"Initialized {exchange_id}")
            except Exception as e:
                logger.error(f"Failed to initialize {exchange_id}: {e}")

    async def close_exchanges(self):
        """Close all exchange connections."""
        for name, exchange in self.exchanges.items():
            await exchange.close()
            logger.info(f"Closed {name}")

    async def fetch_candles(self, exchange_name, symbol, interval, limit=500):
        """Fetch OHLCV data from a specific exchange."""
        exchange = self.exchanges.get(exchange_name)
        if not exchange:
            logger.error(f"Exchange {exchange_name} not found.")
            return []

        try:
            # Check if exchange supports fetchOHLCV
            if not exchange.has['fetchOHLCV']:
                logger.warning(f"{exchange_name} does not support fetchOHLCV")
                return []

            # CCXT returns: [timestamp, open, high, low, close, volume]
            ohlcv = await exchange.fetch_ohlcv(symbol, interval, limit=limit)
            logger.info(f"Fetched {len(ohlcv)} candles for {symbol} from {exchange_name}")
            return ohlcv
        except Exception as e:
            logger.error(f"Error fetching candles for {symbol} on {exchange_name}: {e}")
            return []

    def save_candles(self, ohlcv_data, symbol, interval):
        """Save candles to the database using upsert."""
        if not ohlcv_data:
            return

        session = SessionLocal()
        try:
            for candle in ohlcv_data:
                # CCXT timestamp is ms
                ts = datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc)
                
                stmt = insert(Candle).values(
                    symbol=symbol,
                    interval=interval,
                    timestamp=ts,
                    open=candle[1],
                    high=candle[2],
                    low=candle[3],
                    close=candle[4],
                    volume=candle[5]
                )
                
                # SQLite upsert: update if exists (to ensure data consistency)
                # We update everything except the primary key ID
                do_update_stmt = stmt.on_conflict_do_update(
                    index_elements=['symbol', 'interval', 'timestamp'],
                    set_={
                        'open': stmt.excluded.open,
                        'high': stmt.excluded.high,
                        'low': stmt.excluded.low,
                        'close': stmt.excluded.close,
                        'volume': stmt.excluded.volume
                    }
                )
                
                session.execute(do_update_stmt)
            
            session.commit()
            logger.info(f"Saved {len(ohlcv_data)} candles for {symbol} to DB.")
        except Exception as e:
            logger.error(f"Database error saving candles: {e}")
            session.rollback()
        finally:
            session.close()

    async def run_poll_loop(self, exchange_name, symbols, interval):
        """Main polling loop for a list of symbols on an exchange."""
        logger.info(f"Starting poll loop for {exchange_name} - {interval}")
        
        # Determine wait time based on interval
        # Basic logic: 1h -> wait for next hour + 5s
        # 15m -> wait for next 15m block + 5s
        
        while True:
            now = datetime.now(timezone.utc)
            
            if interval == '1h':
                # Next hour
                next_run = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            elif interval == '4h':
                # Next 4 hour block (0, 4, 8, 12, 16, 20)
                current_block = now.hour // 4
                next_hour = (current_block + 1) * 4
                if next_hour >= 24:
                    next_run = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                else:
                    next_run = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
            elif interval == '15m':
                # Next 15m block
                minutes = now.minute
                next_15 = ((minutes // 15) + 1) * 15
                if next_15 >= 60:
                    next_run = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                else:
                    next_run = now.replace(minute=next_15, second=0, microsecond=0)
            elif interval == '1d':
                # Next day
                next_run = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            else:
                 # Default fallback: 1 minute
                 next_run = now + timedelta(minutes=1)

            # Add 5 second buffer
            target_time = next_run + timedelta(seconds=5)
            sleep_seconds = (target_time - now).total_seconds()
            
            if sleep_seconds > 0:
                logger.info(f"Sleeping for {sleep_seconds:.2f}s until {target_time}")
                await asyncio.sleep(sleep_seconds)
            
            # Fetch for all symbols
            tasks = []
            for symbol in symbols:
                tasks.append(self.process_symbol(exchange_name, symbol, interval))
            
            await asyncio.gather(*tasks)

    async def process_symbol(self, exchange_name, symbol, interval, limit=5):
        """Process a single symbol: fetch and save."""
        # limit is small for live polling (we only need the last closed candle)
        # But for the first run, we might want backfill. 
        # For simplicity, we can fetch a larger chunk on startup or handle backfill separately.
        # The story says "Historical backfill (500 candles) logic implemented for newly added symbols".
        # We can just fetch 500 every time? No, waste of bandwidth.
        # But since we upsert, it's safe.
        # Maybe fetch 5 candles for live loop, 500 for startup.
        # I'll stick to 'limit' param. The caller decides.
        
        ohlcv = await self.fetch_candles(exchange_name, symbol, interval, limit)
        self.save_candles(ohlcv, symbol, interval)

    async def backfill(self, exchange_name, symbols, interval):
         """One-time backfill."""
         logger.info(f"Backfilling {len(symbols)} symbols on {exchange_name}...")
         tasks = []
         for symbol in symbols:
             tasks.append(self.process_symbol(exchange_name, symbol, interval, limit=500))
         await asyncio.gather(*tasks)

# Example usage entry point if run directly
if __name__ == "__main__":
    async def main():
        harvester = Harvester()
        try:
            # Example: Backfill BTC/USDT on Binance
            await harvester.backfill('binance', ['BTC/USDT'], '1h')
        finally:
            await harvester.close_exchanges()

    asyncio.run(main())
