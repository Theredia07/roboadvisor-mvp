import numpy as np
import pandas as pd
import yfinance as yf
from dataclasses import dataclass

# --- Configuración por defecto de ETFs (Europa) ---
DEFAULT_EQUITY = {"name": "Vanguard FTSE All-World UCITS ETF (Acc)",
                  "ticker": "VWCE.DE",  # Sufijo .DE suele funcionar en Yahoo; cambiar si no
                  "weight": 0.8}
DEFAULT_BOND = {"name": "iShares Core Global Aggregate Bond UCITS ETF EUR Hedged (Acc)",
                "ticker": "AGGH.DE",
                "weight": 0.2}

PROFILE_WEIGHTS = {
    "Conservador": (0.30, 0.70),
    "Moderado": (0.50, 0.50),
    "Agresivo": (0.80, 0.20)
}

@dataclass
class PortfolioConfig:
    equity_ticker: str = DEFAULT_EQUITY["ticker"]
    bond_ticker: str = DEFAULT_BOND["ticker"]
    equity_weight: float = DEFAULT_EQUITY["weight"]
    bond_weight: float = DEFAULT_BOND["weight"]
    monthly_contribution: float = 300.0
    rebalance_months: int = 6  # rebalanceo semestral
    start: str = "2015-01-01"
    end: str = None  # hasta hoy

def download_prices(tickers, start, end=None):
    data = yf.download(tickers, start=start, end=end, progress=False, auto_adjust=True)
    if isinstance(data, pd.DataFrame) and "Close" in data.columns:
        px = data["Close"]
    else:
        px = data
    # Para tickers únicos, yfinance devuelve Serie
    if isinstance(px, pd.Series):
        px = px.to_frame(tickers if isinstance(tickers, str) else tickers[0])
    return px.dropna(how="all")

def monthly_dates(index):
    return pd.to_datetime(index).to_period("M").to_timestamp("M").unique()

def simulate_dca(cfg: PortfolioConfig):
    tickers = [cfg.equity_ticker, cfg.bond_ticker]
    prices = download_prices(tickers, cfg.start, cfg.end)
    prices = prices.ffill().dropna()
    m_idx = monthly_dates(prices.index)
    prices_m = prices.reindex(m_idx).ffill()

    # Asignaciones objetivo
    target_w = np.array([cfg.equity_weight, cfg.bond_weight])

    shares = np.array([0.0, 0.0], dtype=float)
    cash = 0.0

    history = []
    months_since_reb = 0

    for d in prices_m.index:
        # Aportación del mes
        cash += cfg.monthly_contribution

        # Comprar proporcional a pesos objetivo (DCA)
        alloc = cfg.monthly_contribution * target_w
        price_vec = prices_m.loc[d, tickers].values.astype(float)
        buy_shares = np.where(price_vec > 0, alloc / price_vec, 0)
        shares += buy_shares

        # Rebalanceo periódico (opcional)
        months_since_reb += 1
        port_value = (shares * price_vec).sum() + cash
        if cfg.rebalance_months and months_since_reb >= cfg.rebalance_months and port_value > 0:
            target_values = target_w * port_value
            current_values = shares * price_vec
            diff_values = target_values - current_values
            # Vender/comprar para acercar a objetivo (ignora comisiones)
            shares += diff_values / price_vec
            cash = 0.0
            months_since_reb = 0

        # Registrar valor
        port_value = (shares * price_vec).sum() + cash
        history.append({
            "date": d,
            "equity_value": shares[0] * price_vec[0],
            "bond_value": shares[1] * price_vec[1],
            "cash": cash,
            "total": port_value
        })

    df = pd.DataFrame(history).set_index("date")
    return df, prices_m

def performance_stats(series: pd.Series):
    # series: valores de la cartera en el tiempo (mensual)
    returns = series.pct_change().dropna()
    if returns.empty:
        return {"CAGR": 0, "Vol": 0, "MaxDD": 0, "Sharpe": 0}
    # CAGR
    n_years = (series.index[-1] - series.index[0]).days / 365.25
    cagr = (series.iloc[-1] / series.iloc[0]) ** (1 / n_years) - 1 if n_years > 0 else 0
    vol = returns.std() * np.sqrt(12)
    cummax = series.cummax()
    dd = series / cummax - 1.0
    maxdd = dd.min()
    sharpe = (returns.mean() * 12) / vol if vol != 0 else 0
    return {"CAGR": cagr, "Vol": vol, "MaxDD": maxdd, "Sharpe": sharpe}

def profile_to_weights(profile: str):
    w = PROFILE_WEIGHTS.get(profile, PROFILE_WEIGHTS["Moderado"])
    return w