# -*- coding: utf-8 -*-
import io
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

BRAND_NAME = "Fincontrol"
DEFAULTS = {
    "equity_ticker": "VWRA.L",
    "bond_ticker": "AGGU.L",
    "crypto_ticker": "BTC-USD",
    "start": "2018-01-01",
}
# 👇 Tu Google Form real:
FEEDBACK_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfKW6vS86U0hUh7hlLhJM6XUJwaSy7Ci_ZpxDGtqwUu55OEQQ/viewform?usp=header"

st.set_page_config(page_title=f"{BRAND_NAME} — Simulador de Inversión", page_icon="💼", layout="centered")

LANGS = {
    "ES": {
        "title": f"💼 {BRAND_NAME} — Simulador de Inversión (Demo)",
        "intro": "Simula aportes mensuales (DCA) en varios activos (acciones/ETF, bonos y cripto) con rebalanceo periódico. "
                 "Es **educativo**: no es asesoramiento financiero ni mueve dinero real.",
        "demo_note": "**Demo educativa** — Sin conexión a broker. Aprende cómo podría comportarse una cartera en el tiempo.",
        "language": "Idioma", "spanish": "Español", "english": "English",
        "currency": "Moneda", "eur": "EUR (€)", "usd": "USD ($)",
        "sidebar_header": "🧭 Onboarding rápido",
        "darkmode": "Tema oscuro",
        "age": "Tu edad", "horizon": "¿Cuántos años piensas invertir sin tocarlo?",
        "tolerance": "¿Qué tanto soportas subidas/bajadas?", "tol_help": "1 = No la soporto • 10 = La soporto totalmente",
        "monthly": "Aportación mensual", "monthly_help": "Introduce la aportación en la moneda seleccionada arriba.",
        "rebalance": "Rebalanceo (cada X meses)", "reb_opt_none": "Sin rebalanceo",
        "profiles_header": "Perfiles & Pesos", "choose_profile": "Perfil sugerido (puedes cambiarlo)",
        "custom_weights": "Ajusta pesos (suman 100%)", "equity_weight": "Acciones (%)",
        "bond_weight": "Bonos (%)", "crypto_weight": "Cripto (%)",
        "assets_header": "Activos por defecto (puedes cambiarlos)",
        "equity_label": "Acciones / ETF (ej: VWRA.L)", "bond_label": "Bonos / ETF (ej: AGGU.L)",
        "crypto_enable": "Incluir Cripto", "crypto_label": "Cripto (ej: BTC-USD)",
        "start_label": "Inicio histórico (YYYY-MM-DD)", "simulate": "▶️ Simular cartera",
        "no_hist": "ℹ️ No hay datos históricos para **{ticker}** desde **{start}** hasta **{today}**.",
        "no_data_range": "ℹ️ No hay datos suficientes entre **{start}** y **{today}** para estos activos.",
        "sim_done": "✅ Simulación completa", "sim_fail": "❌ No se pudo simular la cartera. Revisa los tickers o inténtalo más tarde.",
        "summary": "Resumen", "final_value": "Valor final", "contributed": "Aportado",
        "metrics": "Métricas", "cagr": "**CAGR** (crecimiento anual compuesto)",
        "vol": "**Volatilidad** (aprox. anual)", "maxdd": "**Max Drawdown** (máx. caída)", "sharpe": "**Sharpe (rf≈0)**",
        "risk_level": "**Nivel de riesgo estimado:** {level}",
        "concentration": "Concentración (HHI) y Nº efectivo de posiciones", "hhi": "HHI: {hhi:.3f} • Nº efectivo: {neff:.2f}",
        "signals": "Señales de tendencia (MA200)", "bearish": "⚠️ {ticker}: **bajista** (precio < MA200)",
        "not_bearish": "ℹ️ {ticker}: **no bajista** (precio ≥ MA200)",
        "evolution": "Evolución de la cartera (interactiva)", "components_title": "Componentes por valor",
        "total_title": "Valor total de la cartera", "date": "Fecha", "component": "Componente", "hover_total": "Total",
        "last12": "Datos (últimos 12 meses)",
        "glossary": "📖 Cómo leer los resultados",
        "glossary_text": (
            "- **DCA (Dollar-Cost Averaging):** aportar una cantidad fija cada período.\n"
            "- **Valor de la cartera (Total):** lo que tendrías hoy si hubieras invertido cada mes.\n"
            "- **Aportado:** suma de tus aportes (ej. 300 × nº de meses) en la moneda seleccionada.\n"
            "- **Equity (Acciones):** ETFs/acciones globales (mayor crecimiento, mayor volatilidad).\n"
            "- **Bond (Bonos):** ETFs de renta fija (más estables, menor crecimiento).\n"
            "- **Cripto:** activos como BTC/ETH (muy volátiles; opcionales).\n"
            "- **Rebalanceo:** volver a los pesos objetivo cada cierto tiempo (2/4/6/8/10/12 meses o sin rebalanceo).\n"
            "- **CAGR:** crecimiento anual compuesto.\n"
            "- **Volatilidad:** cuánto sube y baja la cartera (riesgo).\n"
            "- **Max Drawdown:** peor caída desde un máximo a un mínimo.\n"
            "- **Sharpe:** rentabilidad ajustada al riesgo (más alto, mejor).\n"
            "- **MA200:** media móvil de 200 días; si el precio < MA200, tendencia bajista simple.\n"
            "- **HHI (Concentración):** suma de pesos²; cuanto mayor, más concentrada.\n"
            "- **Nº efectivo:** 1/HHI; aproxima “cuántos activos independientes” tienes.\n"
            "- **Moneda:** los valores se convierten a la moneda seleccionada (EUR/USD) usando tipos de cambio de Yahoo.\n"
            "- **TIP:** si no ves datos, prueba inicio desde **2018-01-01**."
        ),
        "table_howto_title": "ℹ️ Cómo leer la tabla de los últimos 12 meses",
        "table_howto_text": (
            "La tabla muestra el valor al final de cada mes (en la moneda elegida):\n"
            "- **Equity Value**: valor de acciones.\n"
            "- **Bond Value**: valor de bonos.\n"
            "- **Crypto Value**: valor de cripto (si está activada).\n"
            "- **Cash**: efectivo no invertido (normalmente 0 tras rebalanceo).\n"
            "- **Total**: **suma** de todas las columnas anteriores."
        ),
        "pdf_btn": "📄 Descargar PDF del informe",
        "feedback": "📝 Feedback rápido",
        "feedback_text": "¿Qué mejorarías? Cuéntanos aquí: [Formulario de feedback]({url}) *(1 minuto)*",
        "disclaimer": "Demo educativa. No es asesoramiento financiero ni mueve dinero real.",
    },
    "EN": {
        "title": f"💼 {BRAND_NAME} — Investment Simulator (Demo)",
        "intro": "Simulate monthly contributions (DCA) into multiple assets (equities/ETFs, bonds and crypto) with periodic rebalancing. "
                 "This is **educational**: not financial advice and no real money is moved.",
        "demo_note": "**Educational demo** — No broker connection. Learn how a portfolio could behave over time.",
        "language": "Language", "spanish": "Español", "english": "English",
        "currency": "Currency", "eur": "EUR (€)", "usd": "USD ($)",
        "sidebar_header": "🧭 Quick onboarding",
        "darkmode": "Dark theme",
        "age": "Your age", "horizon": "How many years will you invest without touching it?",
        "tolerance": "How much volatility can you stand?", "tol_help": "1 = I can't stand it • 10 = I can fully stand it",
        "monthly": "Monthly contribution", "monthly_help": "Enter the contribution in the selected currency above.",
        "rebalance": "Rebalancing (every X months)", "reb_opt_none": "No rebalancing",
        "profiles_header": "Profiles & Weights", "choose_profile": "Suggested profile (you can change it)",
        "custom_weights": "Adjust weights (sum to 100%)", "equity_weight": "Equities (%)",
        "bond_weight": "Bonds (%)", "crypto_weight": "Crypto (%)",
        "assets_header": "Default assets (you can change them)",
        "equity_label": "Equities / ETF (e.g., VWRA.L)", "bond_label": "Bonds / ETF (e.g., AGGU.L)",
        "crypto_enable": "Include Crypto", "crypto_label": "Crypto (e.g., BTC-USD)",
        "start_label": "Start date (YYYY-MM-DD)", "simulate": "▶️ Run simulation",
        "no_hist": "ℹ️ No historical data for **{ticker}** from **{start}** to **{today}**.",
        "no_data_range": "ℹ️ Not enough data between **{start}** and **{today}** for these assets.",
        "sim_done": "✅ Simulation completed", "sim_fail": "❌ Could not run the simulation. Check tickers or try later.",
        "summary": "Summary", "final_value": "Final value", "contributed": "Contributed",
        "metrics": "Metrics", "cagr": "**CAGR** (compound annual growth rate)",
        "vol": "**Volatility** (approx. annual)", "maxdd": "**Max Drawdown**", "sharpe": "**Sharpe (rf≈0)**",
        "risk_level": "**Estimated risk level:** {level}",
        "concentration": "Concentration (HHI) & Effective number", "hhi": "HHI: {hhi:.3f} • Effective N: {neff:.2f}",
        "signals": "Trend signals (MA200)", "bearish": "⚠️ {ticker}: **bearish** (price < MA200)",
        "not_bearish": "ℹ️ {ticker}: **not bearish** (price ≥ MA200)",
        "evolution": "Portfolio evolution (interactive)", "components_title": "Components by value",
        "total_title": "Total portfolio value", "date": "Date", "component": "Component", "hover_total": "Total",
        "last12": "Data (last 12 months)",
        "glossary": "📖 How to read the results",
        "glossary_text": (
            "- **DCA (Dollar-Cost Averaging):** invest a fixed amount each period.\n"
            "- **Portfolio value (Total):** what you'd have today if you invested monthly.\n"
            "- **Contributed:** total contributions (e.g., 300 × months) in the selected currency.\n"
            "- **Equity:** global equities/ETFs (higher growth, higher volatility).\n"
            "- **Bond:** fixed-income ETFs (more stable, lower growth).\n"
            "- **Crypto:** assets like BTC/ETH (very volatile; optional).\n"
            "- **Rebalancing:** revert to target weights periodically (2/4/6/8/10/12 months or none).\n"
            "- **CAGR:** compound annual growth rate.\n"
            "- **Volatility:** how much the portfolio moves (risk).\n"
            "- **Max Drawdown:** worst peak-to-trough decline.\n"
            "- **Sharpe:** risk-adjusted return (higher is better).\n"
            "- **MA200:** 200-day moving average; price < MA200 = simple bearish signal.\n"
            "- **HHI (Concentration):** sum of weights²; higher = more concentrated.\n"
            "- **Effective number:** 1/HHI; approximates “how many independent assets”.\n"
            "- **Currency:** values are converted to the selected currency (EUR/USD) using Yahoo FX rates.\n"
            "- **TIP:** if you don't see data, try start date from **2018-01-01**."
        ),
        "table_howto_title": "ℹ️ How to read the last 12 months table",
        "table_howto_text": (
            "The table shows month-end values (in the selected currency):\n"
            "- **Equity Value**: equities value.\n"
            "- **Bond Value**: bonds value.\n"
            "- **Crypto Value**: crypto value (if enabled).\n"
            "- **Cash**: cash not invested (usually 0 after rebalancing).\n"
            "- **Total**: the **sum** of all previous columns."
        ),
        "pdf_btn": "📄 Download PDF report",
        "feedback": "📝 Quick feedback",
        "feedback_text": "What would you improve? Tell us here: [Feedback form]({url}) *(1 minute)*",
        "disclaimer": "Educational demo. Not financial advice and no real money is moved.",
    },
}
def t(lang, key, **kwargs):
    text = LANGS[lang][key]
    return text.format(**kwargs) if kwargs else text

# ── Idioma / Moneda / Dark mode ──────────────────────────────────────
lang = st.sidebar.selectbox(f"{t('ES','language')} / {t('EN','language')}",
                            ["ES", "EN"], index=0,
                            format_func=lambda x: LANGS[x]["spanish"] if x=="ES" else LANGS[x]["english"])
currency = st.sidebar.selectbox(t(lang, "currency"), ["EUR", "USD"], index=0,
                                format_func=lambda x: t(lang, "eur") if x=="EUR" else t(lang, "usd"))
CURRENCY_SYMBOL = "€" if currency == "EUR" else "$"
dark = st.sidebar.toggle(t(lang, "darkmode"), value=False)

# Branding (logo + intro)
LOGO_WORDMARK = "assets/fincontrol_wordmark.svg"
if Path(LOGO_WORDMARK).exists():
    col_logo, col_title = st.columns([1, 3])
    with col_logo:
        st.image(LOGO_WORDMARK, use_container_width=True)
    with col_title:
        st.title(t(lang, "title"))
        st.write(t(lang, "intro"))
else:
    st.title(t(lang, "title"))
    st.write(t(lang, "intro"))
st.info(t(lang, "demo_note"))

# CSS claro/oscuro
light_css = """
<style>
.block-container { max-width: 980px; }
h3, .stSubheader { border-left: 6px solid #16A34A22; padding-left: 10px; }
div.stMarkdown > div.card {
  background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 14px;
  padding: 14px 16px; box-shadow: 0 1px 2px rgba(0,0,0,.04); margin-bottom: 12px;
}
button[kind="primary"] { border-radius: 10px; }
</style>
"""
dark_css = """
<style>
.block-container { max-width: 980px; }
html, body, [data-testid="stAppViewContainer"] { background: #0B1220 !important; color: #EEF2F6; }
section[data-testid="stSidebar"] { background: #0F172A !important; }
h1,h2,h3,h4,h5,h6, label, span, p { color: #EEF2F6 !important; }
.stDataFrame tbody td, .stDataFrame thead th { color: #EEF2F6 !important; }
h3, .stSubheader { border-left: 6px solid #16A34A55; padding-left: 10px; }
div.stMarkdown > div.card {
  background: #111827; border: 1px solid #1F2937; border-radius: 14px;
  padding: 14px 16px; box-shadow: 0 1px 2px rgba(0,0,0,.3); margin-bottom: 12px;
}
button[kind="primary"] { border-radius: 10px; }
</style>
"""
st.markdown(dark_css if dark else light_css, unsafe_allow_html=True)

# ── Datos / proveedor ────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def yahoo_prices(ticker: str, start: str, end: str | None = None) -> pd.Series:
    df = yf.download(ticker.strip(), start=start.strip(), end=end, progress=False, auto_adjust=True)
    if df is None or df.empty:
        return pd.Series(dtype=float)
    s = df["Close"].dropna()
    s.index = pd.to_datetime(s.index)
    return s

@st.cache_data(show_spinner=False, ttl=86400)
def get_currency_of_ticker(ticker: str) -> str:
    try:
        info = yf.Ticker(ticker).fast_info
        cur = getattr(info, "currency", None)
        if cur: return cur
    except Exception:
        pass
    try:
        info2 = yf.Ticker(ticker).info
        cur = info2.get("currency")
        if cur: return cur
    except Exception:
        pass
    return "USD"

def fx_pair(src: str, dst: str) -> str | None:
    if src == dst: return None
    return f"{src}{dst}=X"

def convert_series_to(series: pd.Series, src_cur: str, dst_cur: str, start: str) -> pd.Series:
    if src_cur == dst_cur: return series
    pair = fx_pair(src_cur, dst_cur)
    fx = yahoo_prices(pair, start)
    if fx.empty:
        st.warning(f"FX no disponible para {src_cur}->{dst_cur} ({pair}). Se muestran valores sin convertir.")
        return series
    fx = fx.reindex(series.index).ffill().bfill()
    return series * fx

def has_history(ticker: str, start: str) -> bool:
    try:
        s = yahoo_prices(ticker, start)
        return not s.empty
    except Exception:
        return False

# ── Sidebar / controles ─────────────────────────────────────────────
with st.sidebar:
    st.header(t(lang, "sidebar_header"))
    edad = st.number_input(t(lang, "age"), min_value=18, max_value=90, value=18, step=1)
    horizonte = st.slider(t(lang, "horizon"), 1, 30, 7)
    tolerancia = st.slider(t(lang, "tolerance"), 1, 10, 7, help=t(lang, "tol_help"))
    st.caption(t(lang, "tol_help"))
    aportacion = st.number_input(t(lang, "monthly") + f" ({CURRENCY_SYMBOL})", 1, 10000, 300, step=10, help=t(lang,"monthly_help"))

    # Rebalanceo: 2/4/6/8/10/12 o sin rebalanceo
    reb_opts = [2, 4, 6, 8, 10, 12, t(lang, "reb_opt_none")]
    rebalanceo_opt = st.selectbox(t(lang, "rebalance"), reb_opts, index=2)
    rb = 0 if rebalanceo_opt == t(lang, "reb_opt_none") else int(rebalanceo_opt)

    st.subheader(t(lang, "profiles_header"))
    if horizonte >= 5 and tolerancia >= 7:
        perfil_sugerido = "Agresivo"; w_equity, w_bond, w_crypto = 80, 20, 0
    elif horizonte >= 3 and tolerancia >= 5:
        perfil_sugerido = "Moderado"; w_equity, w_bond, w_crypto = 50, 50, 0
    else:
        perfil_sugerido = "Conservador"; w_equity, w_bond, w_crypto = 30, 70, 0

    perfil = st.selectbox(t(lang, "choose_profile"),
                          ["Conservador", "Moderado", "Agresivo"],
                          index=["Conservador","Moderado","Agresivo"].index(perfil_sugerido))

    st.caption(t(lang, "custom_weights"))
    col_w1, col_w2, col_w3 = st.columns(3)
    with col_w1: w_equity = st.number_input(t(lang, "equity_weight"), 0, 100, w_equity, step=5)
    with col_w2: w_bond   = st.number_input(t(lang, "bond_weight"),   0, 100, w_bond,   step=5)
    with col_w3:
        include_crypto = st.checkbox(t(lang, "crypto_enable"), value=False)
        w_crypto = st.number_input(t(lang, "crypto_weight"), 0, 100, w_crypto, step=5, disabled=not include_crypto)

    total_w = max(1, w_equity + w_bond + (w_crypto if include_crypto else 0))
    w_equity_norm = round(100 * w_equity / total_w, 2)
    w_bond_norm   = round(100 * w_bond   / total_w, 2)
    w_crypto_norm = round(100 * (w_crypto if include_crypto else 0) / total_w, 2)

    st.divider()
    st.subheader(t(lang, "assets_header"))
    eq_ticker = st.text_input(t(lang, "equity_label"), DEFAULTS["equity_ticker"])
    bd_ticker = st.text_input(t(lang, "bond_label"), DEFAULTS["bond_ticker"])
    if include_crypto:
        cr_ticker = st.text_input(t(lang, "crypto_label"), DEFAULTS["crypto_ticker"])
    else:
        cr_ticker = None
    start = st.text_input(t(lang, "start_label"), DEFAULTS["start"])

run = st.button(t(lang, "simulate"))

# ── Simulación ───────────────────────────────────────────────────────
@dataclass
class Asset:
    ticker: str
    weight: float  # 0..1
    currency: str

def monthly_index_union(series_list: list[pd.Series]) -> pd.DatetimeIndex:
    idx = None
    for s in series_list:
        if s is None or s.empty: 
            continue
        m = s.resample("M").last().index
        idx = m if idx is None else idx.union(m)
    return pd.DatetimeIndex([]) if idx is None else idx.sort_values()

def simulate_dca_multi(assets: list[Asset], monthly_contribution: float, start: str, end: str | None,
                       rebalance_months: int, display_currency: str) -> tuple[pd.DataFrame, dict]:
    native_prices = {a.ticker: yahoo_prices(a.ticker, start, end) for a in assets}
    conv_prices   = {}
    for a in assets:
        s = native_prices[a.ticker]
        if s.empty: conv_prices[a.ticker] = s; continue
        s_conv = convert_series_to(s, a.currency, display_currency, start)
        conv_prices[a.ticker] = s_conv
    if all(s.empty for s in conv_prices.values()): return pd.DataFrame(), conv_prices

    m_idx = monthly_index_union([s for s in conv_prices.values()])
    if len(m_idx) == 0: return pd.DataFrame(), conv_prices

    prices_m = {t: s.reindex(m_idx).ffill() for t, s in conv_prices.items()}
    shares = {a.ticker: 0.0 for a in assets}; cash = 0.0
    target_w = {a.ticker: a.weight for a in assets}
    hist, months_since_reb = [], 0

    for d in m_idx:
        cash += monthly_contribution
        for a in assets:
            t = a.ticker; px = float(prices_m[t].loc[d])
            if px > 0:
                alloc = monthly_contribution * target_w[t]
                shares[t] += alloc / px
        months_since_reb += 1
        values = {t: shares[t] * float(prices_m[t].loc[d]) for t in shares}
        port_value = sum(values.values()) + cash
        if rebalance_months and months_since_reb >= rebalance_months and port_value > 0:
            target_values = {t: target_w[t] * port_value for t in shares}
            for t in shares:
                px = float(prices_m[t].loc[d])
                if px > 0:
                    diff = target_values[t] - values[t]
                    shares[t] += diff / px
            cash = 0.0; months_since_reb = 0
            values = {t: shares[t] * float(prices_m[t].loc[d]) for t in shares}
            port_value = sum(values.values()) + cash
        row = {"date": d, "cash": cash, "total": port_value}
        for a in assets:
            name = "equity_value" if a.ticker == eq_ticker else ("bond_value" if a.ticker == bd_ticker else "crypto_value")
            row[name] = values[a.ticker]
        hist.append(row)

    df = pd.DataFrame(hist).set_index("date")
    for c in ["equity_value", "bond_value", "crypto_value"]:
        if c not in df.columns: df[c] = 0.0
    return df, prices_m

def perf_stats(series: pd.Series) -> dict:
    r = series.pct_change().dropna()
    if r.empty: return {"CAGR": 0.0, "Vol": 0.0, "MaxDD": 0.0, "Sharpe": 0.0}
    years = (series.index[-1] - series.index[0]).days / 365.25
    cagr = (series.iloc[-1] / series.iloc[0]) ** (1 / years) - 1 if years > 0 else 0.0
    vol = r.std() * np.sqrt(12)
    cummax = series.cummax(); dd = series / cummax - 1.0; maxdd = dd.min()
    sharpe = (r.mean() * 12) / vol if vol > 0 else 0.0
    return {"CAGR": cagr, "Vol": vol, "MaxDD": maxdd, "Sharpe": sharpe}

def risk_level(vol: float, maxdd: float) -> str:
    if vol < 0.08 and maxdd > -0.15: return "Bajo / Low"
    if vol <= 0.15 or maxdd >= -0.30: return "Medio / Medium"
    return "Alto / High"

def hhi_and_neff(weights: dict[str, float]) -> tuple[float, float]:
    w = np.array([max(0.0, v) for v in weights.values()], dtype=float)
    if w.sum() <= 0: return 0.0, 0.0
    w = w / w.sum(); hhi = float(np.sum(w ** 2)); neff = float(1.0 / hhi) if hhi > 0 else 0.0
    return hhi, neff

def trend_is_bearish(ticker: str, start: str, display_currency: str) -> bool | None:
    s = yahoo_prices(ticker, start)
    if s.empty or len(s) < 200: return None
    src_cur = get_currency_of_ticker(ticker)
    s = convert_series_to(s, src_cur, display_currency, start)
    if len(s) < 200: return None
    ma200 = s.rolling(200).mean()
    return bool(s.iloc[-1] < ma200.iloc[-1])

if run:
    today = date.today().isoformat()
    check_tickers = [eq_ticker, bd_ticker] + ([cr_ticker] if (cr_ticker and include_crypto) else [])
    missing = [t for t in check_tickers if not has_history(t, start)]
    if missing:
        for tck in missing:
            st.warning(t(lang, "no_hist", ticker=tck, start=start, today=today))
        st.stop()

    eq_cur = get_currency_of_ticker(eq_ticker)
    bd_cur = get_currency_of_ticker(bd_ticker)
    assets = [
        Asset(eq_ticker, weight=(w_equity_norm/100.0), currency=eq_cur),
        Asset(bd_ticker, weight=(w_bond_norm/100.0),   currency=bd_cur),
    ]
    if include_crypto and cr_ticker:
        cr_cur = get_currency_of_ticker(cr_ticker)
        assets.append(Asset(cr_ticker, weight=(w_crypto_norm/100.0), currency=cr_cur))

    with st.spinner("Descargando datos y simulando..." if lang == "ES" else "Downloading data and simulating..."):
        df, prices_m = simulate_dca_multi(
            assets=assets, monthly_contribution=float(aportacion), start=start, end=None,
            rebalance_months=rb, display_currency=currency
        )
        if df is None or df.empty:
            st.warning(t(lang, "no_data_range", start=start, today=today)); st.stop()
        st.success(t(lang, "sim_done"))

    # KPIs
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(t(lang, "summary"))
        valor_final = float(df["total"].iloc[-1])
        aportado = float(df.shape[0] * float(aportacion))
        st.metric(t(lang, "final_value"), f"{CURRENCY_SYMBOL}{valor_final:,.2f}")
        st.metric(t(lang, "contributed"), f"{CURRENCY_SYMBOL}{aportado:,.2f}")
    with col2:
        st.subheader(t(lang, "metrics"))
        stats = perf_stats(df["total"])
        st.write(f"{t(lang,'cagr')}: {stats['CAGR']*100:.2f}%")
        st.write(f"{t(lang,'vol')}: {stats['Vol']*100:.2f}%")
        st.write(f"{t(lang,'maxdd')}: {stats['MaxDD']*100:.2f}%")
        st.write(f"{t(lang,'sharpe')}: {stats['Sharpe']:.2f}")
        st.write(t(lang, "risk_level", level=risk_level(stats["Vol"], stats["MaxDD"])))

    # Concentración
    st.subheader(t(lang, "concentration"))
    weights_pct = {a.ticker: a.weight*100 for a in assets}
    hhi, neff = hhi_and_neff({a.ticker: a.weight for a in assets})
    st.write(t(lang, "hhi", hhi=hhi, neff=neff))

    # Señales MA200
    st.subheader(t(lang, "signals"))
    for a in assets:
        sig = trend_is_bearish(a.ticker, start, currency)
        if sig is True: st.warning(t(lang, "bearish", ticker=a.ticker))
        elif sig is False: st.info(t(lang, "not_bearish", ticker=a.ticker))
        else: st.caption(f"{a.ticker}: {'No hay datos suficientes' if lang=='ES' else 'Insufficient data'} (MA200)")

    # Gráficos (Plotly) con tema según claro/oscuro
    st.subheader(t(lang, "evolution"))
    df_plot = df.copy(); df_plot["date"] = df_plot.index
    value_cols = [c for c in ["equity_value", "bond_value", "crypto_value"] if c in df_plot.columns]

    brand_seq_light = ["#16A34A", "#0EA5E9", "#F59E0B"]
    brand_seq_dark  = ["#34D399", "#60A5FA", "#FBBF24"]
    seq = brand_seq_dark if dark else brand_seq_light
    template = "plotly_dark" if dark else "plotly"

    fig_comp = px.line(df_plot, x="date", y=value_cols, template=template,
                       color_discrete_sequence=seq,
                       labels={"value": CURRENCY_SYMBOL, "date": t(lang,"date"), "variable": t(lang,"component")},
                       title=t(lang, "components_title"))
    fig_comp.update_traces(mode="lines+markers",
                           hovertemplate="%{x|%Y-%m-%d}<br>%{fullData.name}: "+CURRENCY_SYMBOL+"%{y:,.2f}")
    st.plotly_chart(fig_comp, use_container_width=True)

    fig_tot = px.line(df_plot, x="date", y="total", template=template,
                      color_discrete_sequence=[seq[0]],
                      labels={"total": CURRENCY_SYMBOL, "date": t(lang,"date")},
                      title=t(lang, "total_title"))
    fig_tot.update_traces(mode="lines+markers",
                          hovertemplate="%{x|%Y-%m-%d}<br>"+t(lang,"hover_total")+": "+CURRENCY_SYMBOL+"%{y:,.2f}")
    st.plotly_chart(fig_tot, use_container_width=True)

    st.subheader(t(lang, "last12"))
    tail_cols = [c for c in ["equity_value","bond_value","crypto_value","cash","total"] if c in df.columns]
    st.dataframe(df[tail_cols].tail(12).style.format({col: lambda v: f"{CURRENCY_SYMBOL}{v:,.2f}" for col in tail_cols if col!="date"}))

    # PDF
    def generar_pdf(buffer, brand, lang, perfil, aportacion, rebalanceo_opt, currency, weights_pct, tickers, stats, valor_final, aportado, hhi, neff):
        c = canvas.Canvas(buffer, pagesize=A4)
        W, H = A4; x, y = 2*cm, H - 2*cm
        c.setFont("Helvetica-Bold", 16)
        c.drawString(x, y, f"{brand} — {'Informe de Simulación' if lang=='ES' else 'Simulation Report'}")
        y -= 1.2*cm; c.setFont("Helvetica", 11)
        c.drawString(x, y, (f"Fecha: {datetime.now():%Y-%m-%d %H:%M}" if lang=='ES' else f"Date: {datetime.now():%Y-%m-%d %H:%M}"))
        y -= 0.8*cm
        line1 = (f"Perfil: {perfil}  |  Aportación mensual: {CURRENCY_SYMBOL}{aportacion:,.2f}  |  Rebalanceo: {rebalanceo_opt}"
                 if lang=='ES' else
                 f"Profile: {perfil}  |  Monthly: {CURRENCY_SYMBOL}{aportacion:,.2f}  |  Rebalancing: {rebalanceo_opt}")
        c.drawString(x, y, line1); y -= 0.8*cm
        c.drawString(x, y, f"Moneda: {currency}  |  Pesos: {weights_pct}"); y -= 0.6*cm
        c.drawString(x, y, f"Tickers: {tickers}"); y -= 1.0*cm
        c.setFont("Helvetica-Bold", 12); c.drawString(x, y, ("Resultados" if lang=='ES' else "Results")); y -= 0.8*cm
        c.setFont("Helvetica", 11)
        c.drawString(x, y, (f"Valor final: {CURRENCY_SYMBOL}{valor_final:,.2f}" if lang=='ES' else f"Final value: {CURRENCY_SYMBOL}{valor_final:,.2f}")); y -= 0.6*cm
        c.drawString(x, y, (f"Aportado: {CURRENCY_SYMBOL}{aportado:,.2f}" if lang=='ES' else f"Contributed: {CURRENCY_SYMBOL}{aportado:,.2f}")); y -= 0.6*cm
        c.drawString(x, y, f"CAGR: {stats['CAGR']*100:.2f}%  |  Vol: {stats['Vol']*100:.2f}%"); y -= 0.6*cm
        c.drawString(x, y, f"MaxDD: {stats['MaxDD']*100:.2f}%  |  Sharpe: {stats['Sharpe']:.2f}"); y -= 0.6*cm
        c.drawString(x, y, (f"Concentración (HHI): {hhi:.3f}  |  Nº efectivo: {neff:.2f}" if lang=='ES' else
                            f"Concentration (HHI): {hhi:.3f}  |  Effective N: {neff:.2f}"))
        y -= 1.0*cm; c.setFont("Helvetica-Oblique", 9)
        c.drawString(x, y, ("Nota: Simulación educativa. No es asesoramiento financiero ni mueve dinero real."
                            if lang=='ES' else
                            "Note: Educational simulation. Not financial advice and no real money is moved."))
        c.showPage(); c.save()

    pdf_buffer = io.BytesIO()
    generar_pdf(pdf_buffer, BRAND_NAME, lang, perfil, float(aportacion), rebalanceo_opt, currency,
                {k: f"{v:.1f}%" for k, v in weights_pct.items()}, list(weights_pct.keys()),
                stats, valor_final, aportado, hhi, neff)
    st.download_button(label=t(lang, "pdf_btn"), data=pdf_buffer.getvalue(),
                       file_name=f"{BRAND_NAME}_report_{datetime.now():%Y%m%d_%H%M}.pdf", mime="application/pdf")

# ── Glosario & Feedback ─────────────────────────────────────────────
st.divider()
st.subheader(t(lang, "glossary"))
with st.expander(t(lang, "glossary")):
    st.markdown(t(lang, "glossary_text"))
    st.markdown("---")
    st.markdown(f"### {t(lang, 'table_howto_title')}")
    st.markdown(t(lang, "table_howto_text"))

st.divider()
st.subheader(t(lang, "feedback"))
st.markdown(t(lang, "feedback_text", url=FEEDBACK_URL))
st.caption(t(lang, "disclaimer"))
