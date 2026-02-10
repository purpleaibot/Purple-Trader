import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import time

# PROJECT ID: app_binance_001
# Date: 2026-02-01

st.set_page_config(page_title="The Oracle Trading Hub", layout="wide")

# --- AUTHENTICATION MOCK ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def login_page():
    st.title("💜 The Oracle Trading Hub")
    st.subheader("Login to access the Command Center")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Access Hub")
        if submitted:
            if username == "alex" and password == "purple": # Mock credentials
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid credentials. The Sentinel is watching.")

# --- DATA LAYER ---
def get_live_data():
    try:
        # Using the venv python to run the live pull script
        import subprocess
        result = subprocess.run(
            ["/home/ubuntu/.openclaw/workspace/projects/binance-tracker/venv/bin/python3", "projects/binance-tracker/live_pull.py"],
            capture_output=True, text=True
        )
        return result.stdout
    except Exception as e:
        return f"Error fetching live data: {e}"

# --- MAIN HUB ---
def main_hub():
    with st.sidebar:
        selected = option_menu(
            "Main Menu", ["Dashboard", "Exchange Setup", "Pair Monitor", "Signals", "Settings"],
            icons=['house', 'gear', 'eye', 'activity', 'info-circle'],
            menu_icon="cast", default_index=0,
        )
        
        st.divider()
        st.info("Status: DEVELOPMENT MODE")
        st.write(f"Agents: 5 Active")
        
        if st.button("Refresh Live Data"):
            st.session_state.live_feed = get_live_data()
            st.toast("Developer Agent: Fresh data harvested.")

        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

    if selected == "Dashboard":
        st.title("🚀 Oracle Dashboard")
        
        if 'live_feed' in st.session_state:
            st.code(st.session_state.live_feed)
        else:
            st.warning("Click 'Refresh Live Data' to wake up the Developer.")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tracked Pairs", "100", "+5")
        col2.metric("Active Signals", "12", "High Conviction")
        col3.metric("Exchange Status", "Connected", "Binance")
        col4.metric("Market Sentiment", "Bullish", "LLM Score: 85")
        
        st.subheader("Top Movers (Mock Data)")
        df = pd.DataFrame({
            'Symbol': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'LINK/USDT', 'ADA/USDT'],
            'Price': [65432.10, 3456.78, 145.22, 18.90, 0.55],
            '24h Change': ['+2.5%', '+1.8%', '+5.2%', '-0.5%', '+0.2%'],
            'Volume': ['1.2B', '800M', '300M', '50M', '20M']
        })
        st.table(df)

    elif selected == "Exchange Setup":
        st.title("⚙️ Exchange Configuration")
        col1, col2 = st.columns(2)
        with col1:
            exchange = st.selectbox("Select Exchange", ["Binance", "Bybit", "OKX", "Coinbase"])
            market = st.radio("Select Market", ["Spot", "Futures", "Margin"])
        with col2:
            base_currency = st.selectbox("Base Currency", ["USDT", "USDC", "BTC", "ETH"])
            api_status = st.success("API Keys Found in .env")
        
        st.button("Sync Exchange Assets")

    elif selected == "Pair Monitor":
        st.title("👀 Pair Monitor")
        st.write("Select up to 100 pairs to track across 15m, 1h, 4h, and 1d timeframes.")
        
        all_pairs = [f"{s}/USDT" for s in ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT", "LINK"]]
        selected_pairs = st.multiselect("Active Tracking List", all_pairs, default=all_pairs[:5])
        
        if st.button("Update Harvester"):
            st.toast("Developer Agent updating WebSocket streams...")

    elif selected == "Signals":
        st.title("⚡ Real-Time Signals")
        st.write("Live analysis from the Strategist & Oracle agents.")
        
        signal_data = {
            "Symbol": "BTC/USDT",
            "Signal": "BUY",
            "Timeframe": "1h",
            "Strategy": "EMA 9/21 Cross + RSI Oversold",
            "Confidence": "88%",
            "Oracle Verdict": "Positive News Sentiment + Whale accumulation detected."
        }
        st.json(signal_data)
        
        # Mock Chart
        chart_data = pd.DataFrame(np.random.randn(20, 3), columns=['Close', 'EMA9', 'EMA21'])
        st.line_chart(chart_data)

# --- ROUTING ---
if not st.session_state.authenticated:
    login_page()
else:
    main_hub()
