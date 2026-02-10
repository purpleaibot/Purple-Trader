# THE ORACLE TRADING HUB: COMMAND CENTER
ID: doc_cmd_001
Date: 2026-02-01

## 1. Project Initialization
```bash
# Setup Virtual Environment
python3 -m venv venv
source venv/bin/activate

# Install Core Dependencies
pip install ccxt pandas-ta streamlit supabase python-dotenv playwright
playwright install chromium
```

## 2. Testing Procedures
### 2.1 UI Testing (Playwright)
```bash
# Run UI Tests
pytest tests/ui/
```

### 2.2 Core Logic (Sandbox)
```bash
# Run Harvester Mock Test
python3 tests/core/test_harvester.py
```

## 3. Maintenance
- **Update Manifesto:** `python3 scripts/update_manifesto.py`
- **Security Check:** `python3 scripts/sentinel_audit.py`
