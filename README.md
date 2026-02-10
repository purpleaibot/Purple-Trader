# The Oracle Trading Hub (V2)

A comprehensive, multi-agent trading ecosystem designed for advanced, multi-modal cryptocurrency analysis and automated execution. This system handles authentication, multi-exchange monitoring, high-scale data ingestion (100+ pairs), and multi-modal analysis (Technical, News, On-chain, LLM).

## Key Features & Implemented Modules (Phase 5)

Our recent development efforts focused on critical enhancements, completing Epics 4 and 5, which brought the project to a state of readiness for live deployment.

### Epic 4: Risk & Deployment Hub (Complete)
*   **10-Level Risk Engine (`core/risk.py`):** Implemented a dynamic risk management system with 10 configurable risk levels, position sizing, and daily loss limits. Includes dynamic risk adjustment based on real-time drawdown.
*   **Correlation & Liquidity Guards (`core/guards.py`):** Introduced safeguards to prevent over-exposure by limiting concurrent trades per asset and validating order book spread/depth via CCXT.
*   **Deployment Dashboard (`ui/app.py`, `ui/pages/1_Deployments.py`):** A Streamlit-based user interface for managing active deployments, with features for starting, stopping, and creating new trading instances.

### Epic 5: Signal Packaging & Post-Mortem (Complete)
*   **Secure Signal Packaging (`core/signals.py`):** Developed a system for generating secure JSON trade packets with robust validation and file logging (`core/logs/signals.log`).
*   **Post-Mortem Analysis Loop (`agents/post_mortem.py`):** An agent-based system for comprehensive trade analysis, including win/loss statistics, performance breakdown by symbol, and AI-generated insights (placeholder for LLM integration). Reports are saved to `data/reports/post_mortem_YYYY-MM-DD.md`.

## Core Architecture & Agents

The Oracle Trading Hub operates as a multi-agent system, orchestrated by the **Purple AI Orchestrator**.

*   **The Hub (Purple AI Orchestrator):** Manages all specialized agents.
*   **The Harvester (agent_developer_001):** Asynchronous data ingestion for 100+ pairs, handling historical candle backfill and real-time close tracking (15m to 1M).
*   **The UI Specialist (agent_ui_001):** Manages the Streamlit frontend with pages for Login, Exchange Selection, Monitoring (up to 100 pairs), and Top Movers.
*   **The Oracle (agent_llm_001 - NEW):** Provides LLM-based data synthesis, generating natural language sentiment scores from technical data.
*   **The News Hound (agent_news_001 - NEW):** Monitors sentiment and blockchain alerts, scraping news and tracking whale movements for selected pairs.
*   **The General (agent_commander_001 - NEW):** The decision and risk manager, consolidating information from Strategist, Oracle, and News Hound to define entry, exit, and risk parameters.
*   **The Executioner (agent_trader_001):** Responsible for trade placement and management, interacting with exchanges or a dedicated trade management program.

## Technical Stack

*   **Backend:** Python 3.12 (Asynchronous/Asyncio)
*   **Frontend:** Streamlit (Multi-page: Login, Config, Monitor, Top Movers)
*   **Database:** Supabase (Remote/Faster for multi-agent sync) or SQLite (Local fallback)
*   **Exchange Integration:** CCXT (Universal library for multiple exchanges)
*   **Analysis:** LangChain/Gemini (For LLM assessment)
*   **Security:** AES encryption for API keys in .env + Sentinel monitoring.

## Deployment

The project includes a `main.py` orchestrator and a `deploy.sh` script for one-command live deployment. To go live:

1.  **Configure API keys:** Edit the `.env` file to add your exchange API keys.
    ```bash
    nano .env
    # Add your exchange keys
    ```
2.  **Start live trading:**
    ```bash
    ./deploy.sh test-deployment BTC/USDT ETH/USDT
    ```

## Project Structure (Key Directories)

*   `main.py`: The central orchestrator.
*   `deploy.sh`: Deployment script.
*   `core/`: Contains core logic like risk management, guards, and signal packaging.
*   `agents/`: Houses specialized agents (e.g., `post_mortem.py`).
*   `ui/`: Streamlit application files for the user interface.
*   `oracle-trading-hub/`: Project specification (`SPEC.md`), configuration, and other related files.
*   `data/`: Data storage, including post-mortem reports.
*   `tests/`: Unit and integration tests.
