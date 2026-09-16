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

    # 分组展示的 + 两张图要用的,合起来才是这一页真正需要取的序列
    codes = []
    for _, group in C.OVERVIEW_GROUPS:
        codes += group
    codes += [c for c in C.OVERVIEW_YIELD_CHART + C.OVERVIEW_PRICE_CHART if c not in codes]
    codes = [c for c in dict.fromkeys(codes) if c in C.ASSETS]

    series_cache = {}
    for code in codes:
        series_cache[code] = asset_series(code, "1y")

    def _card(code):
        s = series_cache.get(code, pd.Series(dtype=float))
        last, absc, pct = core.last_and_change(s)
        ch, color = core.chg_str(absc, pct, C.ASSETS[code].get("is_yield"))
        return (aname(code), core.fmt(code, last), ch, color)

    for label_key, group in C.OVERVIEW_GROUPS:
        group = [c for c in group if c in C.ASSETS]
        if not group:
            continue
        st.markdown(f"**{t(label_key)}**")
        core.cards_row([_card(c) for c in group])

    miss = [c for c in codes if series_cache[c].empty]
    if miss:
        st.markdown(f'<div class="note">{t("fetch_fail", names=", ".join(aname(c) for c in miss))}</div>',
                    unsafe_allow_html=True)
    st.markdown(f'<div class="note" style="margin-top:6px">{t("ov_quad_hint")}</div>',
                unsafe_allow_html=True)

    st.divider()

    # 时间窗口:两张图共用
    zh_keys = list(C.OVERVIEW_WINDOWS.keys())
    idx = zh_keys.index(C.OVERVIEW_DEFAULT_WINDOW) if C.OVERVIEW_DEFAULT_WINDOW in zh_keys else 1
    wins = C.OVERVIEW_WINDOWS_EN if lang() == "en" else C.OVERVIEW_WINDOWS
    wkeys = list(wins.keys())
    wlabel = st.selectbox(t("ov_window"), wkeys, index=min(idx, len(wkeys) - 1))
    days = wins[wlabel]

    # ── 图一:收益率,画原始 % ──
    st.markdown(f"#### {t('ov_chart_yield')}")
    ycodes = [c for c in C.OVERVIEW_YIELD_CHART if c in C.ASSETS]
    ypick = st.multiselect(t("pick_assets"), ycodes, default=ycodes,
                           format_func=aname, key="ov_yield_pick")
    fig = go.Figure()
    for code in ypick:
        s = core.recent(series_cache.get(code, pd.Series(dtype=float)), days=days)
        if s.empty:
            continue
        fig.add_trace(go.Scatter(x=s.index, y=s, name=aname(code), mode="lines",
                                 line=dict(width=2),
                                 hovertemplate="%{y:.2f}%<extra>" + aname(code) + "</extra>"))
    fig = style_fig(fig, 340)
    fig.update_layout(yaxis_title="%")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f'<div class="note">{t("ov_chart_note")}</div>', unsafe_allow_html=True)

    # ── 图二:价格类,基准化 = 100 ──
    st.markdown(f"#### {t('ov_chart_price')}")
    pcodes = [c for c in codes if not C.ASSETS[c].get("is_yield")]
    default_p = [c for c in C.OVERVIEW_PRICE_CHART if c in pcodes]
    ppick = st.multiselect(t("pick_assets"), pcodes, default=default_p,
                           format_func=aname, key="ov_price_pick")
    fig2 = go.Figure()
    for code in ppick:
        s = core.recent(series_cache.get(code, pd.Series(dtype=float)), days=days)
        if s.empty or s.iloc[0] == 0:
            continue
        fig2.add_trace(go.Scatter(x=s.index, y=s / s.iloc[0] * 100, name=aname(code),
                                  mode="lines", line=dict(width=2),
                                  hovertemplate="%{y:.1f}<extra>" + aname(code) + "</extra>"))
    fig2.add_hline(y=100, line=dict(color=T["line"], width=1, dash="dot"))
    st.plotly_chart(style_fig(fig2, 340), use_container_width=True)


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
# 页面:美债实验室(对应《美债研究手册》第一 ~ 第四层)
# ════════════════════════════════════════════════════════════════════════════
def _ust_pick_window():
    """回看窗口下拉框。中英文标签不同但天数一一对应,按位置取默认值。"""
    zh_keys = list(C.UST_WINDOWS.keys())
    idx = zh_keys.index(C.UST_DEFAULT_WINDOW) if C.UST_DEFAULT_WINDOW in zh_keys else 1
    wins = C.UST_WINDOWS_EN if lang() == "en" else C.UST_WINDOWS
    keys = list(wins.keys())
    label = st.selectbox(t("ust_window"), keys, index=min(idx, len(keys) - 1))
    return label, wins[label]


def _chg_bp(s: pd.Series, w: int):
    """序列在 w 个观测值之前到现在的变动,换算成 bps(FRED 利率序列单位是 %)。"""
    s = s.dropna()
    if len(s) < w + 1:
        return None
    return float((s.iloc[-1] - s.iloc[-(w + 1)]) * 100)


def _aligned_chg(series_map: dict, w: int):
    """先对齐再算变动,这样恒等式(名义 = 实际 + 通胀补偿)能严格对上。
    任何一个序列缺失就返回 None。额外带回 _start / _end:对齐之后这一刀真正用的窗口
    ——期限溢价发布有滞后,所以两刀的窗口末端可能差几天,名义变动也会差几个 bps。"""
    parts = {k: v.dropna() for k, v in series_map.items() if v is not None and not v.dropna().empty}
    if len(parts) != len(series_map):
        return None
    df = pd.concat(parts, axis=1).dropna()
    if len(df) < w + 1:
        return None
    d = (df.iloc[-1] - df.iloc[-(w + 1)]) * 100
    out = {k: float(d[k]) for k in series_map}
    out["_start"], out["_end"] = df.index[-(w + 1)], df.index[-1]
    return out


def _contrib_bar(pairs, title, asof=None):
    """pairs: [(名称, bps, 颜色)] —— 横向条形图,正负都画。"""
    names = [p[0] for p in pairs]
    vals = [p[1] for p in pairs]
    colors = [p[2] for p in pairs]
    fig = go.Figure(go.Bar(
        x=vals, y=names, orientation="h", marker_color=colors,
        text=[f"{v:+.0f}" for v in vals], textposition="outside",
        hovertemplate="%{y}: %{x:+.0f} bps<extra></extra>", cliponaxis=False))
    st.markdown(f"**{title}**")
    if asof:
        st.caption(f"{asof[0].date()} → {asof[1].date()}")
    # style_fig 会把 showlegend 打开,所以关图例要放在它之后
    fig = style_fig(fig, 170)
    fig.update_layout(showlegend=False, xaxis_title="bps")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)


def page_ust():
    st.markdown('<div class="eyebrow">TREASURY LAB</div>', unsafe_allow_html=True)
    st.markdown(f"## {t('ust_title')}")
    if not core.fred_key():
        st.markdown(f'<div class="note">{t("ust_need_key")}</div>', unsafe_allow_html=True)
        return

    U = C.UST
    s_nom = core.fred_series(U["nominal_10y"])
    s_real = core.fred_series(U["real_10y"])
    s_be = core.fred_series(U["breakeven_10y"])
    s_5y5y = core.fred_series(U["breakeven_5y5y"])
    s_tp = core.fred_series(U["term_premium_10y"])
    s_zero = core.fred_series(U["fitted_zero_10y"])
    s_2y = core.fred_series(U["nominal_2y"])
    s_3m = core.fred_series(U["nominal_3m"])
    s_2s10s = core.fred_series(U["spread_2s10s"])
    s_3m10s = core.fred_series(U["spread_3m10s"])
    move = core.yf_one(U["move_ticker"], "2y")

    # ── 快照卡片 ──
    def _last(s):
        s = s.dropna()
        return float(s.iloc[-1]) if not s.empty else None

    items = []
    for key, s, color, note in [
        ("ust_nom10", s_nom, T["accent"], None),
        ("ust_real10", s_real, T["accent"], t("gold_driver")),
        ("ust_be10", s_be, T["gold"], None),
        ("ust_be5y5y", s_5y5y, T["gold"], t("ust_anchor")),
        ("ust_tp10", s_tp, T["up"], t("ust_tp_note")),
    ]:
        v = _last(s)
        items.append((t(key), f"{v:.2f}%" if v is not None else "—", note, color))
    for key, s in [("ust_2s10s", s_2s10s), ("ust_3m10s", s_3m10s)]:
        v = _last(s)
        items.append((t(key), f"{v * 100:+.0f} bps" if v is not None else "—",
                      t("inverted") if (v or 0) < 0 else t("normal"),
                      T["down"] if (v or 0) < 0 else T["up"]))
    mv = _last(move)
    items.append((t("ust_move"), f"{mv:.0f}" if mv is not None else "—", None, T["muted"]))
    core.cards_row(items)

    win_label, w = _ust_pick_window()
    st.divider()

    # ── 第一层:收益率分解归因 ──
    st.markdown(f"### {t('ust_decomp_title')}")
    d_nom = _chg_bp(s_nom, w)
    cut1 = _aligned_chg({"nom": s_nom, "real": s_real, "be": s_be}, w)
    # 第二刀必须用同口径的零息收益率减期限溢价,不能用 DGS10(附息)——见 config 里的注释
    cut2 = _aligned_chg({"zero": s_zero, "tp": s_tp}, w)

    if d_nom is None or cut1 is None:
        st.markdown(f'<div class="note">{t("fetch_fail", names="FRED")}</div>', unsafe_allow_html=True)
    else:
        st.caption(t("ust_decomp_sub", win=win_label, bp=f"{cut1['nom']:+.0f}"))
        c1, c2 = st.columns(2)
        with c1:
            _contrib_bar([
                (t("ust_bar_nominal"), cut1["nom"], T["muted"]),
                (t("ust_bar_real"), cut1["real"], T["accent"]),
                (t("ust_bar_be"), cut1["be"], T["gold"]),
            ], t("ust_cut1"), asof=(cut1["_start"], cut1["_end"]))
        with c2:
            if cut2 is None:
                st.markdown(f"**{t('ust_cut2')}**")
                st.markdown(f'<div class="note">{t("ust_tp_missing")}</div>', unsafe_allow_html=True)
            else:
                _contrib_bar([
                    (t("ust_bar_zero"), cut2["zero"], T["muted"]),
                    (t("ust_bar_path"), cut2["zero"] - cut2["tp"], T["down"]),
                    (t("ust_bar_tp"), cut2["tp"], T["up"]),
                ], t("ust_cut2"), asof=(cut2["_start"], cut2["_end"]))
                st.caption(t("ust_tp_lag"))

        # 一句话解读:哪个通道主导
        thr = C.UST_DOMINANT_SHARE
        pct_txt = f"{thr * 100:.0f}"
        if abs(cut1["nom"]) < C.UST_REGIME_MIN_BP:
            read = t("ust_read_flat", win=win_label, bp=f"{cut1['nom']:+.0f}")
        else:
            denom1 = abs(cut1["real"]) + abs(cut1["be"]) or 1.0
            if abs(cut1["be"]) / denom1 > thr:
                read = t("ust_read_c")
            elif cut2 is None:
                read = t("ust_read_real")
            else:
                tp, path = cut2["tp"], cut2["zero"] - cut2["tp"]
                denom2 = abs(tp) + abs(path) or 1.0
                if abs(tp) / denom2 > thr:
                    read = t("ust_read_b")
                elif abs(path) / denom2 > thr:
                    read = t("ust_read_a")
                else:
                    read = t("ust_read_mix", pct=pct_txt)
        st.markdown(read)
        st.markdown(f'<div class="note">{t("ust_verify")}</div>', unsafe_allow_html=True)

    st.divider()

    # ── 第二层:曲线形态四象限 ──
    st.markdown(f"### {t('ust_regime_title')}")
    d2, d10 = _chg_bp(s_2y, w), _chg_bp(s_nom, w)
    if d2 is None or d10 is None:
        st.markdown(f'<div class="note">{t("fetch_fail", names="DGS2 / DGS10")}</div>', unsafe_allow_html=True)
    else:
        level = (d2 + d10) / 2          # 水平:上=熊(收益率涨),下=牛
        slope = d10 - d2                # 斜率:正=陡化,负=平坦化
        mn = C.UST_REGIME_MIN_BP
        # 两个维度各自判阈值:动得不够就不给方向,免得把几个 bps 的噪音讲成"熊陡"
        lv = 0 if abs(level) < mn else (1 if level > 0 else -1)
        sl = 0 if abs(slope) < mn else (1 if slope > 0 else -1)
        REGIME = {
            (0, 0):   ("ust_regime_flat", T["muted"]),
            (0, 1):   ("ust_steepen",     T["gold"]),
            (0, -1):  ("ust_flatten",     T["gold"]),
            (1, 0):   ("ust_bear_par",    T["down"]),
            (-1, 0):  ("ust_bull_par",    T["up"]),
            (1, 1):   ("ust_bear_steep",  T["down"]),
            (1, -1):  ("ust_bear_flat",   T["down"]),
            (-1, 1):  ("ust_bull_steep",  T["up"]),
            (-1, -1): ("ust_bull_flat",   T["up"]),
        }
        key, color = REGIME[(lv, sl)]
        label = t(key, bp=f"{mn:.0f}") if key == "ust_regime_flat" else t(key)
        st.markdown(f'{t("ust_regime_now")}<span class="pill" style="background:{color};'
                    f'color:#0a0d17">{label}</span>', unsafe_allow_html=True)
        st.caption(t("ust_regime_detail", win=win_label,
                     d2=f"{d2:+.0f}", d10=f"{d10:+.0f}", ds=f"{slope:+.0f}"))

        # 过去 1 年的每周轨迹
        al = pd.concat({"2Y": s_2y.dropna(), "10Y": s_nom.dropna()}, axis=1).dropna()
        wk = al.resample("W-FRI").last().dropna()
        ww = max(1, int(round(w / 5)))
        dd = ((wk - wk.shift(ww)) * 100).dropna()
        dd = dd[dd.index >= dd.index.max() - pd.DateOffset(years=1)]
        if len(dd) > 3:
            x = dd["10Y"] - dd["2Y"]
            y = (dd["10Y"] + dd["2Y"]) / 2
            st.markdown(f"#### {t('ust_quad_title')}")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x[:-1], y=y[:-1], mode="markers",
                                     marker=dict(size=7, color=T["muted"], opacity=.55),
                                     hovertemplate="利差 %{x:+.0f} · 水平 %{y:+.0f} bps<extra></extra>"))
            fig.add_trace(go.Scatter(x=[x.iloc[-1]], y=[y.iloc[-1]], mode="markers",
                                     marker=dict(size=14, color=T["gold"],
                                                 line=dict(color=T["txt"], width=1)),
                                     hovertemplate="最新:利差 %{x:+.0f} · 水平 %{y:+.0f} bps<extra></extra>"))
            fig.add_hline(y=0, line=dict(color=T["line"], width=1))
            fig.add_vline(x=0, line=dict(color=T["line"], width=1))
            fig = style_fig(fig, 340)
            fig.update_layout(showlegend=False, xaxis_title=t("ust_quad_x"),
                              yaxis_title=t("ust_quad_y"))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(f'<div class="note">{t("ust_quad_note")}</div>', unsafe_allow_html=True)

    st.divider()

    # ── 第三层:拍卖监测 ──
    st.markdown(f"### {t('ust_auction_title')}")
    st.caption(t("ust_auction_sub"))
    au = core.fetch_auctions(C.AUCTION_LOOKBACK_DAYS)
    if au.empty:
        st.markdown(f'<div class="note">{t("ust_auction_fail")}</div>', unsafe_allow_html=True)
    else:
        au = core.btc_vs_baseline(au, C.AUCTION_BASELINE_N)
        recent_au = au.sort_values("date", ascending=False).head(C.AUCTION_SHOW_N)
        # 缺字段进了 DataFrame 会变成 NaN,"is not None" 拦不住,统一用这个判空
        def _num(v, spec, suffix=""):
            if v is None or pd.isna(v):
                return "—"
            return format(v, spec) + suffix

        rows = []
        for _, r in recent_au.iterrows():
            dealer = r.get("dealer_pct")
            warn = (dealer is not None and pd.notna(dealer) and dealer > C.AUCTION_DEALER_WARN)
            rows.append({
                t("ust_col_date"): r["date"].date(),
                t("ust_col_term"): r["term"],
                t("ust_col_yield"): _num(r.get("high_yield"), ".3f", "%"),
                t("ust_col_btc"): _num(r.get("btc"), ".2f"),
                t("ust_col_btc_diff", n=C.AUCTION_BASELINE_N): _num(r.get("btc_diff"), "+.2f"),
                t("ust_col_dealer"): _num(dealer, ".1f", "%" + (" ⚠️" if warn else "")),
                t("ust_col_indirect"): _num(r.get("indirect_pct"), ".1f", "%"),
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        st.markdown(f'<div class="note">{t("ust_auction_note", n=C.AUCTION_BASELINE_N)}</div>',
                    unsafe_allow_html=True)

    st.divider()

    # ── 第四层:定价检验 ──
    st.markdown(f"### {t('ust_check_title')}")
    mvs = move.dropna()
    if not mvs.empty:
        fig = go.Figure(go.Scatter(x=mvs.index, y=mvs, line=dict(color=T["down"], width=1.6)))
        st.plotly_chart(style_fig(fig, 240), use_container_width=True)
    st.markdown(f'<div class="note">{t("ust_move_note")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="note" style="margin-top:10px">{t("ust_cot_note")}</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="note" style="margin-top:10px">{t("ust_handbook")}</div>',
                unsafe_allow_html=True)


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
    "overview": page_overview, "rates": page_rates, "ust": page_ust, "sentiment": page_sentiment,
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
