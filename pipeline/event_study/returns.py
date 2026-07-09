"""
returns.py — pluggable returns + Fama-French factor loaders.

Three return sources, same output contract (wide DataFrame: index=DatetimeIndex, columns=tickers,
values=simple daily returns):
  * stooq   — free, no key (default). Good for a quick outside-researcher pass.
  * yfinance— free, no key. Alternative if stooq coverage is thin.
  * crsp    — WRDS/CRSP via SQL (gold standard for a citable PAE; needs a WRDS account).

Factors come from the Ken French Data Library (free) via pandas-datareader: returns mktrf, smb, hml,
rmw, cma, rf, and mkt = mktrf + rf, as DECIMALS (the library is in percent; we divide by 100).

All heavy imports are lazy so this module imports even if a given provider isn't installed.
"""
from __future__ import annotations
import pandas as pd

# ----------------------------------------------------------------------------- factors
def load_ff_factors(start, end, model="ff5") -> pd.DataFrame:
    """Daily Fama-French factors as decimals. Columns: mktrf, smb, hml, [rmw, cma], rf, mkt."""
    from pandas_datareader import data as pdr
    ds = ("F-F_Research_Data_5_Factors_2x3_daily" if model == "ff5"
          else "F-F_Research_Data_Factors_daily")
    raw = pdr.DataReader(ds, "famafrench", start, end)[0] / 100.0
    raw = raw.rename(columns={"Mkt-RF": "mktrf", "SMB": "smb", "HML": "hml",
                              "RMW": "rmw", "CMA": "cma", "RF": "rf"})
    raw.index = pd.to_datetime(raw.index)
    raw["mkt"] = raw["mktrf"] + raw["rf"]                      # total market return
    return raw


# ----------------------------------------------------------------------------- prices -> returns
def _prices_to_returns(prices: pd.DataFrame) -> pd.DataFrame:
    prices = prices.sort_index()
    return prices.pct_change().dropna(how="all")


def load_returns_stooq(tickers, start, end) -> pd.DataFrame:
    """Free daily returns via Stooq. US symbols are queried with a `.US` suffix then renamed back."""
    from pandas_datareader import data as pdr
    sym = {f"{t}.US": t for t in tickers}
    px = pdr.DataReader(list(sym), "stooq", start, end)
    close = px["Close"] if isinstance(px.columns, pd.MultiIndex) else px
    close = close.rename(columns=sym)
    return _prices_to_returns(close)


def load_returns_yf(tickers, start, end) -> pd.DataFrame:
    """Free daily returns via yfinance (auto-adjusted close)."""
    import yfinance as yf
    data = yf.download(list(tickers), start=start, end=end, auto_adjust=True, progress=False)
    close = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data[["Close"]]
    if isinstance(close, pd.Series):
        close = close.to_frame(tickers[0])
    return _prices_to_returns(close)


# WRDS / CRSP SQL — the gold standard for a citable academic event study.
CRSP_RETURNS_SQL = """
-- Daily delisting-adjusted returns for a set of tickers over a date range.
-- Requires a WRDS account. Map ticker -> permno via crsp.stocknames (point-in-time tickers).
WITH ids AS (
    SELECT DISTINCT permno, ticker
    FROM crsp.stocknames
    WHERE ticker IN %(tickers)s
)
SELECT d.permno, i.ticker, d.date, d.ret
FROM crsp.dsf d
JOIN ids i USING (permno)
WHERE d.date BETWEEN %(start)s AND %(end)s
ORDER BY i.ticker, d.date;
-- Market (value-weighted incl. dividends) for the market model / market-adjusted benchmark:
--   SELECT date, vwretd FROM crsp.dsi WHERE date BETWEEN %(start)s AND %(end)s;
"""

def load_returns_crsp(tickers, start, end, wrds_username=None) -> pd.DataFrame:
    """Daily CRSP returns via WRDS. Needs `pip install wrds` and a WRDS account."""
    import wrds
    db = wrds.Connection(wrds_username=wrds_username)
    try:
        df = db.raw_sql(CRSP_RETURNS_SQL, params={
            "tickers": tuple(tickers), "start": str(start), "end": str(end)})
    finally:
        db.close()
    df["date"] = pd.to_datetime(df["date"])
    return df.pivot_table(index="date", columns="ticker", values="ret")


def load_returns(tickers, start, end, source="stooq", **kw) -> pd.DataFrame:
    """Dispatch to a return source. source in {'stooq','yfinance','crsp'}."""
    tickers = list(dict.fromkeys(tickers))
    if source == "stooq":
        return load_returns_stooq(tickers, start, end)
    if source == "yfinance":
        return load_returns_yf(tickers, start, end)
    if source == "crsp":
        return load_returns_crsp(tickers, start, end, wrds_username=kw.get("wrds_username"))
    raise ValueError(f"unknown source {source!r}")
