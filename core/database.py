import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Configuration
DB_PATH = os.getenv("DB_PATH", "data/oracle.db")
# Ensure the directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

Base = declarative_base()

class Candle(Base):
    __tablename__ = 'candles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False)
    interval = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    # Efficient indices for lookups
    __table_args__ = (
        Index('idx_symbol_interval_timestamp', 'symbol', 'interval', 'timestamp'),
        UniqueConstraint('symbol', 'interval', 'timestamp', name='uq_candle'),
    )

    def __repr__(self):
        return f"<Candle(symbol='{self.symbol}', interval='{self.interval}', ts='{self.timestamp}')>"

class Deployment(Base):
    __tablename__ = 'deployments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    exchange = Column(String, nullable=False)
    api_key_ref = Column(String) # Reference to env var name, not the key itself
    start_amount = Column(Float, default=100.0)
    current_balance = Column(Float, default=100.0)
    level = Column(Integer, default=1)
    slevel = Column(Integer, default=0) # 0 means not in safety level
    status = Column(String, default="active") # active, paused, stopped
    
    trades = relationship("Trade", back_populates="deployment")
    signals = relationship("Signal", back_populates="deployment")

    def __repr__(self):
        return f"<Deployment(name='{self.name}', level={self.level})>"

class Trade(Base):
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    deployment_id = Column(Integer, ForeignKey('deployments.id'), nullable=False)
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False) # BUY, SELL
    entry_price = Column(Float, nullable=False)
    sl = Column(Float, nullable=False)
    tp = Column(Float, nullable=False)
    size = Column(Float, nullable=False)
    status = Column(String, default="OPEN") # OPEN, CLOSED, CANCELED
    level_at_entry = Column(Integer, nullable=False)
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)
    exit_price = Column(Float, nullable=True)
    pnl = Column(Float, default=0.0)

    deployment = relationship("Deployment", back_populates="trades")

    def __repr__(self):
        return f"<Trade(id={self.id}, symbol='{self.symbol}', pnl={self.pnl})>"

class Signal(Base):
    __tablename__ = 'signals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    deployment_id = Column(Integer, ForeignKey('deployments.id'), nullable=False)
    symbol = Column(String, nullable=False)
    interval = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    strategy_verdict = Column(String) # HOLD, BUY, SELL
    agent_verdict = Column(String) # BULLISH, BEARISH, NEUTRAL
    confidence = Column(Float)
    sl = Column(Float)
    tp = Column(Float)
    
    deployment = relationship("Deployment", back_populates="signals")

    def __repr__(self):
        return f"<Signal(id={self.id}, symbol='{self.symbol}', verdict='{self.strategy_verdict}')>"

# Engine and Session Factory
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Initializes the database by creating all tables."""
    Base.metadata.create_all(engine)
    print(f"Database initialized at {DB_PATH}")

def get_db():
    """Dependency for getting a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
