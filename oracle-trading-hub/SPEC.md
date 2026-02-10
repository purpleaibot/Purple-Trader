# PROJECT SPECIFICATION: The Oracle Trading Hub
ID: spec_binance_001
Date: 2026-02-01
Status: VISION_LOCKED

## 1. Vision Overview
A comprehensive, multi-agent trading ecosystem. The system handles authentication, multi-exchange monitoring, high-scale data ingestion (100+ pairs), and multi-modal analysis (Technical, News, On-chain, LLM).

## 2. Technical Stack
- **Backend:** Python 3.12 (Asynchronous/Asyncio)
- **Frontend:** Streamlit (Multi-page: Login, Config, Monitor, Top Movers)
- **Database:** Supabase (Remote/Faster for multi-agent sync) or SQLite (Local fallback)
- **Exchange Integration:** CCXT (Universal library for multiple exchanges)
- **Analysis:** LangChain/Gemini (For LLM assessment)
- **Security:** AES encryption for API keys in .env + Sentinel monitoring.

## 3. Core Architecture & Agents
### 3.1 The Hub (Purple AI Orchestrator)
- Manages the following specialized agents.

### 3.2 The Harvester (agent_developer_001)
- **Role:** Async data ingestion for 100+ pairs.
- **Task:** Historical candle backfill + real-time close tracking (15m to 1M).

### 3.3 The UI Specialist (agent_ui_001)
- **Pages:**
  - `Login`: Secure entry.
  - `Exchange Selector`: Select Base Currency, Market (Spot/Futures), and Exchange.
  - `Monitoring`: Select/Track up to 100 pairs.
  - `Top Movers`: Real-time ranking.

### 3.4 The Strategist (agent_analyst_001)
- **Role:** Technical Analysis Assessment.
- **Task:** Runs predefined technical strategies on closed candles.

### 3.5 The Oracle (agent_llm_001 - NEW)
- **Role:** LLM-based Data Synthesis.
- **Task:** Receives technical data and provides a natural language sentiment score.

### 3.6 The News Hound (agent_news_001 - NEW)
- **Role:** Sentiment & Blockchain Monitor.
- **Task:** Scrapes news and monitors whale movements/blockchain alerts for selected pairs.

### 3.7 The General (agent_commander_001 - NEW)
- **Role:** Decision & Risk Manager.
- **Task:** Collects info from Strategist, Oracle, and News Hound. Defines Entry, Exit, and Risk.

### 3.8 The Executioner (agent_trader_001)
- **Role:** Trade Placement & Management.
- **Task:** Interacts with exchanges or a separate trade management program.

## 4. Immediate Roadmap
1. [ ] Architect: Design the Supabase/Database schema for multi-timeframe candle storage.
2. [ ] Sentinel: Implement secure login and encrypted storage for API keys.
3. [ ] Developer: Create the CCXT-based Async Harvester for Binance/Multi-exchange.
