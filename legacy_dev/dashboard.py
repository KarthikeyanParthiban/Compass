import streamlit as st
import pandas as pd
import numpy as np
from monte_carlo import run_full_simulation, plot_results, load_portfolio_data
import matplotlib.pyplot as plt

# Set page config
st.set_page_config(page_title="Portfolio Monte Carlo Dashboard", layout="wide", page_icon="📈")

# Custom CSS for a premium dark-themed look
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #00ffcc;
    }
    div[data-testid="stMetricDelta"] {
        color: #00ff00;
    }
    .stButton>button {
        background-color: #00ffcc;
        color: #000000;
        font-weight: bold;
        border-radius: 5px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #00cca3;
        color: #000000;
    }
    .info-box {
        background-color: #1e2227;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #30363d;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# Title and Description
st.title("🚀 Portfolio Monte Carlo Simulation Dashboard")
st.markdown("Predict the future performance of your Groww portfolio using historical volatility and correlated random walks.")

# Sidebar Configuration
st.sidebar.header("Simulation Settings")
num_sims = st.sidebar.select_slider("Iterations", options=[1000, 2000, 5000, 10000, 20000], value=10000)
days = st.sidebar.slider("Projection Period (Days)", 30, 756, 252, step=30)
st.sidebar.markdown("---")
st.sidebar.info("This simulation uses 2 years of historical data to estimate mean returns and asset correlations.")

# Persistent state for results
if 'results' not in st.session_state:
    st.session_state.results = None

# On-demand Run Button
if st.sidebar.button("Run Simulation", use_container_width=True):
    with st.spinner("Analyzing portfolio and running simulations..."):
        try:
            st.session_state.results = run_full_simulation(num_sims=num_sims, days=days)
            st.success("Simulation complete!")
        except Exception as e:
            st.error(f"Error: {e}")

# Main Content
if st.session_state.results:
    res = st.session_state.results
    
    # Metrics Bar
    m1, m2, m3, m4 = st.columns(4)
    
    growth = ((res['mean_end'] / res['current_value']) - 1) * 100
    m1.metric("Current Value", f"₹{res['current_value']:,.2f}")
    m2.metric("Expected (Mean)", f"₹{res['mean_end']:,.2f}", f"{growth:+.1f}%")
    m3.metric("VaR (5%)", f"₹{res['current_value'] - res['var_5']:,.2f}")
    m4.metric("Profit Prob.", f"{res['prob_profit']*100:.1f}%")
    
    st.markdown("---")
    
    # Plots
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("Monte Carlo Path Projections")
        fig = plot_results(res['paths'], res['current_value'], save_path=None)
        st.pyplot(fig)
    
    with col_right:
        st.subheader("Portfolio Allocation")
        weights_df = pd.DataFrame({
            'Asset': res['symbols'],
            'Weight': [w * 100 for w in res['weights']]
        }).sort_values('Weight', ascending=False)
        
        fig2, ax2 = plt.subplots(figsize=(6, 6))
        ax2.pie(weights_df['Weight'], labels=weights_df['Asset'], autopct='%1.1f%%', 
                startangle=140, colors=plt.cm.viridis(np.linspace(0, 1, len(weights_df))))
        ax2.axis('equal')
        fig2.patch.set_facecolor('#0e1117')
        plt.setp(ax2.get_xticklabels(), color="white")
        plt.setp(ax2.get_yticklabels(), color="white")
        st.pyplot(fig2)

    st.markdown("---")
    
    # Details Table
    with st.expander("Detailed Portfolio Breakdown"):
        st.dataframe(weights_df, hide_index=True, use_container_width=True)

else:
    # Landing state
    st.markdown("""
    <div class="info-box">
        <h3>Welcome to the Portfolio Analyzer</h3>
        <p>Ready to see where your investments could be in a year? This tool fetches your real-time holdings from Groww and performs a statistical risk analysis.</p>
        <p><b>Step 1:</b> Adjust the settings in the sidebar.</p>
        <p><b>Step 2:</b> Click <b>'Run Simulation'</b> to start.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show holdings preview
    try:
        holdings = load_portfolio_data()
        st.subheader("Detected Holdings")
        df_holdings = pd.DataFrame(holdings)
        st.dataframe(df_holdings[['symbol', 'quantity', 'avg_price']], hide_index=True, use_container_width=True)
    except Exception as e:
        st.warning("Could not load holdings preview. Please ensure Main.py has a valid token.")
