import streamlit as st
import pandas as pd
from core.database import SessionLocal, Deployment, init_db
from sqlalchemy.exc import IntegrityError

st.set_page_config(page_title="Deployments", layout="wide")

# Initialize DB if not exists (for first run)
try:
    init_db()
except Exception:
    pass

st.title("Deployment Manager 🚀")

db = SessionLocal()

# --- Active Deployments ---
st.subheader("Active Instances")
try:
    deployments = db.query(Deployment).all()
    if deployments:
        # Convert to DataFrame for display
        data = [{
            "ID": d.id,
            "Name": d.name,
            "Exchange": d.exchange,
            "Balance": f"${d.current_balance:.2f}",
            "Risk Level": d.level,
            "Status": d.status
        } for d in deployments]
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        # Actions for each deployment
        col1, col2 = st.columns(2)
        with col1:
            stop_id = st.number_input("Stop ID", min_value=1, step=1, key="stop_deploy")
            if st.button("Stop Deployment"):
                d = db.query(Deployment).filter(Deployment.id == stop_id).first()
                if d:
                    d.status = "stopped"
                    db.commit()
                    st.success(f"Stopped {d.name}")
                    st.rerun()
                else:
                    st.error("Deployment not found")
        
        with col2:
            start_id = st.number_input("Start ID", min_value=1, step=1, key="start_deploy")
            if st.button("Start Deployment"):
                d = db.query(Deployment).filter(Deployment.id == start_id).first()
                if d:
                    d.status = "active"
                    db.commit()
                    st.success(f"Started {d.name}")
                    st.rerun()
                else:
                    st.error("Deployment not found")

    else:
        st.info("No active deployments found. Create one below.")

except Exception as e:
    st.error(f"Error loading deployments: {e}")

st.divider()

# --- Create New Deployment ---
st.subheader("Create New Deployment")

with st.form("new_deployment"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Instance Name", placeholder="My-Binance-Bot-1")
        exchange = st.selectbox("Exchange", ["binance", "kucoin", "gateio"])
    
    with col2:
        start_amount = st.number_input("Start Balance ($)", min_value=10.0, value=100.0)
        risk_level = st.slider("Initial Risk Level", 1, 10, 1)
    
    api_key_ref = st.text_input("API Key Env Var (Optional)", placeholder="BINANCE_API_KEY")
    
    submitted = st.form_submit_button("Launch Deployment 🚀")
    
    if submitted:
        if not name:
            st.error("Name is required")
        else:
            try:
                new_deploy = Deployment(
                    name=name,
                    exchange=exchange,
                    api_key_ref=api_key_ref,
                    start_amount=start_amount,
                    current_balance=start_amount,
                    level=risk_level,
                    status="active"
                )
                db.add(new_deploy)
                db.commit()
                st.success(f"Deployed {name} successfully!")
                st.rerun()
            except IntegrityError:
                st.error("Deployment name already exists!")
                db.rollback()
            except Exception as e:
                st.error(f"Failed to create deployment: {e}")
                db.rollback()

db.close()
