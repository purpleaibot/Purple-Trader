"""
Oracle AI Trading Hub - Main Orchestrator
Integrates: Harvester -> Engine -> Risk -> Guards -> Signals
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional

from dotenv import load_dotenv

from core.database import SessionLocal, Deployment, Trade, init_db
from core.harvester import Harvester
from core.engine import check_signal, get_candles_df
from core.risk import RiskEngine
from core.guards import CorrelationGuard, LiquidityGuard
from core.signals import SignalPackager
from agents.analyst import CryptoAnalyst

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("oracle")

class OracleOrchestrator:
    """
    Main orchestrator for the Oracle AI Trading Hub.
    Coordinates all components for signal generation and trade execution.
    """
    
    def __init__(self, deployment_name: str = "default"):
        self.deployment_name = deployment_name
        self.deployment = None
        self.harvester = None
        self.risk_engine = None
        self.correlation_guard = None
        self.liquidity_guard = None
        self.analyst = CryptoAnalyst()
        
        # Trading configuration
        self.symbols: List[str] = []
        self.exchange_name: str = "binance"
        self.intervals = ['1d', '4h', '1h']
        
        # State
        self.active_positions: List[str] = []
        self.running = False

    def load_deployment(self) -> bool:
        """Load deployment configuration from database."""
        db = SessionLocal()
        try:
            self.deployment = db.query(Deployment).filter_by(
                name=self.deployment_name, 
                status="active"
            ).first()
            
            if not self.deployment:
                logger.error(f"No active deployment found: {self.deployment_name}")
                return False
            
            self.exchange_name = self.deployment.exchange
            logger.info(f"Loaded deployment: {self.deployment.name} (Level {self.deployment.level})")
            
            # Initialize risk engine with deployment level
            self.risk_engine = RiskEngine(initial_level=self.deployment.level)
            
            return True
        finally:
            db.close()

    async def initialize(self, symbols: List[str]):
        """Initialize all components."""
        self.symbols = symbols
        
        # 1. Initialize database
        init_db()
        
        # 2. Load deployment config
        if not self.load_deployment():
            raise RuntimeError("Failed to load deployment")
        
        # 3. Initialize harvester
        self.harvester = Harvester()
        
        # 4. Initialize guards
        self.correlation_guard = CorrelationGuard(max_trades_per_asset=2)
        
        # Get exchange for liquidity guard
        exchange = self.harvester.exchanges.get(self.exchange_name)
        if exchange:
            self.liquidity_guard = LiquidityGuard(
                exchange=exchange,
                max_spread_pct=0.005,
                min_depth_usdt=500.0
            )
        
        logger.info(f"Initialized Oracle for {len(symbols)} symbols on {self.exchange_name}")

    async def backfill_data(self):
        """Backfill historical data for all symbols and intervals."""
        logger.info("Starting data backfill...")
        for interval in self.intervals:
            await self.harvester.backfill(self.exchange_name, self.symbols, interval)
        logger.info("Backfill complete")

    async def run_analysis_cycle(self) -> List[Dict]:
        """
        Run one complete analysis cycle for all symbols.
        Returns list of generated signals.
        """
        signals = []
        
        # Update correlation guard with current positions
        self.correlation_guard.update_positions(self.active_positions)
        
        for symbol in self.symbols:
            try:
                signal = await self.analyze_symbol(symbol)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
        
        return signals

    async def analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Complete analysis pipeline for a single symbol.
        """
        logger.info(f"Analyzing {symbol}...")
        
        # 1. Check technical signal
        verdict, reason = check_signal(symbol)
        
        if verdict != "BUY":
            logger.debug(f"{symbol}: {verdict} - {reason}")
            return None
        
        logger.info(f"{symbol}: Technical signal = BUY ({reason})")
        
        # 2. Check correlation guard
        if not self.correlation_guard.check(symbol):
            logger.warning(f"{symbol}: Blocked by correlation guard")
            return None
        
        # 3. Check liquidity guard (requires async exchange)
        if self.liquidity_guard:
            # Note: LiquidityGuard uses sync CCXT. For async, we'd need adjustment.
            # For now, skip in async context or wrap in executor
            pass
        
        # 4. Get sentiment analysis
        sentiment = self.analyst.analyze_sentiment(symbol.split('/')[0])
        
        if sentiment['verdict'] == "BEARISH":
            logger.warning(f"{symbol}: Sentiment is bearish, skipping")
            return None
        
        # 5. Calculate position sizing
        account_balance = self.deployment.current_balance
        position_size_value = self.risk_engine.calculate_position_size(account_balance)
        
        # Get current price for size calculation
        df = get_candles_df(symbol, '1h', limit=1)
        if df.empty:
            logger.error(f"{symbol}: No price data available")
            return None
        
        current_price = df['close'].iloc[-1]
        position_size = position_size_value / current_price
        
        # 6. Calculate SL/TP (simple ATR-based or percentage)
        # Using 2% SL, 6% TP (1:3 RR)
        sl = current_price * 0.98
        tp = current_price * 1.06
        
        # 7. Package signal
        signal_data = {
            'symbol': symbol,
            'side': 'BUY',
            'entry_price': current_price,
            'sl': sl,
            'tp': tp,
            'size': position_size,
            'level': self.risk_engine.current_level,
            'slevel': 0,
            'strategy_verdict': verdict,
            'agent_verdict': sentiment['verdict']
        }
        
        packet = SignalPackager.package_trade(signal_data)
        logger.info(f"Signal generated for {symbol}: Entry={current_price:.2f}, Size={position_size:.6f}")
        
        return packet

    async def run_live(self, poll_interval_seconds: int = 60):
        """
        Main live trading loop.
        """
        self.running = True
        logger.info("Starting live trading loop...")
        
        while self.running:
            try:
                # 1. Update candle data
                for interval in ['1h']:  # Focus on trigger timeframe for live
                    for symbol in self.symbols:
                        await self.harvester.process_symbol(
                            self.exchange_name, symbol, interval, limit=5
                        )
                
                # 2. Run analysis
                signals = await self.run_analysis_cycle()
                
                if signals:
                    logger.info(f"Generated {len(signals)} signals this cycle")
                    for sig in signals:
                        logger.info(f"  -> {sig['trade']['symbol']} @ {sig['trade']['entry']}")
                
                # 3. Wait for next cycle
                await asyncio.sleep(poll_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in live loop: {e}")
                await asyncio.sleep(10)

    async def shutdown(self):
        """Clean shutdown of all components."""
        self.running = False
        if self.harvester:
            await self.harvester.close_exchanges()
        logger.info("Oracle shutdown complete")


async def run_integration_test():
    """Integration test: backfill data and run one analysis cycle."""
    logger.info("=" * 60)
    logger.info("ORACLE AI TRADING HUB - INTEGRATION TEST")
    logger.info("=" * 60)
    
    # Create a test deployment if none exists
    db = SessionLocal()
    try:
        existing = db.query(Deployment).filter_by(name="test-deployment").first()
        if not existing:
            test_deploy = Deployment(
                name="test-deployment",
                exchange="binance",
                start_amount=1000.0,
                current_balance=1000.0,
                level=5,
                status="active"
            )
            db.add(test_deploy)
            db.commit()
            logger.info("Created test deployment")
    finally:
        db.close()
    
    # Initialize orchestrator
    oracle = OracleOrchestrator(deployment_name="test-deployment")
    
    try:
        # Initialize with test symbols
        test_symbols = ['BTC/USDT', 'ETH/USDT']
        await oracle.initialize(test_symbols)
        
        # Backfill data
        await oracle.backfill_data()
        
        # Run one analysis cycle
        logger.info("Running analysis cycle...")
        signals = await oracle.run_analysis_cycle()
        
        logger.info("=" * 60)
        logger.info(f"INTEGRATION TEST COMPLETE - {len(signals)} signals generated")
        logger.info("=" * 60)
        
        return signals
        
    finally:
        await oracle.shutdown()


async def run_live_trading(deployment_name: str, symbols: List[str]):
    """Start live trading loop."""
    oracle = OracleOrchestrator(deployment_name=deployment_name)
    
    try:
        await oracle.initialize(symbols)
        await oracle.backfill_data()
        await oracle.run_live(poll_interval_seconds=300)  # 5 minute cycles
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await oracle.shutdown()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "live":
        # Live mode: python main.py live <deployment_name> <symbol1> <symbol2> ...
        deployment = sys.argv[2] if len(sys.argv) > 2 else "test-deployment"
        symbols = sys.argv[3:] if len(sys.argv) > 3 else ['BTC/USDT', 'ETH/USDT']
        asyncio.run(run_live_trading(deployment, symbols))
    else:
        # Test mode
        asyncio.run(run_integration_test())
