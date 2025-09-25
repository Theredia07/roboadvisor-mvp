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

# ───────────────────────────── CONFIG ─────────────────────────────
BRAND_NAME = "Fincontrol"
LOGO_WORDMARK = "assets/fincontrol_wordmark.svg"  # asegúrate de subirlo
FEEDBACK_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfKW6vS86U0hUh7hlLhJM6XUJwaSy7Ci_ZpxDGtqwUu55OEQQ/viewform?usp=header"

DEFAULTS = {
    "equity_ticker": "VWRA.L",  # ETF global acciones (LSE, USD)
    "bond_ticker": "AGGU.L",    # ETF global bonos (LSE, USD)
    "crypto_ticker": "BTC-USD",
    "start": "2018-01-01",
}

st.set_page_config(page_title=f"{BRAND_NAME} — Simulador de Inversión", page_icon="💼", layout="wide")

# ───────────────────────────── TEXTOS ─────────────────────────────
LANGS = {
    "ES": {
        "slogan": "Tu dinero, bajo control.",
        "language": "Idioma", "spanish": "Español", "english": "English",
        "currency": "Moneda", "eur": "EUR (€)", "usd": "USD ($)",
        "darkmode": "Tema oscuro",
        "demo_note": "Demo educativa — Sin conexión a broker. Aprende cómo podría comportarse una cartera en el tiempo.",
        "sidebar_header": "🧭 Onboarding rápido",
        "age": "Tu edad",
        "horizon": "¿Cuántos años sin tocar la inversión?",
        "tolerance": "¿Qué tanto soportas subidas/bajadas?",
        "tol_help": "1 = Nada • 10 = Totalmente",
        "monthly": "Aportación mensual",
        "monthly_help": "Introduce la aportación en la moneda seleccionada.",
        "rebalance": "Rebalanceo (cada X meses)",
        "reb_opt_none": "Sin rebalanceo",
        "profiles_header": "Perfiles & Pesos",
        "choose_profile": "Perfil sugerido (editable)",
        "custom_weights": "Ajusta pesos (suman 100%)",
        "equity_weight": "Acciones (%)",
        "bond_weight": "Bonos (%)",
        "crypto_weight": "Cripto (%)",
        "assets_header": "Activos por defecto (cambiables)",
        "equity_label": "Acciones / ETF (p.ej., VWRA.L)",
        "bond_label": "Bonos / ETF (p.ej., AGGU.L)",
        "crypto_enable": "Incluir cripto",
        "crypto_label": "Cripto (p.ej., BTC-USD)",
        "start_label": "Inicio histórico (YYYY-MM-DD)",
        "suggest_shortcut": "Atajos de sugerencias",
        "suggest_eq": "Sugeridos (Acciones)",
        "suggest_bd": "Sugeridos (Bonos)",
        "fill": "Rellenar",
        "simulate": "▶️ Simular cartera",
        "no_hist": "No hay datos para **{ticker}** desde **{start}** hasta **{today}**.",
        "try_alt": "Alternativas recomendadas",
        "use_date": "Usar fecha sugerida",
        "cant_simulate": "No pudimos simular porque faltan datos para algunos activos o desde la fecha elegida.",
        "no_data_range": "No hay datos suficientes entre **{start}** y **{today}** para estos activos.",
        "sim_done": "Simulación completa",
        "summary": "Resumen", "final_value": "Valor final", "contributed": "Aportado",
        "metrics": "Métricas",
        "cagr": "CAGR", "vol": "Volatilidad (aprox. anual)", "maxdd": "Max Drawdown", "sharpe": "Sharpe (rf≈0)",
        "risk_level": "Nivel de riesgo estimado: {level}",
        "concentration": "Concentración (HHI) y Nº efectivo",
        "hhi": "HHI: {hhi:.3f} • Nº efectivo: {neff:.2f}",
        "signals": "Señales de tendencia (MA200)",
        "bearish": "⚠️ {ticker} bajista (precio < MA200)",
        "not_bearish": "ℹ️ {ticker} no bajista (precio ≥ MA200)",
        "evolution": "Evolución de la cartera (interactiva)",
        "components_title": "Componentes por valor",
        "total_title": "Valor total de la cartera",
        "date": "Fecha", "component": "Componente", "hover_total": "Total",
        "last12": "Datos (últimos 12 meses)",
        "glossary": "📖 Cómo leer los resultados",
        "glossary_text": (
            "- **DCA:** aportas una cantidad fija cada mes.\n"
            "- **Total:** lo que tendrías hoy con esos aportes.\n"
            "- **Rebalanceo:** volver a los pesos objetivo (2/4/6/8/10/12 meses o sin).\n"
            "- **CAGR/Vol/MaxDD/Sharpe:** rendimiento y riesgo.\n"
            "- **MA200:** media móvil 200 días (tendencia simple).\n"
            "- **HHI/Nº efectivo:** concentración/diversificación.\n"
            "- **Moneda:** conversión a EUR/USD con tipos de Yahoo.\n"
            "- **TIP:** si no ves datos, prueba inicio desde **2018-01-01**."
        ),
        "table_howto_title": "Cómo leer la tabla de los últimos 12 meses",
        "table_howto_text": "Valores de fin de mes: Equity, Bond, Crypto, Cash y **Total** (suma).",
        "pdf_btn": "📄 Descargar PDF del informe",
        "feedback": "📝 Feedback rápido",
        "feedback_text": "¿Qué mejorarías? Dínoslo aquí: [Formulario]({url}) *(1 min)*",
        "disclaimer": "Demo educativa. No es asesoramiento financiero ni mueve dinero real.",
    },
    "EN": {
        "slogan": "Your money, under control.",
        "language": "Language", "spanish": "Español", "english": "English",
        "currency": "Currency", "eur": "EUR (€)", "usd": "USD ($)",
        "darkmode": "Dark theme",
        "demo_note": "Educational demo — No broker connection.",
        "sidebar_header": "🧭 Quick onboarding",
        "age": "Your age",
        "horizon": "How many years without touching it?",
        "tolerance": "How much volatility can you stand?",
        "tol_help": "1 = None • 10 = Fully",
        "monthly": "Monthly contribution",
        "monthly_help": "Enter the contribution in the selected currency.",
        "rebalance": "Rebalancing (every X months)",
        "reb_opt_none": "No rebalancing",
        "profiles_header": "Profiles & Weights",
        "choose_profile": "Suggested profile (editable)",
        "custom_weights": "Adjust weights (sum to 100%)",
        "equity_weight": "Equities (%)",
        "bond_weight": "Bonds (%)",
        "crypto_weight": "Crypto (%)",
        "assets_header": "Default assets (changeable)",
        "equity_label": "Equities / ETF (e.g., VWRA.L)",
        "bond_label": "Bonds / ETF (e.g., AGGU.L)",
        "crypto_enable": "Include crypto",
        "crypto_label": "Crypto (e.g., BTC-USD)",
        "start_label": "Start date (YYYY-MM-DD)",
        "suggest_shortcut": "Suggestion shortcuts",
        "suggest_eq": "Suggested (Equities)",
        "suggest_bd": "Suggested (Bonds)",
        "fill": "Fill",
        "simulate": "▶️ Run simulation",
        "no_hist": "No data for **{ticker}** from **{start}** to **{today}**.",
        "try_alt": "Recommended alternatives",
        "use_date": "Use suggested date",
        "cant_simulate": "We couldn't simulate because data is missing for some assets or from the chosen date.",
        "no_data_range": "Not enough data between **{start}** and **{today}** for these assets.",
        "sim_done": "Simulation completed",
        "summary": "Summary", "final_value": "Final value", "contributed": "Contributed",
        "metrics": "Metrics",
        "cagr": "CAGR", "vol": "Volatility (approx. annual)", "maxdd": "Max Drawdown", "sharpe": "Sharpe (rf≈0)",
        "risk_level": "Estimated risk level: {level}",
        "concentration": "Concentration (HHI) & Effective number",
        "hhi": "HHI: {hhi:.3f} • Effective N: {neff:.2f}",
        "signals": "Trend signals (MA200)",
        "bearish": "⚠️ {ticker} bearish (price < MA200)",
        "not_bearish": "ℹ️ {ticker} not bearish (price ≥ MA200)",
        "evolution": "Portfolio evolution (interactive)",
        "components_title": "Components by value",
        "total_title": "Total portfolio value",
        "date": "Date", "component": "Component", "hover_total": "Total",
        "last12": "Data (last 12 months)",
        "glossary": "How to read the results",
        "glossary_text": "Month-end values: Equity, Bond, Crypto, Cash and **Total** (sum).",
        "pdf_btn": "📄 Download PDF report",
        "feedback": "📝 Quick feedback",
        "feedback_text": "Tell us here: [Form]({url}) *(1 min)*",
        "disclaimer": "Educational demo. Not financial advice; no real money moved.",
    },
}
def t(lang, key, **kwargs):
    txt = LANGS[lang][key]
    return txt.format(**kwargs) if kwargs else txt

# ────────────────────────── HEADER / BRANDING ─────────────────────────
# Controles arriba (idioma, moneda, tema) en el sidebar
lang = st.sidebar.selectbox(f"{t('ES','language')} / {t('EN','language')}",
                            ["ES", "EN"], index=0,
                            format_func=lambda x: LANGS[x]["spanish"] if x=="ES" else LANGS[x]["english"])
currency = st.sidebar.selectbox(t(lang, "currency"), ["EUR", "USD"], index=0,
                                format_func=lambda x: t(lang, "eur") if x=="EUR" else t(lang, "usd"))
CURRENCY_SYMBOL = "€" if currency == "EUR" else "$"
dark = st.sidebar.toggle(t(lang, "darkmode"), value=False)

# --- HEADER con logo (robusto para SVG) ---
from pathlib import Path

def render_brand_header():
    svg_path = Path("assets/fincontrol_wordmark.svg")
    png_path = Path("assets/fincontrol_wordmark.png")

    if svg_path.exists():
        svg = svg_path.read_text(encoding="utf-8")
        st.markdown(
            f"""
            <div style="display:flex; flex-direction:column; align-items:center; gap:.35rem; margin:.4rem 0 1rem 0;">
                <div style="max-width:560px; width:60%; min-width:260px; height:auto;">
                    {svg}
                </div>
                <div style="font-size:1.05rem; opacity:.85;">{t(lang,'slogan')}</div>
            </div>
            <hr style="margin:.4rem 0 1.2rem 0; opacity:.25;">
            """,
            unsafe_allow_html=True
        )
    elif png_path.exists():
        st.markdown(
            f"""
            <div style="display:flex; flex-direction:column; align-items:center; gap:.35rem; margin:.4rem 0 1rem 0;">
                <img src="{png_path.as_posix()}" alt="{BRAND_NAME}" style="max-width:560px; width:60%; min-width:260px; height:auto;">
                <div style="font-size:1.05rem; opacity:.85;">{t(lang,'slogan')}</div>
            </div>
            <hr style="margin:.4rem 0 1.2rem 0; opacity:.25%;">
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning("No se encontró el logo en `assets/`. Sube `fincontrol_wordmark.svg` o `fincontrol_wordmark.png`.")

render_brand_header()
st.info(t(lang, "demo_note"))

# CSS para airear UI
base_css = """
<style>
.block-container { max-width: 1140px; }
section[data-testid="stSidebar"] { min-width: 340px; }
section[data-testid="stSidebar"] * { line-height: 1.25rem; }
.sidebar-spacer { height: 10px; }
h3, .stSubheader { border-left: 6px solid #16A34A22; padding-left: 10px; }
div.card { background:#FFFFFF; border:1px solid #E5E7EB; border-radius:14px;
           padding:14px 16px; box-shadow:0 1px 2px rgba(0,0,0,.04); margin-bottom:12px; }
</style>
"""
dark_css = """
<style>
html, body, [data-testid="stAppViewContainer"] { background:#0B1220 !important; color:#EEF2F6; }
section[data-testid="stSidebar"] { background:#0F172A !important; }
h1,h2,h3,h4,h5,h6, label, span, p { color:#EEF2F6 !important; }
.stDataFrame tbody td, .stDataFrame thead th { color:#EEF2F6 !important; }
h3, .stSubheader { border-left:6px solid #16A34A55; padding-left:10px; }
div.card { background:#111827; border:1px solid #1F2937; border-radius:14px;
           padding:14px 16px; box-shadow:0 1px 2px rgba(0,0,0,.3); margin-bottom:12px; }
</style>
"""
st.markdown(base_css + (dark_css if dark else ""), unsafe_allow_html=True)

# ────────────────────────── DATOS / HELPERS ──────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def yahoo_prices(ticker, start, end=None):
    df = yf.download(ticker.strip(), start=start.strip(), end=end, progress=False, auto_adjust=True)
    if df is None or df.empty:
        return pd.Series(dtype=float)
    s = df["Close"].dropna()
    s.index = pd.to_datetime(s.index)
    return s

@st.cache_data(show_spinner=False, ttl=86400)
def get_currency_of_ticker(ticker):
    try:
        info = yf.Ticker(ticker).fast_info
        cur = getattr(info, "currency", None)
        if cur:
            return cur
    except Exception:
        pass
    try:
        cur = yf.Ticker(ticker).info.get("currency")
        if cur:
            return cur
    except Exception:
        pass
    return "USD"

def fx_pair(src, dst):
    return None if src == dst else f"{src}{dst}=X"

def convert_series_to(series, src_cur, dst_cur, start):
    if src_cur == dst_cur:
        return series
    pair = fx_pair(src_cur, dst_cur)
    fx = yahoo_prices(pair, start) if pair else pd.Series(dtype=float)
    if fx.empty:
        st.warning(f"FX no disponible para {src_cur}->{dst_cur} ({pair}). Se muestran valores sin convertir.")
        return series
    fx = fx.reindex(series.index).ffill().bfill()
    return series * fx

def has_history(ticker, start):
    try:
        return not yahoo_prices(ticker, start).empty
    except Exception:
        return False

def first_available_month(ticker):
    """Devuelve 'YYYY-MM-01' de la primera vela mensual disponible para el ticker (o None)."""
    try:
        df = yf.download(ticker.strip(), period="max", interval="1mo", progress=False, auto_adjust=True)
        if df is None or df.empty:
            return None
        d0 = pd.to_datetime(df.index.min())
        return f"{d0.year:04d}-{d0.month:02d}-01"
    except Exception:
        return None

def recommend_tickers(kind, currency):
    """kind: 'equity' | 'bond' | 'crypto'"""
    if kind == "equity":
        return ["VWRA.L", "VWCE.DE", "IWDA.AS", "VT", "ACWI"]
    if kind == "bond":
        return ["AGGU.L", "AGGH.MI", "BNDW", "IGLO.L", "IGLA.L"]
    if kind == "crypto":
        return ["BTC-USD", "ETH-USD"]
    return []

# precios con posibles fechas duplicadas → obtener float seguro
def px_at(series, d):
    v = series.loc[d]
    if isinstance(v, pd.Series):
        v = v.iloc[-1]
    return float(v)

@dataclass
class Asset:
    ticker: str
    role: str   # 'equity' | 'bond' | 'crypto'
    weight: float
    currency: str

def monthly_index_union(series_list):
    idx = None
    for s in series_list:
        if s is None or s.empty:
            continue
        m = s.resample("M").last().index
        idx = m if idx is None else idx.union(m)
    return pd.DatetimeIndex([]) if idx is None else idx.sort_values()

def simulate_dca_multi(assets, monthly_contribution, start, end, rebalance_months, display_currency):
    native_prices = {a.ticker: yahoo_prices(a.ticker, start, end) for a in assets}
    conv_prices = {}
    for a in assets:
        s = native_prices[a.ticker]
        conv_prices[a.ticker] = convert_series_to(s, a.currency, display_currency, start) if not s.empty else s
    if all(s.empty for s in conv_prices.values()):
        return pd.DataFrame(), conv_prices

    m_idx = monthly_index_union([s for s in conv_prices.values()])
    if len(m_idx) == 0:
        return pd.DataFrame(), conv_prices

    prices_m = {t: s.reindex(m_idx).ffill() for t, s in conv_prices.items()}
    shares = {a.ticker: 0.0 for a in assets}
    cash = 0.0
    target_w = {a.ticker: a.weight for a in assets}
    role_by_ticker = {a.ticker: a.role for a in assets}
    hist, months_since_reb = [], 0

    for d in m_idx:
        # aporte del mes
        cash += monthly_contribution
        # compra proporcional a pesos objetivo
        for a in assets:
            t = a.ticker
            px = px_at(prices_m[t], d)
            if px > 0:
                alloc = monthly_contribution * target_w[t]
                shares[t] += alloc / px

        months_since_reb += 1
        values = {t: shares[t] * px_at(prices_m[t], d) for t in shares}
        port_value = sum(values.values()) + cash

        # rebalanceo
        if rebalance_months and months_since_reb >= rebalance_months and port_value > 0:
            target_values = {t: target_w[t] * port_value for t in shares}
            for t in shares:
                px = px_at(prices_m[t], d)
                if px > 0:
                    diff = target_values[t] - values[t]
                    shares[t] += diff / px
            cash = 0.0
            months_since_reb = 0
            values = {t: shares[t] * px_at(prices_m[t], d) for t in shares}
            port_value = sum(values.values()) + cash

        row = {"date": d, "cash": cash, "total": port_value}
        for t, val in values.items():
            role = role_by_ticker[t]
            if role == "equity":
                row["equity_value"] = val
            elif role == "bond":
                row["bond_value"] = val
            elif role == "crypto":
                row["crypto_value"] = val
        hist.append(row)

    df = pd.DataFrame(hist).set_index("date")
    for c in ["equity_value", "bond_value", "crypto_value"]:
        if c not in df.columns:
            df[c] = 0.0
    return df, prices_m

def perf_stats(series):
    r = series.pct_change().dropna()
    if r.empty:
        return {"CAGR": 0.0, "Vol": 0.0, "MaxDD": 0.0, "Sharpe": 0.0}
    years = (series.index[-1] - series.index[0]).days / 365.25
    cagr = (series.iloc[-1] / series.iloc[0]) ** (1 / years) - 1 if years > 0 else 0.0
    vol = r.std() * np.sqrt(12)
    maxdd = (series / series.cummax() - 1.0).min()
    sharpe = (r.mean() * 12) / vol if vol > 0 else 0.0
    return {"CAGR": cagr, "Vol": vol, "MaxDD": maxdd, "Sharpe": sharpe}

def risk_level(vol, maxdd):
    if vol < 0.08 and maxdd > -0.15: return "Bajo / Low"
    if vol <= 0.15 or maxdd >= -0.30: return "Medio / Medium"
    return "Alto / High"

def hhi_and_neff(weights):
    w = np.array([max(0.0, v) for v in weights.values()], dtype=float)
    if w.sum() <= 0:
        return 0.0, 0.0
    w = w / w.sum()
    hhi = float(np.sum(w ** 2))
    neff = float(1.0 / hhi) if hhi > 0 else 0.0
    return hhi, neff

def trend_is_bearish(ticker: str, start: str, display_currency: str) -> bool | None:
    """
    Devuelve:
      True  -> bajista (precio < MA200)
      False -> no bajista
      None  -> datos insuficientes o NaN
    """
    s = yahoo_prices(ticker, start)
    if s is None or s.empty:
        return None

    # Convertir a moneda objetivo
    src_cur = get_currency_of_ticker(ticker)
    s = convert_series_to(s, src_cur, display_currency, start)

    # Necesitamos al menos 200 datos para MA200
    if s is None or len(s.dropna()) < 200:
        return None

    # MA200 y último precio como floats seguros
    ma200 = s.rolling(200).mean()
    last_px = s.iloc[-1]
    last_ma = ma200.iloc[-1]

    try:
        last_px_f = float(last_px)
        last_ma_f = float(last_ma)
    except Exception:
        return None
    if np.isnan(last_px_f) or np.isnan(last_ma_f):
        return None

    return bool(last_px_f < last_ma_f)
# ────────────────────────── CONTROLES (SIDEBAR) ──────────────────────
# Estado inicial para poder rellenar con botones
for k, v in {
    "eq_ticker": DEFAULTS["equity_ticker"],
    "bd_ticker": DEFAULTS["bond_ticker"],
    "cr_ticker": DEFAULTS["crypto_ticker"],
    "start_date": DEFAULTS["start"],
}.items():
    st.session_state.setdefault(k, v)

with st.sidebar:
    st.header(t(lang, "sidebar_header"))
    edad = st.number_input(t(lang, "age"), 18, 90, 18, step=1)
    horizonte = st.slider(t(lang, "horizon"), 1, 30, 7)
    tolerancia = st.slider(t(lang, "tolerance"), 1, 10, 7, help=t(lang, "tol_help"))
    st.caption(t(lang, "tol_help"))
    st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)

    aportacion = st.number_input(
        f"{t(lang,'monthly')} ({'€' if currency=='EUR' else '$'})",
        1, 10000, 300, step=10, help=t(lang,"monthly_help")
    )

    reb_opts = [2, 4, 6, 8, 10, 12, t(lang, "reb_opt_none")]
    rebalanceo_opt = st.selectbox(t(lang, "rebalance"), reb_opts, index=2)
    rb = 0 if rebalanceo_opt == t(lang, "reb_opt_none") else int(rebalanceo_opt)
    st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)

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
    c1, c2, c3 = st.columns(3)
    with c1: w_equity = st.number_input(t(lang, "equity_weight"), 0, 100, w_equity, step=5)
    with c2: w_bond   = st.number_input(t(lang, "bond_weight"),   0, 100, w_bond,   step=5)
    with c3:
        include_crypto = st.checkbox(t(lang, "crypto_enable"), value=False)
        w_crypto = st.number_input(t(lang, "crypto_weight"), 0, 100, w_crypto, step=5, disabled=not include_crypto)

    total_w = max(1, w_equity + w_bond + (w_crypto if include_crypto else 0))
    w_equity_norm = round(100 * w_equity / total_w, 2)
    w_bond_norm   = round(100 * w_bond   / total_w, 2)
    w_crypto_norm = round(100 * (w_crypto if include_crypto else 0) / total_w, 2)

    st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)
    st.subheader(t(lang, "assets_header"))
    eq_ticker = st.text_input(t(lang, "equity_label"), st.session_state["eq_ticker"], key="eq_ticker")
    bd_ticker = st.text_input(t(lang, "bond_label"),   st.session_state["bd_ticker"], key="bd_ticker")
    cr_ticker = st.text_input(t(lang, "crypto_label"), st.session_state["cr_ticker"], key="cr_ticker") if include_crypto else None
    start     = st.text_input(t(lang, "start_label"),  st.session_state["start_date"], key="start_date")

    with st.expander(t(lang, "suggest_shortcut"), expanded=False):
        colA, colB = st.columns(2)
        with colA:
            eq_sug = st.selectbox(t(lang, "suggest_eq"),
                                  recommend_tickers("equity", currency), index=0)
            if st.button(t(lang, "fill") + " (Equity)"):
                st.session_state["eq_ticker"] = eq_sug
                st.rerun()
        with colB:
            bd_sug = st.selectbox(t(lang, "suggest_bd"),
                                  recommend_tickers("bond", currency), index=0)
            if st.button(t(lang, "fill") + " (Bond)"):
                st.session_state["bd_ticker"] = bd_sug
                st.rerun()

run = st.button(t(lang, "simulate"))

# ───────────────────────────── SIMULACIÓN ───────────────────────────
if run:
    today = date.today().isoformat()

    # Verificación de histórico
    check_tickers = [eq_ticker, bd_ticker] + ([cr_ticker] if (cr_ticker and include_crypto) else [])
    missing = [t for t in check_tickers if not has_history(t, start)]
    if missing:
        st.error(t(lang, "cant_simulate"))
        for tck in missing:
            st.warning(t(lang, "no_hist", ticker=tck, start=start, today=today))

            # ¿Qué activo es para sugerir?
            if tck == st.session_state.get("eq_ticker"):
                kind = "equity"
            elif tck == st.session_state.get("bd_ticker"):
                kind = "bond"
            else:
                kind = "crypto"

            cols = st.columns([1, 2])
            # Sugerir primera fecha disponible
            first_ok = first_available_month(tck)
            with cols[0]:
                if first_ok and st.button(f"{t(lang,'use_date')}: {first_ok}", key=f"use_date_{tck}"):
                    st.session_state["start_date"] = first_ok
                    st.rerun()

            # Sugerir tickers alternativos
            alts = recommend_tickers(kind, currency)
            with cols[1]:
                if alts:
                    st.caption("• " + t(lang, "try_alt"))
                    alt_cols = st.columns(min(3, len(alts)))
                    for i, alt in enumerate(alts[:6]):
                        with alt_cols[i % len(alt_cols)]:
                            if st.button(f"Usar {alt}", key=f"use_{kind}_{alt}"):
                                if kind == "equity":
                                    st.session_state["eq_ticker"] = alt
                                elif kind == "bond":
                                    st.session_state["bd_ticker"] = alt
                                else:
                                    st.session_state["cr_ticker"] = alt
                                st.rerun()
        st.stop()

    # Construye la lista de activos
    eq_cur = get_currency_of_ticker(eq_ticker)
    bd_cur = get_currency_of_ticker(bd_ticker)
    assets = [
        Asset(eq_ticker, role="equity", weight=(w_equity_norm/100.0), currency=eq_cur),
        Asset(bd_ticker, role="bond",   weight=(w_bond_norm/100.0),   currency=bd_cur),
    ]
    if include_crypto and cr_ticker:
        cr_cur = get_currency_of_ticker(cr_ticker)
        assets.append(Asset(cr_ticker, role="crypto", weight=(w_crypto_norm/100.0), currency=cr_cur))

    # Ejecutar simulación
    with st.spinner("Descargando datos y simulando..." if lang=="ES" else "Downloading data and simulating..."):
        df, prices_m = simulate_dca_multi(
            assets=assets,
            monthly_contribution=float(aportacion),
            start=start, end=None,
            rebalance_months=rb,
            display_currency=("EUR" if currency=="EUR" else "USD"),
        )
        if df is None or df.empty:
            st.warning(t(lang, "no_data_range", start=start, today=today))
            st.stop()

    st.success(t(lang, "sim_done"))

    # ───────── KPIs ─────────
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(t(lang, "summary"))
        valor_final = float(df["total"].iloc[-1])
        aportado = float(df.shape[0] * float(aportacion))
        st.metric(t(lang, "final_value"), f"{CURRENCY_SYMBOL}{valor_final:,.2f}")
        st.metric(t(lang, "contributed"), f"{CURRENCY_SYMBOL}{aportado:,.2f}")
    with c2:
        st.subheader(t(lang, "metrics"))
        stats = perf_stats(df["total"])
        st.write(f"{t(lang,'cagr')}: {stats['CAGR']*100:.2f}%")
        st.write(f"{t(lang,'vol')}: {stats['Vol']*100:.2f}%")
        st.write(f"{t(lang,'maxdd')}: {stats['MaxDD']*100:.2f}%")
        st.write(f"{t(lang,'sharpe')}: {stats['Sharpe']:.2f}")
        # nivel de riesgo
        lvl = risk_level(stats["Vol"], stats["MaxDD"])
        st.write(t(lang, "risk_level", level=lvl))

    # ───────── Concentración ─────────
    st.subheader(t(lang, "concentration"))
    weights_pct = {a.ticker: a.weight*100 for a in assets}
    hhi, neff = hhi_and_neff({a.ticker: a.weight for a in assets})
    st.write(t(lang, "hhi", hhi=hhi, neff=neff))

    # ───────── Señales MA200 ─────────
    st.subheader(t(lang, "signals"))
    for a in assets:
        sig = trend_is_bearish(a.ticker, start, currency)
        if sig is True:
            st.warning(t(lang, "bearish", ticker=a.ticker))
        elif sig is False:
            st.info(t(lang, "not_bearish", ticker=a.ticker))
        else:
            st.caption(f"{a.ticker}: {'No hay datos suficientes' if lang=='ES' else 'Insufficient data'} (MA200)")

    # ───────── Gráficos ─────────
    st.subheader(t(lang, "evolution"))
    df_plot = df.copy()
    df_plot["date"] = df_plot.index

    value_cols = [c for c in ["equity_value", "bond_value", "crypto_value"] if c in df_plot.columns]
    seq_light = ["#16A34A", "#0EA5E9", "#F59E0B"]
    seq_dark  = ["#34D399", "#60A5FA", "#FBBF24"]
    seq = seq_dark if dark else seq_light
    template = "plotly_dark" if dark else "plotly"

    fig_comp = px.line(
        df_plot, x="date", y=value_cols, template=template,
        color_discrete_sequence=seq,
        labels={"value": CURRENCY_SYMBOL, "date": t(lang,"date"), "variable": t(lang,"component")},
        title=t(lang, "components_title"),
    )
    fig_comp.update_traces(mode="lines+markers",
                           hovertemplate="%{x|%Y-%m-%d}<br>%{fullData.name}: "+CURRENCY_SYMBOL+"%{y:,.2f}")
    st.plotly_chart(fig_comp, use_container_width=True)

    fig_tot = px.line(
        df_plot, x="date", y="total", template=template,
        color_discrete_sequence=[seq[0]],
        labels={"total": CURRENCY_SYMBOL, "date": t(lang,"date")},
        title=t(lang, "total_title"),
    )
    fig_tot.update_traces(mode="lines+markers",
                          hovertemplate="%{x|%Y-%m-%d}<br>"+t(lang,"hover_total")+": "+CURRENCY_SYMBOL+"%{y:,.2f}")
    st.plotly_chart(fig_tot, use_container_width=True)

    st.subheader(t(lang, "last12"))
    tail_cols = [c for c in ["equity_value", "bond_value", "crypto_value", "cash", "total"] if c in df.columns]
    st.dataframe(
        df[tail_cols].tail(12).style.format({col: (lambda v: f"{CURRENCY_SYMBOL}{v:,.2f}") for col in tail_cols})
    )

    # ───────── PDF ─────────
    def generar_pdf(buffer, brand, lang, perfil, aportacion, rebalanceo_opt, currency,
                    weights_pct, tickers, stats, valor_final, aportado, hhi, neff):
        c = canvas.Canvas(buffer, pagesize=A4)
        W, H = A4; x, y = 2*cm, H - 2*cm
        c.setFont("Helvetica-Bold", 16)
        c.drawString(x, y, f"{brand} — {'Informe de Simulación' if lang=='ES' else 'Simulation Report'}")
        y -= 1.2*cm; c.setFont("Helvetica", 11)
        c.drawString(x, y, (f"Fecha: {datetime.now():%Y-%m-%d %H:%M}" if lang=='ES' else f"Date: {datetime.now():%Y-%m-%d %H:%M}"))
        y -= 0.8*cm
        line1 = (f"Perfil: {perfil}  |  Aportación: {('€' if currency=='EUR' else '$')}{aportacion:,.2f}  |  Rebalanceo: {rebalanceo_opt}"
                 if lang=='ES' else
                 f"Profile: {perfil}  |  Monthly: {('€' if currency=='EUR' else '$')}{aportacion:,.2f}  |  Rebalancing: {rebalanceo_opt}")
        c.drawString(x, y, line1); y -= 0.8*cm
        c.drawString(x, y, f"Moneda: {currency}  |  Pesos: {weights_pct}"); y -= 0.6*cm
        c.drawString(x, y, f"Tickers: {tickers}"); y -= 1.0*cm
        c.setFont("Helvetica-Bold", 12); c.drawString(x, y, ("Resultados" if lang=='ES' else "Results")); y -= 0.8*cm
        c.setFont("Helvetica", 11)
        c.drawString(x, y, (f"Valor final: {('€' if currency=='EUR' else '$')}{valor_final:,.2f}" if lang=='ES' else f"Final value: {('€' if currency=='EUR' else '$')}{valor_final:,.2f}")); y -= 0.6*cm
        c.drawString(x, y, (f"Aportado: {('€' if currency=='EUR' else '$')}{aportado:,.2f}" if lang=='ES' else f"Contributed: {('€' if currency=='EUR' else '$')}{aportado:,.2f}")); y -= 0.6*cm
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
    st.download_button(
        label=t(lang, "pdf_btn"),
        data=pdf_buffer.getvalue(),
        file_name=f"{BRAND_NAME}_report_{datetime.now():%Y%m%d_%H%M}.pdf",
        mime="application/pdf"
    )

# ────────────────────────── GLOSARIO / FEEDBACK ─────────────────────
st.divider()
st.subheader(t(lang, "glossary"))
with st.expander(t(lang, "glossary"), expanded=False):
    st.markdown(t(lang, "glossary_text"))
    st.markdown("---")
    st.markdown(f"### {t(lang, 'table_howto_title')}")
    st.markdown(t(lang, "table_howto_text"))

st.divider()
st.subheader(t(lang, "feedback"))
st.markdown(t(lang, "feedback_text", url=FEEDBACK_URL))
st.caption(t(lang, "disclaimer"))
