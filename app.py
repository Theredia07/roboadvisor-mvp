import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import date, datetime
import io
import plotly.express as px

# Motor
from robo import (
    PortfolioConfig,
    simulate_dca,
    performance_stats,
    profile_to_weights,
)

# ─────────────────────────────────────────────────────────────────────
# BRANDING
# ─────────────────────────────────────────────────────────────────────
BRAND_NAME = "Fincontrol"  # <— cambia aquí si algún día quieres otro nombre

st.set_page_config(
    page_title=f"{BRAND_NAME} — Simulador de Inversión",
    page_icon="💼",
    layout="centered"
)

# ─────────────────────────────────────────────────────────────────────
# I18N (traducciones básicas ES / EN)
# ─────────────────────────────────────────────────────────────────────
LANGS = {
    "ES": {
        "title": f"💼 {BRAND_NAME} — Simulador de Inversión (Demo)",
        "intro": "Simula una inversión mensual en ETFs globales (acciones + bonos) con rebalanceo periódico. "
                 "Esto es **educativo**: no es asesoramiento financiero ni mueve dinero real.",
        "demo_note": "**Demo educativa** — Sin conexión a broker. Para aprender cómo se comportaría una cartera a lo largo del tiempo.",
        "sidebar_header": "🧭 Onboarding rápido",
        "age": "Tu edad",
        "horizon": "¿Cuántos años piensas invertir sin tocarlo?",
        "tolerance": "¿Qué tanto soportas subidas/bajadas?",
        "tol_help": "1 = No la soporto • 10 = La soporto totalmente",
        "monthly": "Aportación mensual (€)",
        "rebalance": "Rebalanceo",
        "reb_6": "Cada 6 meses",
        "reb_12": "Cada 12 meses",
        "reb_none": "Sin rebalanceo",
        "suggested_profile": "Perfil sugerido",
        "choose_profile": "Perfil (puedes cambiarlo)",
        "etfs_header": "ETFs por defecto (puedes cambiarlos)",
        "equity_label": "Acciones (recomendado: VWRA.L)",
        "bond_label": "Bonos (recomendado: AGGU.L)",
        "start_label": "Inicio histórico (YYYY-MM-DD)",
        "simulate": "▶️ Simular cartera",
        "no_hist": "ℹ️ No hay registro histórico para **{ticker}** desde **{start}** hasta **{today}**.",
        "no_data_range": "ℹ️ No hay datos suficientes entre **{start}** y **{today}** para estos tickers.",
        "sim_done": "✅ Simulación completa",
        "sim_fail": "❌ No se pudo simular la cartera. Revisa los tickers o inténtalo más tarde.",
        "summary": "Resumen",
        "final_value": "Valor final (€)",
        "contributed": "Aportado (€)",
        "metrics": "Métricas",
        "cagr": "**CAGR** (crecimiento anual compuesto)",
        "vol": "**Volatilidad** (aprox. anual)",
        "maxdd": "**Max Drawdown** (máx. caída)",
        "sharpe": "**Sharpe (rf≈0)**",
        "evolution": "Evolución de la cartera (interactiva)",
        "components_title": "Componentes: acciones (equity) y bonos (bond)",
        "total_title": "Valor total de la cartera",
        "last12": "Datos (últimos 12 meses)",
        "glossary": "📖 Cómo leer los resultados",
        "glossary_text": (
            "- **Valor de la cartera (Total):** lo que tendrías hoy si hubieras invertido cada mes.\n"
            "- **Aportado:** el dinero que pusiste (ej. 300 € × número de meses).\n"
            "- **Equity value:** valor de la parte de **acciones** (empresas globales).\n"
            "  - Crecen más a largo plazo, pero también suben y bajan más.\n"
            "- **Bond value:** valor de la parte de **bonos** (más estables, menor crecimiento).\n"
            "- **CAGR:** rendimiento medio anual compuesto.\n"
            "- **Volatilidad:** cuánto sube y baja la cartera. Más volatilidad = más riesgo.\n"
            "- **Max Drawdown:** la mayor caída histórica desde un máximo hasta un mínimo.\n"
            "- **Sharpe:** rentabilidad ajustada al riesgo (cuanto más alto, mejor).\n"
            "- **TIP:** si no ves datos, prueba con fecha de inicio desde **2018-01-01**."
        ),
        "table_howto_title": "ℹ️ Cómo leer la tabla de los últimos 12 meses",
        "table_howto_text": (
            "En la tabla se muestran los valores al final de cada mes:\n"
            "- **Equity Value**: valor de las acciones.\n"
            "- **Bond Value**: valor de los bonos.\n"
            "- **Cash**: dinero aún no invertido (normalmente 0).\n"
            "- **Total**: la **suma** de Equity + Bond + Cash."
        ),
        "feedback": "📝 Feedback rápido",
        "feedback_text": "¿Qué te gustaría mejorar? Deja tu idea aquí: [Formulario de feedback]({url}) *(1 minuto)*",
        "disclaimer": "Demo educativa. No es asesoramiento financiero ni mueve dinero real.",
        "language": "Idioma",
        "spanish": "Español",
        "english": "English",
        "date": "Fecha",
        "comp_label": "Componente",
        "hover_total": "Total",
    },
    "EN": {
        "title": f"💼 {BRAND_NAME} — Investment Simulator (Demo)",
        "intro": "Simulate monthly investing in global ETFs (equities + bonds) with periodic rebalancing. "
                 "This is **educational**: not financial advice and no real money is moved.",
        "demo_note": "**Educational demo** — No broker connection. Learn how a portfolio would behave over time.",
        "sidebar_header": "🧭 Quick onboarding",
        "age": "Your age",
        "horizon": "How many years will you invest without touching it?",
        "tolerance": "How much volatility can you stand?",
        "tol_help": "1 = I can't stand it • 10 = I can fully stand it",
        "monthly": "Monthly contribution (€)",
        "rebalance": "Rebalancing",
        "reb_6": "Every 6 months",
        "reb_12": "Every 12 months",
        "reb_none": "No rebalancing",
        "suggested_profile": "Suggested profile",
        "choose_profile": "Profile (you can change it)",
        "etfs_header": "Default ETFs (you can change them)",
        "equity_label": "Equities (recommended: VWRA.L)",
        "bond_label": "Bonds (recommended: AGGU.L)",
        "start_label": "Start date (YYYY-MM-DD)",
        "simulate": "▶️ Run simulation",
        "no_hist": "ℹ️ No historical data for **{ticker}** from **{start}** to **{today}**.",
        "no_data_range": "ℹ️ Not enough data between **{start}** and **{today}** for these tickers.",
        "sim_done": "✅ Simulation completed",
        "sim_fail": "❌ Could not run the simulation. Check tickers or try later.",
        "summary": "Summary",
        "final_value": "Final value (€)",
        "contributed": "Contributed (€)",
        "metrics": "Metrics",
        "cagr": "**CAGR** (compound annual growth rate)",
        "vol": "**Volatility** (approx. annual)",
        "maxdd": "**Max Drawdown**",
        "sharpe": "**Sharpe (rf≈0)**",
        "evolution": "Portfolio evolution (interactive)",
        "components_title": "Components: equities (equity) and bonds (bond)",
        "total_title": "Total portfolio value",
        "last12": "Data (last 12 months)",
        "glossary": "📖 How to read the results",
        "glossary_text": (
            "- **Portfolio value (Total):** what you'd have today if you invested monthly.\n"
            "- **Contributed:** money you put in (e.g., €300 × number of months).\n"
            "- **Equity value:** value of the **equities** part (global companies).\n"
            "  - Higher long-term growth but more ups and downs.\n"
            "- **Bond value:** value of the **bonds** part (more stable, lower growth).\n"
            "- **CAGR:** compound annual growth rate.\n"
            "- **Volatility:** how much the portfolio moves up/down. More volatility = more risk.\n"
            "- **Max Drawdown:** largest peak-to-trough decline.\n"
            "- **Sharpe:** risk-adjusted return (higher is better).\n"
            "- **TIP:** if you don't see data, try start date from **2018-01-01**."
        ),
        "table_howto_title": "ℹ️ How to read the last 12 months table",
        "table_howto_text": (
            "The table shows end-of-month values:\n"
            "- **Equity Value**: value of equities.\n"
            "- **Bond Value**: value of bonds.\n"
            "- **Cash**: money not yet invested (usually 0).\n"
            "- **Total**: the **sum** of Equity + Bond + Cash."
        ),
        "feedback": "📝 Quick feedback",
        "feedback_text": "What would you improve? Share here: [Feedback form]({url}) *(1 minute)*",
        "disclaimer": "Educational demo. Not financial advice and no real money is moved.",
        "language": "Language",
        "spanish": "Español",
        "english": "English",
        "date": "Date",
        "comp_label": "Component",
        "hover_total": "Total",
    }
}

def t(lang, key, **kwargs):
    txt = LANGS[lang][key]
    return txt.format(**kwargs) if kwargs else txt

# ─────────────────────────────────────────────────────────────────────
# SELECTOR DE IDIOMA (ES / EN)
# ─────────────────────────────────────────────────────────────────────
lang = st.sidebar.selectbox("Idioma / Language", ["ES", "EN"], index=0,
                            format_func=lambda x: f"{LANGS[x]['spanish']}" if x=="ES" else f"{LANGS[x]['english']}")

# TITULOS / INTRO
st.title(t(lang, "title"))
st.write(t(lang, "intro"))
st.info(t(lang, "demo_note"))

# ─────────────────────────────────────────────────────────────────────
# UTIL: verificación de histórico
# ─────────────────────────────────────────────────────────────────────
def tiene_historico(ticker: str, start: str) -> bool:
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
    st.header(t(lang, "sidebar_header"))
    edad = st.number_input(t(lang, "age"), min_value=18, max_value=90, value=18, step=1)
    horizonte = st.slider(t(lang, "horizon"), 1, 30, 7)
    tolerancia = st.slider(t(lang, "tolerance"), min_value=1, max_value=10, value=7, help=t(lang, "tol_help"))
    st.caption(t(lang, "tol_help"))
    aportacion = st.number_input(t(lang, "monthly"), 1, 10000, 300, step=10)

    rebalanceo_opt = st.selectbox(t(lang, "rebalance"),
                                  [t(lang,"reb_6"), t(lang,"reb_12"), t(lang,"reb_none")], index=0)
    rb = 6 if rebalanceo_opt == t(lang, "reb_6") else (12 if rebalanceo_opt == t(lang, "reb_12") else 0)

    # Sugerencia simple de perfil
    if horizonte >= 5 and tolerancia >= 7:
        perfil_sugerido = "Agresivo" if lang=="ES" else "Agresivo"  # mantenemos claves del motor en ES
    elif horizonte >= 3 and tolerancia >= 5:
        perfil_sugerido = "Moderado"
    else:
        perfil_sugerido = "Conservador"

    opciones = ["Conservador", "Moderado", "Agresivo"]
    idx_sugerido = opciones.index(perfil_sugerido)
    perfil = st.selectbox(t(lang, "choose_profile"), opciones, index=idx_sugerido)
    st.success(f"{t(lang,'suggested_profile')}: {perfil_sugerido} • {t(lang,'choose_profile').split('(')[0].strip()}: **{perfil}**")

    st.divider()
    st.subheader(t(lang, "etfs_header"))
    # Defaults estables en Yahoo:
    eq_ticker = st.text_input(t(lang, "equity_label"), "VWRA.L")
    bd_ticker = st.text_input(t(lang, "bond_label"), "AGGU.L")
    start = st.text_input(t(lang, "start_label"), "2018-01-01")

run = st.button(t(lang, "simulate"))

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
            st.warning(t(lang, "no_hist", ticker=eq_ticker, start=start, today=hoy))
        if not ok_bd:
            st.warning(t(lang, "no_hist", ticker=bd_ticker, start=start, today=hoy))
        st.stop()

    # Perfil elegido → pesos (motor espera "Conservador/Moderado/Agresivo")
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

    with st.spinner("Descargando datos y simulando..." if lang=="ES" else "Downloading data and simulating..."):
        try:
            df, prices = simulate_dca(cfg)
            if df is None or df.empty:
                st.warning(t(lang, "no_data_range", start=start, today=hoy))
                st.stop()
            st.success(t(lang, "sim_done"))
        except Exception as e:
            st.error(t(lang, "sim_fail"))
            st.caption(str(e))
            st.stop()

    # ─────────────────────────────────────────────────────────────────
    # KPIs / MÉTRICAS
    # ─────────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(t(lang, "summary"))
        valor_final = df["total"].iloc[-1]
        aportado = df.shape[0] * cfg.monthly_contribution
        st.metric(t(lang, "final_value"), f"{valor_final:,.2f}")
        st.metric(t(lang, "contributed"), f"{aportado:,.2f}")

    with col2:
        st.subheader(t(lang, "metrics"))
        stats = performance_stats(df["total"])
        st.write(f"{t(lang,'cagr')}: {stats['CAGR']*100:.2f}%")
        st.write(f"{t(lang,'vol')}: {stats['Vol']*100:.2f}%")
        st.write(f"{t(lang,'maxdd')}: {stats['MaxDD']*100:.2f}%")
        st.write(f"{t(lang,'sharpe')}: {stats['Sharpe']:.2f}")

    # ─────────────────────────────────────────────────────────────────
    # GRÁFICOS INTERACTIVOS (Plotly)
    # ─────────────────────────────────────────────────────────────────
    df_plot = df.copy()
    df_plot["date"] = df_plot.index

    st.subheader(t(lang, "evolution"))

    fig_comp = px.line(
        df_plot, x="date", y=["equity_value", "bond_value"],
        labels={"value": "€", "date": t(lang,"date"), "variable": t(lang,"comp_label")},
        title=t(lang, "components_title"),
    )
    fig_comp.update_traces(mode="lines+markers",
                           hovertemplate="%{x|%Y-%m-%d}<br>%{fullData.name}: €%{y:.2f}")
    st.plotly_chart(fig_comp, use_container_width=True)

    fig_tot = px.line(
        df_plot, x="date", y="total",
        labels={"total": "€", "date": t(lang,"date")},
        title=t(lang, "total_title"),
    )
    fig_tot.update_traces(mode="lines+markers",
                          hovertemplate="%{x|%Y-%m-%d}<br>"+t(lang,"hover_total")+": €%{y:.2f}")
    st.plotly_chart(fig_tot, use_container_width=True)

    st.subheader(t(lang, "last12"))
    st.dataframe(df.tail(12))

    # ─────────────────────────────────────────────────────────────────
    # EXPORTAR PDF
    # ─────────────────────────────────────────────────────────────────
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm

    def generar_pdf(buffer, brand, lang, perfil, aportacion, rebalanceo_opt, eq_ticker, bd_ticker, stats, valor_final, aportado):
        c = canvas.Canvas(buffer, pagesize=A4)
        W, H = A4
        x, y = 2*cm, H - 2*cm
        c.setFont("Helvetica-Bold", 16)
        title = f"{brand} — Informe de Simulación" if lang=="ES" else f"{brand} — Simulation Report"
        c.drawString(x, y, title)
        y -= 1.2*cm
        c.setFont("Helvetica", 11)
        c.drawString(x, y, (f"Fecha: {datetime.now():%Y-%m-%d %H:%M}" if lang=="ES" else f"Date: {datetime.now():%Y-%m-%d %H:%M}"))
        y -= 0.8*cm
        line1 = (f"Perfil: {perfil}  |  Aportación mensual: €{aportacion:,.2f}  |  Rebalanceo: {rebalanceo_opt}"
                 if lang=="ES" else
                 f"Profile: {perfil}  |  Monthly: €{aportacion:,.2f}  |  Rebalancing: {rebalanceo_opt}")
        c.drawString(x, y, line1)
        y -= 0.8*cm
        line2 = (f"ETFs — Acciones: {eq_ticker}  |  Bonos: {bd_ticker}"
                 if lang=="ES" else
                 f"ETFs — Equities: {eq_ticker}  |  Bonds: {bd_ticker}")
        c.drawString(x, y, line2)
        y -= 1.2*cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, ("Resultados" if lang=="ES" else "Results"))
        y -= 0.8*cm
        c.setFont("Helvetica", 11)
        c.drawString(x, y, (f"Valor final: €{valor_final:,.2f}" if lang=="ES" else f"Final value: €{valor_final:,.2f}"))
        y -= 0.6*cm
        c.drawString(x, y, (f"Aportado: €{aportado:,.2f}" if lang=="ES" else f"Contributed: €{aportado:,.2f}"))
        y -= 0.6*cm
        c.drawString(x, y, (f"CAGR: {stats['CAGR']*100:.2f}%  |  Volatilidad: {stats['Vol']*100:.2f}%"
                            if lang=="ES" else
                            f"CAGR: {stats['CAGR']*100:.2f}%  |  Volatility: {stats['Vol']*100:.2f}%"))
        y -= 0.6*cm
        c.drawString(x, y, (f"Max Drawdown: {stats['MaxDD']*100:.2f}%  |  Sharpe: {stats['Sharpe']:.2f}"))
        y -= 1.2*cm
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(x, y, ("Nota: Simulación educativa. No es asesoramiento financiero ni mueve dinero real."
                            if lang=="ES" else
                            "Note: Educational simulation. Not financial advice and no real money is moved."))
        c.showPage()
        c.save()

    pdf_buffer = io.BytesIO()
    generar_pdf(
        pdf_buffer, BRAND_NAME, lang, perfil, aportacion, rebalanceo_opt,
        eq_ticker, bd_ticker, stats, valor_final, aportado
    )
    st.download_button(
        label=("📄 Descargar PDF del informe" if lang=="ES" else "📄 Download PDF report"),
        data=pdf_buffer.getvalue(),
        file_name=f"{BRAND_NAME}_report_{datetime.now():%Y%m%d_%H%M}.pdf",
        mime="application/pdf"
    )

# ─────────────────────────────────────────────────────────────────────
# GLOSARIO / AYUDA
# ─────────────────────────────────────────────────────────────────────
st.divider()
st.subheader(t(lang, "glossary"))
with st.expander(t(lang, "glossary")):
    st.markdown(t(lang, "glossary_text"))
    st.markdown("---")
    st.markdown(f"### {t(lang, 'table_howto_title')}")
    st.markdown(t(lang, "table_howto_text"))

st.divider()
st.subheader(t(lang, "feedback"))
# 👇 Reemplaza TUENLACEAQUI por tu enlace real de Google Forms
feedback_url = "https://forms.gle/TUENLACEAQUI"
st.markdown(t(lang, "feedback_text", url=feedback_url))
st.caption(t(lang, "disclaimer"))
