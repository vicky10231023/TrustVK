"""
app.py —— 全球宏观作战室(Phase 1)
运行: streamlit run app.py
部署: GitHub → share.streamlit.io,Secrets 里设 FRED_API_KEY 和 APP_PASSWORD
"""
import datetime as dt
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

import config as C
import core
import events as E

st.set_page_config(page_title="宏观作战室", page_icon="🧭", layout="wide")
core.inject_css()
T = C.THEME


# ════════════════════════════════════════════════════════════════════════════
# 密码门
# ════════════════════════════════════════════════════════════════════════════
def gate():
    if st.session_state.get("authed"):
        return True
    st.markdown("### 🔒 宏观作战室")
    st.caption("私人工具,请输入访问密码")
    pw = st.text_input("密码", type="password", label_visibility="collapsed")
    if st.button("进入"):
        if pw == core.app_password():
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("密码不对")
    return False


# ════════════════════════════════════════════════════════════════════════════
# 通用助手
# ════════════════════════════════════════════════════════════════════════════
def style_fig(fig, h=300):
    fig.update_layout(
        height=h, margin=dict(l=8, r=8, t=10, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=T["muted"], size=11, family="JetBrains Mono"),
        showlegend=True, legend=dict(orientation="h", y=1.12, x=0),
        xaxis=dict(gridcolor=T["line"], zeroline=False),
        yaxis=dict(gridcolor=T["line"], zeroline=False))
    return fig


def asset_series(code, period="1y"):
    """优先 FRED(如美债),否则 yfinance。"""
    meta = C.ASSETS[code]
    if meta.get("fred") and core.fred_key():
        s = core.fred_series(meta["fred"])
        if not s.empty:
            return s
    return core.yf_one(meta["ticker"], period)


def resolve_event_dates(key):
    ev = C.EVENTS[key]
    src = ev["source"]
    if src == "manual":
        return E.parse_dates(ev["dates"])
    if src == "fred_release":
        return core.fred_release_dates(ev["release_id"])
    if src == "fred_change":
        return E.rate_change_dates(core.fred_series(ev["series"]))
    return []


# ════════════════════════════════════════════════════════════════════════════
# 页面:市场总览
# ════════════════════════════════════════════════════════════════════════════
def page_overview():
    st.markdown('<div class="eyebrow">CROSS-ASSET</div>', unsafe_allow_html=True)
    st.markdown("## 市场总览")

    codes = list(C.ASSETS.keys())
    items = []
    series_cache = {}
    for code in codes:
        s = asset_series(code, "1y")
        series_cache[code] = s
        last, absc, pct = core.last_and_change(s)
        ch, color = core.chg_str(absc, pct, C.ASSETS[code].get("is_yield"))
        items.append((C.ASSETS[code]["name"], core.fmt(code, last), ch, color))
    core.cards_row(items)

    miss = [c for c in codes if series_cache[c].empty]
    if miss:
        st.markdown(f'<div class="note">取数失败:{", ".join(C.ASSETS[c]["name"] for c in miss)}'
                    f'（可能是行情源临时不可用或需 FRED key;刷新或稍后再试）。</div>',
                    unsafe_allow_html=True)

    st.markdown("#### 6 个月走势(基准化 = 100)")
    pick = st.multiselect("选择对比资产", codes,
                          default=["gold", "spx", "dxy", "vix"],
                          format_func=lambda c: C.ASSETS[c]["name"])
    fig = go.Figure()
    for code in pick:
        s = series_cache[code].dropna().last("180D")
        if s.empty:
            continue
        base = s.iloc[0]
        fig.add_trace(go.Scatter(x=s.index, y=s / base * 100, name=C.ASSETS[code]["name"],
                                 mode="lines", line=dict(width=2)))
    st.plotly_chart(style_fig(fig, 360), use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# 页面:利率与曲线
# ════════════════════════════════════════════════════════════════════════════
def page_rates():
    st.markdown('<div class="eyebrow">RATES & CURVE</div>', unsafe_allow_html=True)
    st.markdown("## 利率与曲线")
    if not core.fred_key():
        st.markdown('<div class="note">本页需要免费 FRED key(在 Secrets 设 FRED_API_KEY)。'
                    '没设的话,市场总览/情绪页仍可用。</div>', unsafe_allow_html=True)
        return

    tenors, yields, last_map = [], [], {}
    for label, sid in C.TREASURY.items():
        s = core.fred_series(sid).dropna()
        if not s.empty:
            tenors.append(label); yields.append(float(s.iloc[-1])); last_map[label] = s

    real = core.fred_series(C.REAL_YIELD_10Y).dropna()
    # 卡片:整条曲线 + 10Y 实际收益率
    items = [(f"{lab}", f"{y:.2f}%", None, T["muted"]) for lab, y in zip(tenors, yields)]
    if not real.empty:
        items.append(("10Y 实际(TIPS)", f"{real.iloc[-1]:.2f}%", "黄金头号变量", T["gold"]))
    if "10Y" in last_map and "2Y" in last_map:
        sp = (last_map["10Y"].iloc[-1] - last_map["2Y"].iloc[-1]) * 100
        items.append(("2s10s 利差", f"{sp:+.0f} bps",
                      "倒挂" if sp < 0 else "正常", T["down"] if sp < 0 else T["up"]))
    core.cards_row(items)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 当前收益率曲线")
        fig = go.Figure(go.Scatter(x=tenors, y=yields, mode="lines+markers",
                                   line=dict(color=T["accent"], width=2.5)))
        st.plotly_chart(style_fig(fig, 300), use_container_width=True)
    with c2:
        st.markdown("#### 10Y 名义 vs 实际收益率")
        fig = go.Figure()
        if "10Y" in last_map:
            n = last_map["10Y"].last("2Y")
            fig.add_trace(go.Scatter(x=n.index, y=n, name="10Y 名义", line=dict(color=T["accent"], width=2)))
        if not real.empty:
            r = real.last("2Y")
            fig.add_trace(go.Scatter(x=r.index, y=r, name="10Y 实际", line=dict(color=T["gold"], width=2)))
        st.plotly_chart(style_fig(fig, 300), use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# 页面:情绪 / 风险
# ════════════════════════════════════════════════════════════════════════════
def page_sentiment():
    st.markdown('<div class="eyebrow">SENTIMENT & RISK</div>', unsafe_allow_html=True)
    st.markdown("## 情绪 / 风险")
    s = C.SENTIMENT

    vix = core.yf_one(s["vix_ticker"], "2y").dropna()
    move = core.yf_one(s["move_ticker"], "2y").dropna()
    oas = core.fred_series(s["hy_oas_fred"]).dropna()

    items, regime_score = [], 0
    if not vix.empty:
        v = float(vix.iloc[-1]); pc = core.pct_window(vix)
        col = T["up"] if v < s["vix_calm"] else (T["down"] if v > s["vix_stress"] else T["gold"])
        items.append(("VIX 股市波动", f"{v:.1f}",
                      f"1年分位 {pc:.0f}%" if pc is not None else None, col))
        regime_score += (1 if v < s["vix_calm"] else (-1 if v > s["vix_stress"] else 0))
    if not move.empty:
        items.append(("MOVE 债市波动", f"{move.iloc[-1]:.0f}", None, T["muted"]))
    if not oas.empty:
        o = float(oas.iloc[-1])
        col = T["up"] if o < s["oas_calm"] else (T["down"] if o > s["oas_stress"] else T["gold"])
        items.append(("高收益债利差", f"{o:.2f}%", "信用压力信号", col))
        regime_score += (1 if o < s["oas_calm"] else (-1 if o > s["oas_stress"] else 0))
    core.cards_row(items)

    if regime_score >= 1:
        label, color = "RISK-ON · 风险偏好", T["up"]
    elif regime_score <= -1:
        label, color = "RISK-OFF · 避险", T["down"]
    else:
        label, color = "中性 · 观望", T["gold"]
    st.markdown(f'当前风险开关:<span class="pill" style="background:{color};color:#0a0d17">'
                f'{label}</span>', unsafe_allow_html=True)

    if not vix.empty:
        st.markdown("#### VIX 走势(2 年)")
        fig = go.Figure(go.Scatter(x=vix.index, y=vix, line=dict(color=T["down"], width=1.6)))
        fig.add_hline(y=s["vix_stress"], line=dict(color=T["down"], dash="dot", width=1))
        fig.add_hline(y=s["vix_calm"], line=dict(color=T["up"], dash="dot", width=1))
        st.plotly_chart(style_fig(fig, 300), use_container_width=True)
    if oas.empty and not core.fred_key():
        st.markdown('<div class="note">信用利差需 FRED key;VIX 不需要。</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# 页面:宏观日历 & 事件研究
# ════════════════════════════════════════════════════════════════════════════
def page_events():
    st.markdown('<div class="eyebrow">CALENDAR & EVENT STUDY</div>', unsafe_allow_html=True)
    st.markdown("## 宏观日历 & 事件研究")

    # —— 即将到来 ——
    today = pd.Timestamp(dt.date.today())
    st.markdown("#### 📅 即将到来")
    up_rows = []
    for k, ev in C.EVENTS.items():
        ds = resolve_event_dates(k)
        fut = [d for d in ds if d >= today]
        if fut:
            d = min(fut)
            up_rows.append((ev["label"], d.date(), (d - today).days))
    if up_rows:
        up_rows.sort(key=lambda r: r[1])
        df = pd.DataFrame(up_rows, columns=["事件", "下次日期", "剩余天数"])
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.markdown('<div class="note">暂无即将到来的事件(CPI/非农需 FRED key 才能取发布日历)。</div>',
                    unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 🔬 事件研究:历史上这类事件,你的资产怎么反应?")
    c1, c2, c3 = st.columns([1.3, 2, 1])
    with c1:
        ekey = st.selectbox("事件类型", list(C.EVENTS.keys()),
                            format_func=lambda k: C.EVENTS[k]["label"])
    with c2:
        assets = st.multiselect("观察资产", list(C.ASSETS.keys()),
                                default=C.DEFAULT_REACTION_ASSETS,
                                format_func=lambda c: C.ASSETS[c]["name"])
    with c3:
        post = st.slider("事件后天数", 3, 20, 10)
    pre = 5

    if not assets:
        st.info("选至少一个资产"); return

    dates = [d for d in resolve_event_dates(ekey) if d >= pd.Timestamp("2024-01-01")]
    if not dates:
        st.markdown('<div class="note">该事件暂无可用历史日期(CPI/非农需 FRED key)。</div>',
                    unsafe_allow_html=True)
        return

    price_dict = {a: asset_series(a, "5y") for a in assets}
    yflags = {a: C.ASSETS[a].get("is_yield", False) for a in assets}
    avg, moves, n = E.event_study(price_dict, dates, pre=pre, post=post, yield_flags=yflags)

    st.caption(f"样本:{C.EVENTS[ekey]['label']} · 共 {n} 次(2024 年至今)")
    if avg.empty:
        st.warning("窗口内数据不足,换个事件或缩短天数试试。"); return

    # 平均路径
    fig = go.Figure()
    for a in avg.columns:
        fig.add_trace(go.Scatter(x=avg.index, y=avg[a], name=C.ASSETS[a]["name"],
                                 mode="lines", line=dict(width=2)))
    fig.add_vline(x=0, line=dict(color=T["muted"], dash="dot", width=1))
    fig.update_layout(xaxis_title="相对事件日(交易日)")
    st.plotly_chart(style_fig(fig, 380), use_container_width=True)
    st.caption("纵轴 = 基准化到事件日(T0)=100 的平均路径。")

    # 汇总表
    rows = []
    for a in assets:
        sm = E.summarize_moves(moves, a)
        unit = "bps" if yflags[a] else "%"
        rows.append({
            "资产": C.ASSETS[a]["name"],
            f"T+1 均值({unit})": round(sm.get("T+1", {}).get("mean", float('nan')), 2),
            "T+1 上涨概率": f"{sm.get('T+1', {}).get('win', float('nan')):.0f}%",
            f"T+5 均值({unit})": round(sm.get("T+5", {}).get("mean", float('nan')), 2),
            f"T+10 均值({unit})": round(sm.get("T+10", {}).get("mean", float('nan')), 2),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.markdown('<div class="note">价格类资产为百分比变动,收益率类(美债)为 bps 变动。'
                '历史规律不代表未来,仅供研判参考,不构成投资建议。</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# 页面:CPI 详情
# ════════════════════════════════════════════════════════════════════════════
def page_cpi():
    st.markdown('<div class="eyebrow">CPI DETAIL</div>', unsafe_allow_html=True)
    st.markdown("## CPI 详情(美国)")
    if not core.fred_key():
        st.markdown('<div class="note">本页需要 FRED key。</div>', unsafe_allow_html=True)
        return

    items, hist = [], None
    for name, sid in C.CPI_COMPONENTS.items():
        s = core.fred_series(sid)
        y = core.yoy(s)
        if name == "整体 CPI":
            hist = s
        color = T["down"] if (y or 0) >= 3 else (T["up"] if (y or 0) < 2 else T["gold"])
        items.append((name + " 同比", f"{y:.1f}%" if y is not None else "—", None, color))
    core.cards_row(items)

    if hist is not None and not hist.dropna().empty:
        yoy_s = (hist / hist.shift(12) - 1).dropna() * 100
        yoy_s = yoy_s.last("5Y")
        st.markdown("#### 整体 CPI 同比(近 5 年)")
        fig = go.Figure(go.Scatter(x=yoy_s.index, y=yoy_s, line=dict(color=T["gold"], width=2)))
        fig.add_hline(y=2, line=dict(color=T["up"], dash="dot", width=1))
        st.plotly_chart(style_fig(fig, 320), use_container_width=True)
    st.markdown('<div class="note">同比由 FRED 月度指数计算(季调口径,展示用)。'
                '想看更细分项,在 config.py 的 CPI_COMPONENTS 里加 FRED 序列即可。</div>',
                unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# 占位页
# ════════════════════════════════════════════════════════════════════════════
def page_placeholder(title, desc):
    st.markdown(f"## {title}")
    st.markdown(f'<div class="note">{desc}</div>', unsafe_allow_html=True)


PAGE_FUNCS = {
    "overview": page_overview, "rates": page_rates, "sentiment": page_sentiment,
    "events": page_events, "cpi": page_cpi,
    "portfolio": lambda: page_placeholder("持仓监测 (Phase 2)",
        "下一步:你选好组合,这里盯实时盈亏、相关性、与宏观事件的暴露。架构已留好接口。"),
    "brief": lambda: page_placeholder("智能简报 (Phase 3)",
        "再下一步:接 Claude API,自动筛 MU/HBM 等催化剂新闻,每天生成结合你仓位的简报。"),
}


# ════════════════════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════════════════════
def main():
    if not gate():
        return
    with st.sidebar:
        st.markdown("### 🧭 宏观作战室")
        labels = [p[0] for p in C.PAGES]
        choice = st.radio("模块", labels, label_visibility="collapsed")
        key = dict((p[0], p[1]) for p in C.PAGES)[choice]
        st.divider()
        st.caption("数据:yfinance(免费)+ FRED(免费key)")
        st.caption("FRED key 状态:" + ("✅ 已配置" if core.fred_key() else "⚠️ 未配置(部分页受限)"))
        if st.button("🔄 清缓存刷新"):
            st.cache_data.clear(); st.rerun()
    PAGE_FUNCS[key]()
    st.markdown(f'<div style="color:{T["muted"]};font-size:11px;margin-top:24px;'
                f'border-top:1px solid {T["line"]};padding-top:12px">'
                f'数据更新 {dt.date.today()} · 仅供研究,不构成投资建议</div>', unsafe_allow_html=True)


main()
