"""
收益率曲线模块 / Yield Curve Module
宏观作战室 — 10年期与2年期利差监测

数据源 / Data source: FRED
  T10Y2Y  = 10年 − 2年   10-year minus 2-year
  T10Y3M  = 10年 − 3个月  10-year minus 3-month
  DGS2    = 2年期收益率
  DGS10   = 10年期收益率
  USREC   = NBER 衰退指示(1=衰退)  recession indicator

用法 / Usage:
  在主程序里 from yield_curve import render_yield_curve
  然后 render_yield_curve(FRED_API_KEY)
"""

import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"

SERIES = {
    "T10Y2Y": "10Y − 2Y",
    "T10Y3M": "10Y − 3M",
    "DGS2": "2年期 / 2-year",
    "DGS10": "10年期 / 10-year",
}


# ----------------------------------------------------------------------
# 数据获取 / Data fetching
# ----------------------------------------------------------------------
@st.cache_data(ttl=60 * 60 * 6)  # 缓存6小时 / cache 6 hours
def fetch_fred(series_id: str, api_key: str, start: str = "1976-01-01") -> pd.Series:
    """取一条 FRED 序列,返回带日期索引的 Series。"""
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start,
    }
    r = requests.get(FRED_URL, params=params, timeout=30)
    r.raise_for_status()
    obs = r.json().get("observations", [])

    df = pd.DataFrame(obs)
    if df.empty:
        return pd.Series(dtype=float, name=series_id)

    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")  # "." -> NaN
    s = df.set_index("date")["value"].dropna()
    s.name = series_id
    return s


@st.cache_data(ttl=60 * 60 * 24)
def fetch_recessions(api_key: str, start: str = "1976-01-01"):
    """把 USREC 转成 [(开始, 结束), ...] 的衰退区间列表。"""
    usrec = fetch_fred("USREC", api_key, start)
    if usrec.empty:
        return []

    periods, in_rec, rec_start = [], False, None
    for date, val in usrec.items():
        if val == 1 and not in_rec:
            in_rec, rec_start = True, date
        elif val == 0 and in_rec:
            in_rec = False
            periods.append((rec_start, date))
    if in_rec:
        periods.append((rec_start, usrec.index[-1]))
    return periods


# ----------------------------------------------------------------------
# 画图 / Chart
# ----------------------------------------------------------------------
def build_chart(data: dict, recessions, title: str, height: int = 420):
    """data: {label: Series}。利差以基点显示。"""
    fig = go.Figure()

    # 衰退阴影 / recession shading
    for start, end in recessions:
        fig.add_vrect(
            x0=start, x1=end,
            fillcolor="grey", opacity=0.18, line_width=0, layer="below",
        )

    colors = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e"]
    for i, (label, s) in enumerate(data.items()):
        if s.empty:
            continue
        fig.add_trace(go.Scatter(
            x=s.index, y=s.values * 100,   # 百分点 -> 基点 / pct -> bp
            name=label, mode="lines",
            line=dict(width=1.4, color=colors[i % len(colors)]),
            hovertemplate="%{x|%Y-%m-%d}<br>%{y:.1f} bp<extra>" + label + "</extra>",
        ))

    # 零轴 —— 跌破即倒挂 / zero line: below = inverted
    fig.add_hline(
        y=0, line_width=1.2, line_dash="dash", line_color="black",
        annotation_text="0 = 倒挂线 / inversion", annotation_position="top left",
    )

    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        yaxis_title="基点 / basis points",
        xaxis_title="",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
        plot_bgcolor="white",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#eee", zeroline=False)
    return fig


# ----------------------------------------------------------------------
# 主渲染 / Main render
# ----------------------------------------------------------------------
def render_yield_curve(api_key: str = None):
    api_key = api_key or os.getenv("FRED_API_KEY")
    if not api_key:
        st.error("缺少 FRED_API_KEY / FRED_API_KEY not set")
        return

    st.header("收益率曲线 / Yield Curve")
    st.caption(
        "10年期 − 2年期。跌破零 = 倒挂,历史上每次美国衰退之前都出现过。"
        "  ·  10Y minus 2Y. Below zero = inverted; every US recession since 1976 was preceded by one."
    )

    try:
        t10y2y = fetch_fred("T10Y2Y", api_key)
        t10y3m = fetch_fred("T10Y3M", api_key)
        dgs2 = fetch_fred("DGS2", api_key)
        dgs10 = fetch_fred("DGS10", api_key)
        recessions = fetch_recessions(api_key)
    except Exception as e:
        st.error(f"数据获取失败 / fetch failed: {e}")
        return

    # ---------------- 当前读数 / current readings ----------------
    def latest(s):
        return (s.index[-1], s.iloc[-1]) if not s.empty else (None, float("nan"))

    d_spread, v_spread = latest(t10y2y)
    _, v_2y = latest(dgs2)
    _, v_10y = latest(dgs10)
    _, v_3m_spread = latest(t10y3m)

    # 一个月前对比 / one month ago
    prev = t10y2y[t10y2y.index <= (d_spread - pd.Timedelta(days=30))] if d_spread else pd.Series(dtype=float)
    delta_txt = f"{(v_spread - prev.iloc[-1]) * 100:+.0f} bp vs 1M" if len(prev) else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("10Y − 2Y", f"{v_spread * 100:.0f} bp", delta_txt)
    c2.metric("10Y − 3M", f"{v_3m_spread * 100:.0f} bp")
    c3.metric("2年期 / 2Y", f"{v_2y:.3f}%")
    c4.metric("10年期 / 10Y", f"{v_10y:.3f}%")

    if v_spread < 0:
        st.error("⚠️ 曲线已倒挂 / Curve is INVERTED")
    elif v_spread * 100 < 30:
        st.warning(f"曲线偏平 / Curve is flat — {v_spread * 100:.0f} bp")
    else:
        st.info(f"曲线正常 / Curve normal — {v_spread * 100:.0f} bp")

    st.caption(f"最新数据 / latest: {d_spread:%Y-%m-%d}" if d_spread else "")

    # ---------------- 主图 / main chart ----------------
    st.plotly_chart(
        build_chart(
            {"10Y − 2Y": t10y2y, "10Y − 3M": t10y3m},
            recessions,
            "1976 至今 · 灰色为衰退期 / Since 1976 · grey = recessions",
            height=460,
        ),
        use_container_width=True,
    )

    # ---------------- 放大图 / zoom ----------------
    cutoff = pd.Timestamp.today() - pd.DateOffset(years=5)
    st.plotly_chart(
        build_chart(
            {"10Y − 2Y": t10y2y[t10y2y.index >= cutoff],
             "10Y − 3M": t10y3m[t10y3m.index >= cutoff]},
            [(s, e) for s, e in recessions if e >= cutoff],
            "最近5年 · 当前周期 / Last 5 years · current cycle",
            height=360,
        ),
        use_container_width=True,
    )

    # ---------------- 水平收益率 / levels ----------------
    with st.expander("收益率水平 / Yield levels"):
        st.plotly_chart(
            build_chart(
                {"2年期 / 2Y": dgs2[dgs2.index >= cutoff],
                 "10年期 / 10Y": dgs10[dgs10.index >= cutoff]},
                [(s, e) for s, e in recessions if e >= cutoff],
                "2年期 vs 10年期 · 最近5年",
                height=340,
            ).update_layout(yaxis_title="收益率 % (图中单位为 bp×100)"),
            use_container_width=True,
        )
        st.caption("注:此图 y 轴单位为基点,除以100即为百分比。")

    # ---------------- 下载 / download ----------------
    out = pd.DataFrame({"T10Y2Y": t10y2y, "T10Y3M": t10y3m,
                        "DGS2": dgs2, "DGS10": dgs10}).dropna(how="all")
    st.download_button(
        "下载 CSV / Download CSV",
        out.to_csv().encode("utf-8"),
        file_name=f"yield_curve_{datetime.today():%Y%m%d}.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    st.set_page_config(page_title="收益率曲线 / Yield Curve", layout="wide")
    render_yield_curve()
