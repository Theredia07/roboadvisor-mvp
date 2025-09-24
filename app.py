import streamlit as st
from robo import PortfolioConfig, simulate_dca, performance_stats, profile_to_weights, DEFAULT_EQUITY, DEFAULT_BOND
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="RoboAdvisor MVP", page_icon="💼", layout="centered")
st.title("💼 RoboAdvisor MVP — Europa")
st.write("Prototipo educativo: asignación por perfil, aportación mensual (DCA) y rebalanceo semestral entre ETFs.")
st.info("**Aviso**: Esto es una simulación educativa. No es asesoramiento financiero ni gestiona dinero real.")

with st.sidebar:
    st.header("⚙️ Configuración")
    profile = st.selectbox("Perfil de riesgo", ["Conservador", "Moderado", "Agresivo"], index=2)
    w_eq, w_bd = profile_to_weights(profile)
    contrib = st.number_input("Aportación mensual (€)", 1, 10000, 300, step=10)
    rebalance = st.selectbox("Rebalanceo", ["Cada 6 meses", "Cada 12 meses", "Sin rebalanceo"], index=0)
    if rebalance == "Cada 6 meses":
        rb = 6
    elif rebalance == "Cada 12 meses":
        rb = 12
    else:
        rb = 0

    st.subheader("ETFs")
    eq_ticker = st.text_input("Ticker Acciones (VWCE.DE recomendado)", DEFAULT_EQUITY["ticker"])
    bd_ticker = st.text_input("Ticker Bonos (AGGH.DE recomendado)", DEFAULT_BOND["ticker"])
    start = st.text_input("Inicio histórico (YYYY-MM-DD)", "2015-01-01")

cfg = PortfolioConfig(
    equity_ticker=eq_ticker.strip(),
    bond_ticker=bd_ticker.strip(),
    equity_weight=w_eq,
    bond_weight=w_bd,
    monthly_contribution=float(contrib),
    rebalance_months=rb,
    start=start.strip() or "2015-01-01",
    end=None
)

run = st.button("▶️ Simular cartera")
if run:
    with st.spinner("Descargando datos y simulando..."):
        try:
            df, prices = simulate_dca(cfg)
            st.success("Simulación completa")
        except Exception as e:
            st.error("❌ No se pudo simular la cartera. Posibles causas: ticker incorrecto o sin datos.")
            st.caption(str(e))
            st.stop()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Valor de la cartera")
        st.metric("Valor final (€)", f"{df['total'].iloc[-1]:,.2f}")
        st.metric("Aportado (€)", f"{(df.shape[0]*cfg.monthly_contribution):,.2f}")
    with col2:
        stats = performance_stats(df["total"])
        st.subheader("Métricas")
        st.write(f"**CAGR**: {stats['CAGR']*100:.2f}%")
        st.write(f"**Volatilidad**: {stats['Vol']*100:.2f}%")
        st.write(f"**Max Drawdown**: {stats['MaxDD']*100:.2f}%")
        st.write(f"**Sharpe (rf≈0)**: {stats['Sharpe']:.2f}")

    st.subheader("Evolución de la cartera")
    fig, ax = plt.subplots()
    df[["equity_value", "bond_value"]].plot(ax=ax)
    ax.set_ylabel("€")
    ax.set_title("Componentes de la cartera")
    st.pyplot(fig)

    fig2, ax2 = plt.subplots()
    df["total"].plot(ax=ax2)
    ax2.set_ylabel("€")
    ax2.set_title("Valor total de la cartera")
    st.pyplot(fig2)

    st.subheader("Datos (últimas filas)")
    st.dataframe(df.tail(12))

    st.caption("Tickers por defecto: VWCE.DE (acciones globales, acumulativo) y AGGH.DE (bonos globales en EUR). "
               "Si no funcionan en tu región, sustituye por tickers de tu mercado.")
