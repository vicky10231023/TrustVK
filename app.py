"""
app.py —— 全球宏观作战室(Phase 1)· 中 / 英双语
运行: streamlit run app.py
部署: GitHub → share.streamlit.io,Secrets 里设 FRED_API_KEY 和 APP_PASSWORD
语言: 侧栏最上面切换 中文 / English;网址加 ?lang=en 直接打开英文版(例如 https://xxx.streamlit.app/?lang=en)
      所有界面文字都在 config.py 的 TEXT 里,资产/事件/页面名在各自的 name_en / label_en / PAGES 里。
"""
import datetime as dt
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

import config as C
import core
import events as E

st.set_page_config(page_title="宏观作战室 · Macro War Room", page_icon="🧭", layout="wide")
core.inject_css()
T = C.THEME


# ════════════════════════════════════════════════════════════════════════════
# 语言(中 / 英)
# ════════════════════════════════════════════════════════════════════════════
def init_lang():
    """第一次打开时:看网址有没有 ?lang=en / ?lang=zh,没有就用 config 里的默认语言。"""
    if "lang" not in st.session_state:
        q = str(st.query_params.get("lang", "")).lower()
        if q.startswith("en"):
            st.session_state["lang"] = "en"
        elif q.startswith("zh"):
            st.session_state["lang"] = "zh"
        else:
            st.session_state["lang"] = C.DEFAULT_LANG
    st.session_state.setdefault("lang_radio", st.session_state["lang"])


def _on_lang_change():
    """侧栏切换语言时:记住选择,并把 ?lang= 写进网址(方便直接复制链接分享)。"""
    st.session_state["lang"] = st.session_state["lang_radio"]
    st.query_params["lang"] = st.session_state["lang"]


def lang_selector():
    with st.sidebar:
        st.radio("Language", list(C.LANGS.keys()), format_func=lambda c: C.LANGS[c],
                 horizontal=True, label_visibility="collapsed",
                 key="lang_radio", on_change=_on_lang_change)


def lang():
    return st.session_state.get("lang", C.DEFAULT_LANG)


def t(key, **kw):
    """取当前语言的界面文字;英文缺了就退回中文。带 {xxx} 占位符的用 kw 填。"""
    table = C.TEXT.get(lang(), C.TEXT["zh"])
    s = table.get(key) or C.TEXT["zh"].get(key, key)
    return s.format(**kw) if kw else s


def aname(code):
    """资产显示名(中/英)。"""
    a = C.ASSETS[code]
    return (a.get("name_en") or a["name"]) if lang() == "en" else a["name"]


def ename(key):
    """事件显示名(中/英)。"""
    e = C.EVENTS[key]
    return (e.get("label_en") or e["label"]) if lang() == "en" else e["label"]


def cname(key):
    """CPI 分项显示名(中/英)。"""
    c = C.CPI_COMPONENTS[key]
    return (c.get("name_en") or c["name"]) if lang() == "en" else c["name"]


def pname(key):
    """页面显示名(中/英)。"""
    for zh, en, k, _ in C.PAGES:
        if k == key:
            return en if lang() == "en" else zh
    return key


# ════════════════════════════════════════════════════════════════════════════
# 密码门
# ════════════════════════════════════════════════════════════════════════════
def gate():
    if st.session_state.get("authed"):
        return True
    st.markdown(f"### 🔒 {t('app_title')}")
    st.caption(t("gate_caption"))
    pw = st.text_input(t("gate_pw"), type="password", label_visibility="collapsed")
    if st.button(t("gate_enter")):
        if pw == core.app_password():
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error(t("gate_wrong"))
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
    st.markdown(f"## {t('overview_title')}")

    codes = list(C.ASSETS.keys())
    items = []
    series_cache = {}
    for code in codes:
        s = asset_series(code, "1y")
        series_cache[code] = s
        last, absc, pct = core.last_and_change(s)
        ch, color = core.chg_str(absc, pct, C.ASSETS[code].get("is_yield"))
        items.append((aname(code), core.fmt(code, last), ch, color))
    core.cards_row(items)

    miss = [c for c in codes if series_cache[c].empty]
    if miss:
        st.markdown(f'<div class="note">{t("fetch_fail", names=", ".join(aname(c) for c in miss))}</div>',
                    unsafe_allow_html=True)

    st.markdown(f"#### {t('trend_6m')}")
    pick = st.multiselect(t("pick_assets"), codes,
                          default=["gold", "spx", "dxy", "vix"],
                          format_func=aname)
    fig = go.Figure()
    for code in pick:
        s = core.recent(series_cache[code], days=180)
        if s.empty:
            continue
        base = s.iloc[0]
        fig.add_trace(go.Scatter(x=s.index, y=s / base * 100, name=aname(code),
                                 mode="lines", line=dict(width=2)))
    st.plotly_chart(style_fig(fig, 360), use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# 页面:利率与曲线
# ════════════════════════════════════════════════════════════════════════════
def page_rates():
    st.markdown('<div class="eyebrow">RATES & CURVE</div>', unsafe_allow_html=True)
    st.markdown(f"## {t('rates_title')}")
    if not core.fred_key():
        st.markdown(f'<div class="note">{t("rates_need_key")}</div>', unsafe_allow_html=True)
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
        items.append((t("real10"), f"{real.iloc[-1]:.2f}%", t("gold_driver"), T["gold"]))
    if "10Y" in last_map and "2Y" in last_map:
        sp = (last_map["10Y"].iloc[-1] - last_map["2Y"].iloc[-1]) * 100
        items.append((t("spread_2s10s"), f"{sp:+.0f} bps",
                      t("inverted") if sp < 0 else t("normal"), T["down"] if sp < 0 else T["up"]))
    core.cards_row(items)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"#### {t('curve_now')}")
        fig = go.Figure(go.Scatter(x=tenors, y=yields, mode="lines+markers",
                                   line=dict(color=T["accent"], width=2.5)))
        st.plotly_chart(style_fig(fig, 300), use_container_width=True)
    with c2:
        st.markdown(f"#### {t('nominal_vs_real')}")
        fig = go.Figure()
        if "10Y" in last_map:
            n = core.recent(last_map["10Y"], years=2)
            fig.add_trace(go.Scatter(x=n.index, y=n, name=t("nominal10"), line=dict(color=T["accent"], width=2)))
        if not real.empty:
            r = core.recent(real, years=2)
            fig.add_trace(go.Scatter(x=r.index, y=r, name=t("real10_short"), line=dict(color=T["gold"], width=2)))
        st.plotly_chart(style_fig(fig, 300), use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# 页面:情绪 / 风险
# ════════════════════════════════════════════════════════════════════════════
def page_sentiment():
    st.markdown('<div class="eyebrow">SENTIMENT & RISK</div>', unsafe_allow_html=True)
    st.markdown(f"## {t('sent_title')}")
    s = C.SENTIMENT

    vix = core.yf_one(s["vix_ticker"], "2y").dropna()
    move = core.yf_one(s["move_ticker"], "2y").dropna()
    oas = core.fred_series(s["hy_oas_fred"]).dropna()

    items, regime_score = [], 0
    if not vix.empty:
        v = float(vix.iloc[-1]); pc = core.pct_window(vix)
        col = T["up"] if v < s["vix_calm"] else (T["down"] if v > s["vix_stress"] else T["gold"])
        items.append((t("vix_card"), f"{v:.1f}",
                      t("pct_1y", pc=f"{pc:.0f}") if pc is not None else None, col))
        regime_score += (1 if v < s["vix_calm"] else (-1 if v > s["vix_stress"] else 0))
    if not move.empty:
        items.append((t("move_card"), f"{move.iloc[-1]:.0f}", None, T["muted"]))
    if not oas.empty:
        o = float(oas.iloc[-1])
        col = T["up"] if o < s["oas_calm"] else (T["down"] if o > s["oas_stress"] else T["gold"])
        items.append((t("hy_card"), f"{o:.2f}%", t("credit_signal"), col))
        regime_score += (1 if o < s["oas_calm"] else (-1 if o > s["oas_stress"] else 0))
    core.cards_row(items)

    if regime_score >= 1:
        label, color = t("risk_on"), T["up"]
    elif regime_score <= -1:
        label, color = t("risk_off"), T["down"]
    else:
        label, color = t("neutral"), T["gold"]
    st.markdown(f'{t("risk_switch")}<span class="pill" style="background:{color};color:#0a0d17">'
                f'{label}</span>', unsafe_allow_html=True)

    if not vix.empty:
        st.markdown(f"#### {t('vix_2y')}")
        fig = go.Figure(go.Scatter(x=vix.index, y=vix, line=dict(color=T["down"], width=1.6)))
        fig.add_hline(y=s["vix_stress"], line=dict(color=T["down"], dash="dot", width=1))
        fig.add_hline(y=s["vix_calm"], line=dict(color=T["up"], dash="dot", width=1))
        st.plotly_chart(style_fig(fig, 300), use_container_width=True)
    if oas.empty and not core.fred_key():
        st.markdown(f'<div class="note">{t("oas_need_key")}</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# 页面:宏观日历 & 事件研究
# ════════════════════════════════════════════════════════════════════════════
def page_events():
    st.markdown('<div class="eyebrow">CALENDAR & EVENT STUDY</div>', unsafe_allow_html=True)
    st.markdown(f"## {t('events_title')}")

    # —— 即将到来 ——
    today = pd.Timestamp(dt.date.today())
    st.markdown(f"#### {t('upcoming')}")
    up_rows = []
    for k, ev in C.EVENTS.items():
        ds = resolve_event_dates(k)
        fut = [d for d in ds if d >= today]
        if fut:
            d = min(fut)
            up_rows.append((ename(k), d.date(), (d - today).days))
    if up_rows:
        up_rows.sort(key=lambda r: r[1])
        df = pd.DataFrame(up_rows, columns=[t("col_event"), t("col_next"), t("col_days")])
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.markdown(f'<div class="note">{t("no_upcoming")}</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown(f"#### {t('study_title')}")
    c1, c2, c3 = st.columns([1.3, 2, 1])
    with c1:
        ekey = st.selectbox(t("event_type"), list(C.EVENTS.keys()), format_func=ename)
    with c2:
        assets = st.multiselect(t("watch_assets"), list(C.ASSETS.keys()),
                                default=C.DEFAULT_REACTION_ASSETS,
                                format_func=aname)
    with c3:
        post = st.slider(t("post_days"), 3, 20, 10)
    pre = 5

    if not assets:
        st.info(t("pick_one")); return

    dates = [d for d in resolve_event_dates(ekey) if d >= pd.Timestamp("2024-01-01")]
    if not dates:
        st.markdown(f'<div class="note">{t("no_dates")}</div>', unsafe_allow_html=True)
        return

    price_dict = {a: asset_series(a, "5y") for a in assets}
    yflags = {a: C.ASSETS[a].get("is_yield", False) for a in assets}
    avg, moves, n = E.event_study(price_dict, dates, pre=pre, post=post, yield_flags=yflags)

    st.caption(t("sample", label=ename(ekey), n=n))
    if avg.empty:
        st.warning(t("not_enough")); return

    # 平均路径
    fig = go.Figure()
    for a in avg.columns:
        fig.add_trace(go.Scatter(x=avg.index, y=avg[a], name=aname(a),
                                 mode="lines", line=dict(width=2)))
    fig.add_vline(x=0, line=dict(color=T["muted"], dash="dot", width=1))
    fig.update_layout(xaxis_title=t("x_rel"))
    st.plotly_chart(style_fig(fig, 380), use_container_width=True)
    st.caption(t("y_note"))

    # 汇总表
    rows = []
    for a in assets:
        sm = E.summarize_moves(moves, a)
        unit = "bps" if yflags[a] else "%"
        rows.append({
            t("col_asset"): aname(a),
            t("col_t1", unit=unit): round(sm.get("T+1", {}).get("mean", float('nan')), 2),
            t("col_t1_win"): f"{sm.get('T+1', {}).get('win', float('nan')):.0f}%",
            t("col_t5", unit=unit): round(sm.get("T+5", {}).get("mean", float('nan')), 2),
            t("col_t10", unit=unit): round(sm.get("T+10", {}).get("mean", float('nan')), 2),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.markdown(f'<div class="note">{t("study_note")}</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# 页面:CPI 详情
# ════════════════════════════════════════════════════════════════════════════
def page_cpi():
    st.markdown('<div class="eyebrow">CPI DETAIL</div>', unsafe_allow_html=True)
    st.markdown(f"## {t('cpi_title')}")
    if not core.fred_key():
        st.markdown(f'<div class="note">{t("cpi_need_key")}</div>', unsafe_allow_html=True)
        return

    items, hist = [], None
    for key, comp in C.CPI_COMPONENTS.items():
        s = core.fred_series(comp["fred"])
        y = core.yoy(s)
        if key == C.CPI_HEADLINE_KEY:
            hist = s
        color = T["down"] if (y or 0) >= 3 else (T["up"] if (y or 0) < 2 else T["gold"])
        items.append((cname(key) + t("yoy"), f"{y:.1f}%" if y is not None else "—", None, color))
    core.cards_row(items)

    if hist is not None and not hist.dropna().empty:
        yoy_s = (hist / hist.shift(12) - 1).dropna() * 100
        yoy_s = core.recent(yoy_s, years=5)
        st.markdown(f"#### {t('cpi_chart')}")
        fig = go.Figure(go.Scatter(x=yoy_s.index, y=yoy_s, line=dict(color=T["gold"], width=2)))
        fig.add_hline(y=2, line=dict(color=T["up"], dash="dot", width=1))
        st.plotly_chart(style_fig(fig, 320), use_container_width=True)
    st.markdown(f'<div class="note">{t("cpi_note")}</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# 占位页
# ════════════════════════════════════════════════════════════════════════════
def page_placeholder(title, desc):
    st.markdown(f"## {title}")
    st.markdown(f'<div class="note">{desc}</div>', unsafe_allow_html=True)


PAGE_FUNCS = {
    "overview": page_overview, "rates": page_rates, "sentiment": page_sentiment,
    "events": page_events, "cpi": page_cpi,
    "portfolio": lambda: page_placeholder(t("portfolio_title"), t("portfolio_desc")),
    "brief": lambda: page_placeholder(t("brief_title"), t("brief_desc")),
}


# ════════════════════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════════════════════
def main():
    init_lang()
    lang_selector()          # 语言切换放在侧栏最上面,密码页也能切
    if not gate():
        return
    with st.sidebar:
        st.markdown(f"### 🧭 {t('app_title')}")
        keys = [p[2] for p in C.PAGES]
        if st.session_state.get("page") not in keys:
            st.session_state["page"] = keys[0]
        # 用 key 当选项、pname 显示中/英名;切换语言后仍停在当前页
        choice = st.radio("Module", keys, index=keys.index(st.session_state["page"]),
                          format_func=pname, label_visibility="collapsed",
                          key=f"page_radio_{lang()}")
        st.session_state["page"] = choice
        st.divider()
        st.caption(t("sidebar_data"))
        st.caption(t("fred_status") + (t("fred_ok") if core.fred_key() else t("fred_missing")))
        if st.button(t("refresh")):
            st.cache_data.clear(); st.rerun()
    PAGE_FUNCS[choice]()
    st.markdown(f'<div style="color:{T["muted"]};font-size:11px;margin-top:24px;'
                f'border-top:1px solid {T["line"]};padding-top:12px">'
                f'{t("footer", date=dt.date.today())}</div>', unsafe_allow_html=True)


main()
