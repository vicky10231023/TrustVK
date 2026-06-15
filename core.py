"""
core.py —— 数据层 + 主题
yfinance 价格 / FRED 宏观,均带缓存与容错;任何一个源取不到都不让 App 崩。
Phase 2/3 直接复用这里的 fetch_* 函数。
"""
import os, datetime as dt
import requests
import pandas as pd
import streamlit as st
import config as C

FRED_BASE = "https://api.stlouisfed.org/fred"


# ── 密钥 ─────────────────────────────────────────────────────────────────────
def fred_key():
    try:
        if "FRED_API_KEY" in st.secrets:
            return st.secrets["FRED_API_KEY"]
    except Exception:
        pass
    return os.environ.get("FRED_API_KEY")


def app_password():
    try:
        if "APP_PASSWORD" in st.secrets:
            return st.secrets["APP_PASSWORD"]
    except Exception:
        pass
    return os.environ.get("APP_PASSWORD", C.DEFAULT_PASSWORD)


# ── yfinance ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60 * 30, show_spinner=False)
def yf_one(ticker: str, period: str = "1y") -> pd.Series:
    """单只代码的收盘价序列;失败返回空序列(不抛)。"""
    try:
        import yfinance as yf
        h = yf.Ticker(ticker).history(period=period, interval="1d", auto_adjust=True)
        if h is None or h.empty or "Close" not in h:
            return pd.Series(dtype=float)
        s = h["Close"].copy()
        s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
        return s[~s.index.duplicated(keep="last")]
    except Exception:
        return pd.Series(dtype=float)


def yf_many(codes, period="1y"):
    """{资产code: 价格序列};附带哪些取失败。"""
    out, failed = {}, []
    for code in codes:
        t = C.ASSETS[code]["ticker"]
        s = yf_one(t, period)
        if s.empty:
            failed.append(code)
        out[code] = s
    return out, failed


# ── FRED ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def fred_series(series_id: str, start: str = "2015-01-01") -> pd.Series:
    key = fred_key()
    if not key:
        return pd.Series(dtype=float)
    try:
        r = requests.get(f"{FRED_BASE}/series/observations", timeout=20, params={
            "series_id": series_id, "api_key": key, "file_type": "json",
            "observation_start": start, "sort_order": "asc"})
        r.raise_for_status()
        rows = r.json().get("observations", [])
        idx, val = [], []
        for o in rows:
            try:
                val.append(float(o["value"])); idx.append(pd.Timestamp(o["date"]))
            except (ValueError, KeyError):
                continue
        return pd.Series(val, index=pd.DatetimeIndex(idx))
    except Exception:
        return pd.Series(dtype=float)


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def fred_release_dates(release_id: int):
    key = fred_key()
    if not key:
        return []
    try:
        r = requests.get(f"{FRED_BASE}/release/dates", timeout=20, params={
            "release_id": release_id, "api_key": key, "file_type": "json",
            "sort_order": "asc", "include_release_dates_with_no_data": "false",
            "limit": 1000})
        r.raise_for_status()
        return [pd.Timestamp(d["date"]).normalize() for d in r.json().get("release_dates", [])]
    except Exception:
        return []


# ── 工具 ─────────────────────────────────────────────────────────────────────
def last_and_change(s: pd.Series):
    """最新值 + 日变动(绝对、百分比)。"""
    s = s.dropna()
    if len(s) < 2:
        return (s.iloc[-1] if len(s) else None), None, None
    last, prev = s.iloc[-1], s.iloc[-2]
    return last, last - prev, (last / prev - 1) * 100 if prev else None


def yoy(series_monthly: pd.Series):
    s = series_monthly.dropna()
    if len(s) < 13:
        return None
    return (s.iloc[-1] / s.iloc[-13] - 1) * 100


def recent(s: pd.Series, days=None, years=None):
    """取序列尾部一段时间(兼容 pandas 2.x/3.x,替代已被删除的 .last())。"""
    s = s.dropna()
    if s.empty:
        return s
    off = pd.DateOffset(days=days) if days else pd.DateOffset(years=years or 1)
    return s[s.index >= s.index.max() - off]


def pct_window(s: pd.Series, days=30):
    """近 N 个交易日的百分位(用于 VIX 等)。"""
    s = s.dropna()
    if len(s) < days:
        s2 = s
    else:
        s2 = s.iloc[-252:] if len(s) > 252 else s
    if s2.empty:
        return None
    return float((s2 <= s2.iloc[-1]).mean() * 100)


# ── 主题 / 卡片 ──────────────────────────────────────────────────────────────
def inject_css():
    t = C.THEME
    st.markdown(f"""<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@500;700&display=swap');
    .stApp {{ background:
       radial-gradient(1100px 600px at 80% -10%, #141b2e 0%, {t['ink']} 55%); }}
    .block-container {{ padding-top: 2.2rem; max-width: 1180px; }}
    h1,h2,h3,h4 {{ color:{t['txt']}; font-family:'Space Grotesk',-apple-system,system-ui,sans-serif; letter-spacing:-.01em; }}
    .mc-row {{ display:flex; flex-wrap:wrap; gap:12px; margin:6px 0 14px; }}
    .mc {{ flex:1 1 150px; min-width:150px; background:{t['panel']}; border:1px solid {t['line']};
           border-radius:14px; padding:13px 15px; }}
    .mc .nm {{ font-size:12px; color:{t['muted']}; }}
    .mc .vl {{ font-size:22px; font-weight:700; color:{t['txt']};
              font-family:'JetBrains Mono',ui-monospace,monospace; margin-top:3px; }}
    .mc .ch {{ font-size:12.5px; font-weight:600; margin-top:2px;
              font-family:'JetBrains Mono',ui-monospace,monospace; }}
    .eyebrow {{ font-family:'JetBrains Mono',monospace; font-size:11px; letter-spacing:.26em;
               color:{t['muted']}; }}
    .pill {{ display:inline-block; padding:4px 12px; border-radius:999px; font-size:12.5px;
            font-weight:700; }}
    .note {{ background:{t['panel2']}; border:1px solid {t['line']}; border-radius:12px;
            padding:12px 16px; color:{t['muted']}; font-size:13px; }}
    </style>
    """, unsafe_allow_html=True)


def cards_row(items):
    """items: [(名称, 数值字符串, 变动字符串 or None, 颜色)]"""
    t = C.THEME
    html = '<div class="mc-row">'
    for nm, val, ch, color in items:
        ch_html = f'<div class="ch" style="color:{color}">{ch}</div>' if ch else ''
        html += f'<div class="mc"><div class="nm">{nm}</div><div class="vl">{val}</div>{ch_html}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def fmt(code, val):
    if val is None:
        return "—"
    try:
        return C.ASSETS[code]["fmt"].format(val)
    except Exception:
        return f"{val:,.2f}"


def chg_str(absc, pct, is_yield=False):
    if pct is None and absc is None:
        return None, C.THEME["muted"]
    color = C.THEME["up"] if (absc or 0) >= 0 else C.THEME["down"]
    arrow = "▲" if (absc or 0) >= 0 else "▼"
    if is_yield:
        return f"{arrow} {abs(absc)*100:.1f} bps", color
    return f"{arrow} {abs(pct):.2f}%", color
