import streamlit as st
import pandas as pd

# Importamos el "motor" de la carpeta robo.py
from robo import (
    PortfolioConfig,
    simulate_dca,
    performance_stats,
    profile_to_weights,
)

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG GENERAL
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="TuRobo — Simulador de Inversión", page_icon="💼", layout="centered")

st.title("💼 TuRobo — Simulador de Inversión (Demo)")
st.write(
    "Simula una inversión mensual en ETFs globales (acciones + bonos) con rebalanceo periódico. "
    "Esto es **educativo**: no es asesoramiento financiero ni mueve dinero real."
)
st.info("**Demo educativa** — Sin conexión a broker. Para aprender cómo se comportaría una cartera a lo largo del tiempo.")

# ──────────────────────────────────────────────────────────────────────────────
# ONBOARDING (4 preguntas) → sugiere perfil
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🧭 Onboarding rápido")
    edad = st.number_input("Tu edad", min_value=18, max_value=90, value=18, step=1)
    horizonte = st.slider("¿Cuántos años piensas invertir sin tocarlo?", 1, 30, 7)
    tolerancia = st.slider("¿Qué tanto soportas subidas/bajadas?", 1, 10, 7)
    aportacion = st.number_input("Aportación mensual (€)", 1, 10000, 300, step=10)

    # Rebalanceo
    rebalanceo_opt = st.selectbox("Rebalanceo", ["Cada 6 meses", "Cada 12 meses", "Sin rebalanceo"], index=0)
    rb = 6 if rebalanceo_opt == "Cada 6 meses" else (12 if rebalanceo_opt == "Cada 12 meses" else 0)

    # Sugerencia de perfil muy simple
    if horizonte >= 5 and tolerancia >= 7:
        perfil = "Agresivo"
    elif horizonte >= 3 and tolerancia >= 5:
        perfil = "Moderado"
    else:
        perfil = "Conservador"
    st.success(f"**Perfil sugerido:** {perfil}")

    st.divider()
    st.subheader("ETFs por defecto (puedes cambiarlos)")
    # Por defecto usamos tickers que funcionan en Yahoo Finance:
    # Acciones globales (Vanguard FTSE All-World Acc) y Bonos globales (EUR Hedged, Acc)
    eq_ticker = st.text_input("Acciones (recomendado: VWCE.DE)", "VWCE.DE")
    bd_ticker = st.text_input("Bonos (recomendado: AGGH.MI)", "AGGH.MI")

    start = st.text_input("Inicio histórico (YYYY-MM-DD)", "2015-01-01")

run = st.button("▶️ Simular cartera")

# ──────────────────────────────────────────────────────────────────────────────
# SIMULACIÓN
# ──────────────────────────────────────────────────────────────────────────────
if run:
    # Convertimos perfil → pesos objetivo (usa tabla de robo.py)
    w_eq, w_bd = profile_to_weights(perfil)

    cfg = PortfolioConfig(
        equity_ticker=eq_ticker.strip(),
        bond_ticker=bd_ticker.strip(),
        equity_weight=w_eq,
        bond_weight=w_bd,
        monthly_contribution=float(aportacion),
        rebalance_months=rb,
        start=start.strip() or "2015-01-01",
        end=None,
    )

    with st.spinner("Descargando datos y simulando..."):
        try:
            df, prices = simulate_dca(cfg)
            # Si llega vacío, levantamos un error comprensible
            if df is None or df.empty:
                raise ValueError("No hay datos para los tickers/fechas seleccionados.")
            st.success("✅ Simulación completa")
        except Exception as e:
            st.error("❌ No se pudo simular la cartera. Revisa los tickers o inténtalo más tarde.")
            st.caption(str(e))
            st.stop()

    # ──────────────────────────────────────────────────────────────────────────
    # KPIs y métricas
    # ──────────────────────────────────────────────────────────────────────────
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

    # ──────────────────────────────────────────────────────────────────────────
    # GRÁFICOS (import tardío para acelerar carga)
    # ──────────────────────────────────────────────────────────────────────────
    import matplotlib.pyplot as plt

    st.subheader("Evolución de la cartera")
    fig, ax = plt.subplots()
    df[["equity_value", "bond_value"]].plot(ax=ax)
    ax.set_ylabel("€")
    ax.set_title("Componentes: acciones (equity) y bonos (bond)")
    st.pyplot(fig)

    fig2, ax2 = plt.subplots()
    df["total"].plot(ax=ax2)
    ax2.set_ylabel("€")
    ax2.set_title("Valor total de la cartera")
    st.pyplot(fig2)

    st.subheader("Datos (últimos 12 meses)")
    st.dataframe(df.tail(12))

# ──────────────────────────────────────────────────────────────────────────────
# GLOSARIO / AYUDA
# ──────────────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("📖 Cómo leer los resultados")
with st.expander("Explicación de métricas y valores"):
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
""")

st.divider()
st.subheader("📝 Feedback rápido")
st.markdown(
    "¿Qué te gustaría mejorar? Deja tu idea aquí: "
    "[Formulario de feedback](https://forms.gle/tu-form) *(1 minuto)*"
)
st.caption("Demo educativa. No es asesoramiento financiero ni mueve dinero real.")
