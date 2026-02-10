# THE ORACLE TRADING HUB: MASTER MANIFESTO
ID: plan_oracle_001
Date: 2026-02-01
Status: FINALIZED ARCHITECTURE

## 1. Executive Summary
A modular, multi-agent trading system built for precision, resilience, and scale. The system operates on user-defined "Portfolios" of Pair/Timeframe combinations, utilizing a REST-based polling strategy to maintain data integrity without hitting API rate limits or suffering from WebSocket instability.

## 2. The Agent Workforce
- **Commander (Orchestrator):** Manages the lifecycle. Handles the "Bootstrap" (500 historical candles) and keeps the agents in sync.
- **Developer (Harvester):** The data-mule. Performs parallel REST polls at Candle Close + 5s. Validates sequence and uniqueness.
- **Architect (DB Manager):** Owns the Sharded Candle Schema. Ensures high-speed "Upsert" logic and handles the `active_watchlist`.
- **Analyst (Strategist):** The math nerd. Only wakes up when a *new* candle is saved for its specific pair/timeframe. Generates "Raw Signals."
- **Trading Agent (The Gatekeeper):** The pragmatist. Analyzes "Raw Signals" for tradeability (liquidity, spread, exposure) before execution.
- **Sentinel (Security):** Paranoia-as-a-Service. Protects API keys and ensures the UI doesn't leak secrets.
- **UI Specialist:** Builds the Streamlit Command Center for portfolio management and live monitoring.

## 3. The Data Pipeline (REST-Driven)
- **Monitoring Trigger:** User selects Pair + Timeframe (e.g., VET 4h) in UI -> Added to `active_watchlist`.
- **The Bootstrap:** System pulls 500 historical candles once to prime indicators.
- **The Scheduler:** 
    - Every minute, the system checks if a tracked timeframe has closed (15m, 30m, 1h, 4h, etc.).
    - **Execution:** Close + 5 seconds delay to ensure exchange finality.
- **Retry Logic:** 
    - If a pull fails/is corrupt: Log error -> Flag `PENDING_RETRY`.
    - **Retry Schedule:** Every 5 minutes within the current candle window.
    - **Deadline:** If not resolved by the *next* close for that timeframe, the gap is logged and the opportunity is discarded.

## 4. Signal & Execution Flow
1. **New Candle Detected:** Harvester saves it to the Sharded Schema.
2. **Analyst Trigger:** Fired *only* for that specific Pair:Timeframe.
3. **Indicator Calculation:** TA-Lib/Pandas-TA runs fresh math.
4. **Signal Generation:** If strategy conditions = True -> Create `Raw Signal`.
5. **Tradeability Check:** Trading Agent verifies market conditions (Spread, Volume, Account Balance).
6. **Execution:** Signal is logged to `signal_queue`.

## 5. Technology Stack
- **Language:** Python 3.12 (Async)
- **API:** CCXT (Binance REST)
- **Database:** Supabase (PostgreSQL) with Sharded Schema
- **UI:** Streamlit (Headless Sandbox)
- **Testing:** Playwright (UI) + Sentinel Audit (Security)

## 6. Implementation Roadmap
- **Phase 1 (Done):** Environment setup, Mock Dashboard, Basic CCXT Handshake.
- **Phase 2 (In Progress):** Dynamic `active_watchlist` DB layer & Multi-interval Scheduler.
- **Phase 3:** "Tradeability" logic and Trading Agent integration.
- **Phase 4:** Live Strategy Implementation & Portfolio Management UI.
