import streamlit as st

st.set_page_config(page_title="Oracle AI Trading Hub", layout="wide")

st.title("Oracle AI Trading Hub v2")

st.write("""
Welcome to the Oracle AI Trading Hub dashboard.
Use the sidebar to navigate between:
- **Deployments**: Manage bot instances and risk.
- **Analytics**: View backtest results and performance.
- **Settings**: Configure API keys and system settings.
""")

st.info("System Status: Online 🟢")
