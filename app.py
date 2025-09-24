import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import date

# Motor
from robo import (
    PortfolioConfig,
    simulate_dca,
    performance_stats,
    profile_to_weights,
)

# ─────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TuRobo — Simulador de Inversión",
    page_icon="💼",
    layout="centered"
)

st.title("💼 TuRobo — Simulador de Inversión (Demo)")
st.write(
    "Simula una inversión mensual en ETFs globales (acciones + bonos) con rebalanceo periódico. "
    "Esto es **educativo**: no es asesoramiento financiero ni mueve dinero real."
)
st.info("**Demo educativa** — Sin conexión a broker. Para aprender cómo se comportaría una cartera a lo largo del tiempo.")

# ─────────────────────────────────────────────────────────────────────
# UTIL: verificación de histórico
# ─────────────────────────────────────────────────────────────────────
def tiene_historico(ticker: str, start: str) -> bool:
    """
    Devuelve True si Yahoo Finance tiene datos para el ticker desde 'start'.
    """
    try:
        df_ = yf.download(ticker.strip(), start=start.strip() or "2018-01-01",
                          progress=False, auto_adjust=True)
        return not df_.empty
    except Exception:
        return False

# ─────────────────────────────────────────────────────────────────────
# ONBOARDING + CONTROLES
# ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🧭 Onboarding rápido")
    edad = st.number_input("Tu edad", min_value=18, max_value=90, value=18, step=1)
    horizonte = st.slider("¿Cuántos años piensas invertir sin tocarlo?", 1, 30, 7)
    tolerancia = st.slider("¿Qué tanto soportas subidas/bajadas?", 1, 10, 7)
    aportacion = st.number_input("Aportación mensual (€)", 1, 10000, 300, step=10)

    rebalanceo_opt = st.selectbox("Rebalanceo", ["Cada 6 meses", "Cada 12 meses", "Sin rebalanceo"], index=0)
    rb = 6 if rebalanceo_opt == "Cada 6 meses" else (12 if rebalanceo_opt == "Cada 12 meses" else 0)

    # Sugerencia simple de perfil
    if horizonte >= 5 and tolerancia >= 7:
        perfil_sugerido = "Agresivo"
    elif horizonte >= 3 and tolerancia >= 5:
        perfil_sugerido = "Moderado"
    else:
        perfil_sugerido = "Conservador"

    # Usuario puede cambiarlo
    opciones = ["Conservador", "Moderado", "Agresivo"]
    idx_sugerido = opciones.index(perfil_sugerido)
    perfil = st.selectbox("Perfil (puedes cambiarlo)", opciones, index=idx_sugerido)
    st.success(f"Perfil sugerido: {perfil_sugerido} • Perfil elegido: **{perfil}**")

    st.divider()
    st.subheader("ETFs por defecto (puedes cambiarlos)")
    # Defaults que funcionan en Yahoo Finance:
    eq_ticker = st.text_input("Acciones (recomendado: VWCE.DE)", "VWCE.DE")
    bd_ticker = st.text_input("Bonos (recomendado: AGGU.L)", "AGGU.L")

    # Por defecto 2018 porque muchos bonos tienen histórico desde ~2017/2018
    start = st.text_input("Inicio histórico (YYYY-MM-DD)", "2018-01-01")

run = st.button("▶️ Simular cartera")

# ─────────────────────────────────────────────────────────────────────
# SIMULACIÓN
# ─────────────────────────────────────────────────────────────────────
if run:
    hoy = date.today().isoformat()

    # Validar histórico antes de simular
    ok_eq = tiene_historico(eq_ticker, start)
    ok_bd = tiene_historico(bd_ticker, start)

    if not ok_eq or not ok_bd:
        if not ok_eq:
            st.warning(f"ℹ️ No hay registro histórico para **{eq_ticker}** desde **{start}** hasta **{hoy}**.")
        if not ok_bd:
            st.warning(f"ℹ️ No hay registro histórico para **{bd_ticker}** desde **{start}** hasta **{hoy}**.")
        st.stop()

    # Perfil elegido → pesos
    w_eq, w_bd = profile_to_weights(perfil)

    cfg = PortfolioConfig(
        equity_ticker=eq_ticker.strip(),
        bond_ticker=bd_ticker.strip(),
        equity_weight=w_eq,
        bond_weight=w_bd,
        monthly_contribution=float(aportacion),
        rebalance_months=rb,
        start=start.strip() or "2018-01-01",
        end=None,
    )

    with st.spinner("Descargando datos y simulando..."):
        try:
            df, prices = simulate_dca(cfg)
            if df is None or df.empty:
                st.warning(f"ℹ️ No hay datos suficientes entre **{start}** y **{hoy}** para estos tickers.")
                st.stop()
            st.success("✅ Simulación completa")
        except Exception as e:
            st.error("❌ No se pudo simular la cartera. Revisa los tickers o inténtalo más tarde.")
            st.caption(str(e))
            st.stop()

    # ─────────────────────────────────────────────────────────────────
    # KPIs / MÉTRICAS
    # ─────────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Resumen")
        valor_final = df["total"].iloc[-1]
        aportado = df.shape[0] * cfg.monthly_contribution
        st.metric("Valor final (€)", f"{valor_final:,.2f}")
        st.metric("Aportado (€)", f"{aportado:,.2f}")

    with col2:
        st.subheader("Métricas")
        stats = performance_stats(df["total"])
        st.write(f"**CAGR** (crecimiento anual compuesto): {stats['CAGR']*100:.2f}%")
        st.write(f"**Volatilidad** (aprox. anual): {stats['Vol']*100:.2f}%")
        st.write(f"**Max Drawdown** (máx. caída): {stats['MaxDD']*100:.2f}%")
        st.write(f"**Sharpe (rf≈0)**: {stats['Sharpe']:.2f}")

    # ─────────────────────────────────────────────────────────────────
    # GRÁFICOS INTERACTIVOS (Plotly)
    # ─────────────────────────────────────────────────────────────────
    import plotly.express as px

    # Asegurar columna 'date' para el eje X
    df_plot = df.copy()
    df_plot["date"] = df_plot.index

    st.subheader("Evolución de la cartera (interactiva)")

    # 1) Componentes: acciones y bonos
    fig_comp = px.line(
        df_plot,
        x="date",
        y=["equity_value", "bond_value"],
        labels={"value": "€", "date": "Fecha", "variable": "Componente"},
        title="Componentes: acciones (equity) y bonos (bond)",
    )
    fig_comp.update_traces(mode="lines+markers",
                           hovertemplate="%{x|%Y-%m-%d}<br>%{fullData.name}: €%{y:.2f}")
    st.plotly_chart(fig_comp, use_container_width=True)

    # 2) Total de la cartera
    fig_tot = px.line(
        df_plot,
        x="date",
        y="total",
        labels={"total": "€", "date": "Fecha"},
        title="Valor total de la cartera",
    )
    fig_tot.update_traces(mode="lines+markers",
                          hovertemplate="%{x|%Y-%m-%d}<br>Total: €%{y:.2f}")
    st.plotly_chart(fig_tot, use_container_width=True)

    st.subheader("Datos (últimos 12 meses)")
    st.dataframe(df.tail(12))

# ─────────────────────────────────────────────────────────────────────
# GLOSARIO / AYUDA
# ─────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("📖 Cómo leer los resultados")
with st.expander("Explicación de métrricas y valores"):
    st.markdown("""
- **Valor de la cartera (Total):** lo que tendrías hoy si hubieras invertido cada mes.
- **Aportado:** el dinero que tú pusiste (ej. 300 € × número de meses).
- **Equity value:** valor de la parte de **acciones** (empresas globales como Apple, Nestlé, Samsung).
  - Crecen más a largo plazo, pero también suben y bajan más.
- **Bond value:** valor de la parte de **bonos** (préstamos a gobiernos y empresas).
  - Más estables, pero con menos crecimiento.
- **CAGR:** rendimiento medio anual compuesto (ej. 7 % = creció en promedio 7 % cada año).
- **Volatilidad:** cuánto sube y baja la cartera. Más volatilidad = más riesgo.
- **Max Drawdown:** la mayor caída histórica desde un máximo hasta un mínimo.
- **Sharpe:** rentabilidad ajustada al riesgo (cuanto más alto, mejor).
- **TIP:** si no ves datos, prueba con una fecha de inicio desde **2018-01-01**.
""")

st.divider()
st.subheader("📝 Feedback rápido")
st.markdown(
    "¿Qué te gustaría mejorar? Deja tu idea aquí: "
    "[Formulario de feedback](https://forms.gle/tu-form) *(1 minuto)*"
)
st.caption("Demo educativa. No es asesoramiento financiero ni mueve dinero real.")
