"""
app.py —— 全球宏观作战室(Phase 1)· 中 / 英双语
运行: streamlit run app.py
部署: GitHub → share.streamlit.io,Secrets 里设 FRED_API_KEY 和 APP_PASSWORD
语言: 侧栏最上面切换 中文 / English;网址加 ?lang=en 直接打开英文版(例如 https://xxx.streamlit.app/?lang=en)
      所有界面文字都在 config.py 的 TEXT 里,资产/事件/页面名在各自的 name_en / label_en / PAGES 里。
"""
import datetime as dt
import json

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
# 页面:决策台
# 四层框架的落地页。设计意图:平时只读 —— 决策只在预定复盘日,或触发清单上的事
# 真的发生时才做。这道闸门挡的不是判断,是「有看法就想下注」那个冲动。
# ════════════════════════════════════════════════════════════════════════════
def _desk_infl():
    """通胀轴:核心PCE 3个月年化,看连续下行了几个月。返回 (最新值%, 连降月数)。"""
    idx = core.fred_series(C.DESK["infl_series"]).dropna()
    if len(idx) < 8:
        return None, 0
    ann = ((idx / idx.shift(3)) ** 4 - 1) * 100      # 3个月年化
    ann = ann.dropna()
    if ann.empty:
        return None, 0
    n = 0
    for i in range(len(ann) - 1, 0, -1):
        if ann.iloc[i] < ann.iloc[i - 1]:
            n += 1
        else:
            break
    return float(ann.iloc[-1]), n


def _desk_infl_monthly():
    """通胀轴:核心PCE 3个月年化的完整月度序列(轨迹图和当前值都用它)。"""
    idx = core.fred_series(C.DESK["infl_series"], start="2015-01-01").dropna()
    if len(idx) < 8:
        return pd.Series(dtype=float)
    return (((idx / idx.shift(3)) ** 4 - 1) * 100).dropna()


def _desk_growth_monthly():
    """增长轴:初请4周均值,取每月最后一个读数,和通胀轴对齐成月度。"""
    s = core.fred_series(C.DESK["growth_series"], start="2015-01-01").dropna()
    if s.empty:
        return s
    return s.resample("ME").last().dropna()


def _desk_cell(infl_v, gro_v):
    """按水平判格:各轴一条分界线。返回 dk_box1..4 的 key,数据缺失返回 None。"""
    if infl_v is None or gro_v is None:
        return None
    hot = infl_v >= C.DESK["infl_calm"]
    weak = gro_v >= C.DESK["growth_calm"]
    if not hot and not weak:
        return "dk_box1"   # 软着陆
    if hot and not weak:
        return "dk_box2"   # 过热
    if not hot and weak:
        return "dk_box3"   # 过度收紧
    return "dk_box4"       # 滞胀


def _desk_cell_history(infl_s, gro_s):
    """把两条月度序列对齐,逐月算出所在格子。返回 DataFrame(infl/gro/cell)。"""
    if infl_s.empty or gro_s.empty:
        return pd.DataFrame()
    df = pd.concat({"infl": infl_s, "gro": gro_s}, axis=1)
    df = df.resample("ME").last().dropna()
    if df.empty:
        return df
    df["cell"] = [_desk_cell(r.infl, r.gro) for r in df.itertuples()]
    return df


def _desk_held_months(df):
    """当前格子已经连续保持了几个月。"""
    if df.empty:
        return 0
    cells = list(df["cell"])
    now, n = cells[-1], 0
    for c in reversed(cells):
        if c == now:
            n += 1
        else:
            break
    return n


def _desk_grid_fig(df, months, height=420):
    """四象限图:两条分界线切出四格,点是每个月的位置,最新一点高亮。
    纵轴是初请(数字越小增长越强),所以反转,让"强"在上面。"""
    D = C.DESK
    tail = df.tail(months)
    fig = go.Figure()

    x_lo = min(tail["infl"].min(), D["infl_calm"]) - 0.6
    x_hi = max(tail["infl"].max(), D["infl_warn"]) + 0.4
    y_lo = min(tail["gro"].min(), D["growth_calm"]) - 25_000
    y_hi = max(tail["gro"].max(), D["growth_warn"]) + 25_000

    # 四格底色:分界线切开(纵轴已反转,所以"上=强"对应 claims 小)
    for x0, x1, y0, y1, col in [
        (x_lo, D["infl_calm"], y_lo, D["growth_calm"], T["up"]),      # ① 软着陆
        (D["infl_calm"], x_hi, y_lo, D["growth_calm"], T["gold"]),    # ② 过热
        (x_lo, D["infl_calm"], D["growth_calm"], y_hi, T["accent"]),  # ③ 过度收紧
        (D["infl_calm"], x_hi, D["growth_calm"], y_hi, T["down"]),    # ④ 滞胀
    ]:
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                      fillcolor=col, opacity=0.07, line_width=0, layer="below")

    # 分界线(实) / 裂缝线(虚)
    fig.add_vline(x=D["infl_calm"], line=dict(color=T["line"], width=1.5))
    fig.add_hline(y=D["growth_calm"], line=dict(color=T["line"], width=1.5))
    fig.add_vline(x=D["infl_warn"], line=dict(color=T["muted"], width=1, dash="dot"))
    fig.add_hline(y=D["growth_warn"], line=dict(color=T["muted"], width=1, dash="dot"))

    # 四个格子的名字,放在各自区域的角上
    for x, y, key, anchor in [
        (x_lo, y_lo, "dk_box1", "left"), (x_hi, y_lo, "dk_box2", "right"),
        (x_lo, y_hi, "dk_box3", "left"), (x_hi, y_hi, "dk_box4", "right"),
    ]:
        fig.add_annotation(x=x, y=y, text=t(key), showarrow=False,
                           xanchor=anchor, yanchor="top" if y == y_lo else "bottom",
                           font=dict(color=T["muted"], size=11))

    # 轨迹
    fig.add_trace(go.Scatter(
        x=tail["infl"], y=tail["gro"], mode="lines+markers",
        line=dict(color=T["muted"], width=1.2),
        marker=dict(size=6, color=T["muted"], opacity=.6),
        hovertemplate="%{x:.2f}% · %{y:,.0f}<extra>%{text}</extra>",
        text=[d.strftime("%Y-%m") for d in tail.index]))
    last = tail.iloc[-1]
    fig.add_trace(go.Scatter(
        x=[last["infl"]], y=[last["gro"]], mode="markers",
        marker=dict(size=15, color=T["gold"], line=dict(color=T["txt"], width=1.5)),
        hovertemplate="%{x:.2f}% · %{y:,.0f}<extra>" + tail.index[-1].strftime("%Y-%m") + "</extra>"))

    fig = style_fig(fig, height)
    fig.update_layout(showlegend=False, xaxis_title=t("dk_axis_x"), yaxis_title=t("dk_axis_y"))
    fig.update_xaxes(range=[x_lo, x_hi])
    fig.update_yaxes(range=[y_hi, y_lo])   # 反转:初请小(增长强)在上面
    return fig


def _desk_growth():
    """增长轴:初请4周均值。返回 (最新值, 已在260k上方的天数)。"""
    s = core.fred_series(C.DESK["growth_series"], start="2000-01-01").dropna()
    if s.empty:
        return None, 0
    warn = C.DESK["growth_warn"]
    last = float(s.iloc[-1])
    days = 0
    if last >= warn:
        below = s[s < warn]
        if len(below):
            days = (s.index[-1] - below.index[-1]).days
        else:
            days = (s.index[-1] - s.index[0]).days
    return last, days


def _desk_rung(row):
    """三个条件有几个就是几档;三个全空 = 基础层,不走阶梯。"""
    n = int(bool(row.get("direction"))) + int(bool(row.get("catalyst"))) + int(bool(row.get("date")))
    if n == 0:
        return None
    return n


def page_desk():
    st.markdown('<div class="eyebrow">DECISION DESK</div>', unsafe_allow_html=True)
    st.markdown(f"## {t('dk_title')}")
    key = core.fred_key()
    if not key:
        st.markdown(f'<div class="note">{t("dk_need_key")}</div>', unsafe_allow_html=True)
        return
    st.caption(t("dk_sub"))

    D = C.DESK
    today = dt.date.today()

    # ══ ① 横向 ══
    st.markdown(f"### {t('dk_h_title')}")
    infl_v, infl_n = _desk_infl()
    gro_v, gro_days = _desk_growth()

    # 两个轴现在是同一种口径:数字 + 分界线。方向不再决定格子,由轨迹去表达。
    infl_s = _desk_infl_monthly()
    gro_s = _desk_growth_monthly()
    hist = _desk_cell_history(infl_s, gro_s)

    if not hist.empty:
        infl_v = float(hist["infl"].iloc[-1])
        gro_v = float(hist["gro"].iloc[-1])

    if infl_v is None:
        infl_state, infl_col = t("dk_mid"), T["muted"]
    elif infl_v < D["infl_calm"]:
        infl_state, infl_col = t("dk_infl_fall"), T["up"]
    else:
        infl_state, infl_col = t("dk_infl_persist"), T["down"]

    if gro_v is None:
        gro_state, gro_col = t("dk_mid"), T["muted"]
    elif gro_v < D["growth_calm"]:
        gro_state, gro_col = t("dk_growth_hold"), T["up"]
    else:
        gro_state, gro_col = t("dk_growth_weak"), T["down"]

    core.cards_row([
        (t("dk_axis_infl"), f"{infl_v:.1f}%" if infl_v is not None else "—", infl_state, infl_col),
        (t("dk_axis_growth"), f"{gro_v:,.0f}" if gro_v is not None else "—", gro_state, gro_col),
    ])
    if infl_v is not None:
        st.caption(t("dk_infl_detail", v=f"{infl_v:.1f}",
                     calm=f"{D['infl_calm']:.1f}", warn=f"{D['infl_warn']:.1f}"))
    if gro_v is not None:
        st.caption(t("dk_growth_detail", v=f"{gro_v:,.0f}",
                     calm=f"{D['growth_calm']:,}", warn=f"{D['growth_warn']:,}"))

    cell = hist["cell"].iloc[-1] if not hist.empty else None
    if cell is None:
        box, box_col = t("dk_box_trans"), T["muted"]
    else:
        box = t(cell)
        box_col = {"dk_box1": T["up"], "dk_box2": T["gold"],
                   "dk_box3": T["accent"], "dk_box4": T["down"]}[cell]
    st.markdown(f'{t("dk_box_now")}<span class="pill" style="background:{box_col};'
                f'color:#0a0d17">{box}</span>', unsafe_allow_html=True)

    # 换格之后要连续几个月才算确认,免得被单月数据带着跑
    held = _desk_held_months(hist)
    if cell is not None:
        if held >= D["infl_months"]:
            st.caption(t("dk_held", n=held))
        else:
            st.caption(t("dk_pending", n=D["infl_months"] - held))

    # ══ 四象限图 ══
    if len(hist) >= 3:
        st.markdown(f"#### {t('dk_grid_title')}")
        st.plotly_chart(_desk_grid_fig(hist, D["traj_months"]), use_container_width=True)
        st.caption(t("dk_traj_note", n=min(D["traj_months"], len(hist))))

    st.markdown(f'<div class="note" style="margin-top:8px">{t("dk_my_view")}</div>',
                unsafe_allow_html=True)

    st.divider()

    # ══ ② 纵向 ══
    st.markdown(f"### {t('dk_v_title')}")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**{t('dk_v_to3')}**")
        if gro_v is not None:
            st.caption(t("dk_v_gap_claims", v=f"{abs(D['growth_calm'] - gro_v):,.0f}"))
    with c2:
        st.markdown(f"**{t('dk_v_to1')}**")
        if infl_v is not None:
            st.caption(t("dk_v_gap_infl", v=f"{abs(infl_v - D['infl_calm']):.1f}"))

    future = [dt.date.fromisoformat(d) for d in D["review_dates"]
              if dt.date.fromisoformat(d) >= today]
    next_rev = min(future) if future else None
    if next_rev:
        st.info(t("dk_v_next", date=next_rev, n=(next_rev - today).days))
    else:
        st.warning(t("dk_v_none"))

    st.divider()

    # ══ 触发清单 ══
    st.markdown(f"### {t('dk_t_title')}")
    st.caption(t("dk_t_sub"))

    fired = False
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**{t('dk_t_named')}**")
        for i, (zh, en) in enumerate(D["triggers"]):
            if st.checkbox(en if lang() == "en" else zh, key=f"dk_trig_{i}"):
                fired = True
    with c2:
        st.markdown(f"**{t('dk_t_fallback')}**")
        st.caption(t("dk_t_fb_intro"))
        fb = []
        for i, (zh, en) in enumerate(D["fallback"]):
            fb.append(st.checkbox(en if lang() == "en" else zh, key=f"dk_fb_{i}"))
        if all(fb):
            st.caption(t("dk_t_fb_write"))
            why = st.text_area("fallback_why", key="dk_fb_why", height=110,
                               placeholder=t("dk_t_fb_ph"), label_visibility="collapsed")
            # 先写判断,再看价格 —— 顺序反过来写的就是对价格的合理化
            if len((why or "").strip()) >= 40:
                fired = True

    with st.expander(t("dk_t_non")):
        for zh, en in D["non_triggers"]:
            st.markdown(f"✗ {en if lang() == 'en' else zh}")
        st.caption(t("dk_t_non_note"))

    st.divider()

    # ══ ③ 门槛 ══
    st.markdown(f"### {t('dk_g_title')}")
    unlocked = fired or (today.isoformat() in D["review_dates"])

    if "dk_ideas" not in st.session_state:
        st.session_state["dk_ideas"] = [dict(x) for x in D["default_ideas"]]

    up = st.file_uploader(t("dk_upload"), type="json", key="dk_up")
    if up is not None:
        try:
            loaded = json.loads(up.getvalue().decode("utf-8"))
            st.session_state["dk_ideas"] = loaded["ideas"]
            st.success(t("dk_upload_ok"))
        except Exception:
            st.error(t("dk_upload_fail"))

    df = pd.DataFrame(st.session_state["dk_ideas"])
    edited = st.data_editor(
        df, num_rows="dynamic" if unlocked else "fixed",
        disabled=not unlocked, hide_index=True, use_container_width=True,
        column_config={
            "idea": st.column_config.TextColumn(t("dk_col_idea"), width="large"),
            "direction": st.column_config.CheckboxColumn(t("dk_col_dir")),
            "catalyst": st.column_config.CheckboxColumn(t("dk_col_cat")),
            "date": st.column_config.CheckboxColumn(t("dk_col_date")),
        }, key="dk_editor")
    if unlocked:
        st.session_state["dk_ideas"] = edited.fillna(False).to_dict("records")

    st.markdown(t("dk_unlocked") if unlocked else t("dk_locked"))

    # 档位 → 动作
    ACT = {None: ("dk_act_base", T["accent"]), 1: ("dk_act_1", T["muted"]),
           2: ("dk_act_2", T["gold"]), 3: ("dk_act_3", T["up"])}
    rows = []
    for r in edited.fillna(False).to_dict("records"):
        rung = _desk_rung(r)
        akey, _ = ACT.get(rung, ("dk_act_0", T["muted"]))
        rows.append({
            t("dk_col_idea"): r.get("idea", ""),
            t("dk_col_rung"): t("dk_act_base").split("·")[0].strip() if rung is None else f"{rung}",
            t("dk_col_action"): t(akey),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.markdown(f'<div class="note">{t("dk_gate_note")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="note" style="margin-top:8px">{t("dk_base_note")}</div>',
                unsafe_allow_html=True)

    st.divider()

    # ══ 存档 ══
    st.markdown(f"### {t('dk_save_title')}")
    st.caption(t("dk_save_note"))
    blob = json.dumps({"saved": today.isoformat(), "box": box,
                       "ideas": st.session_state["dk_ideas"]},
                      ensure_ascii=False, indent=2)
    c1, c2 = st.columns([1, 1])
    with c1:
        st.download_button(t("dk_download"), blob.encode("utf-8"),
                           file_name=f"decision_desk_{today:%Y%m%d}.json",
                           mime="application/json")
    with c2:
        if st.button(t("dk_reset")):
            st.session_state["dk_ideas"] = [dict(x) for x in D["default_ideas"]]
            st.rerun()


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
# 页面:曲线历史(1976 至今 + NBER 衰退阴影)
# 数据自己取(要 1976 年起的长历史),画图沿用本文件的深色主题。
# ════════════════════════════════════════════════════════════════════════════
def _ch_curve_fig(series_map: dict, recessions, height=380):
    """series_map: {显示名: Series(单位 %)}。纵轴统一换算成 bps。"""
    fig = go.Figure()
    colors = [T["accent"], T["gold"], T["up"], T["down"]]
    for i, (label, s) in enumerate(series_map.items()):
        if s is None or s.empty:
            continue
        fig.add_trace(go.Scatter(
            x=s.index, y=s.values * 100, name=label, mode="lines",
            line=dict(width=1.6, color=colors[i % len(colors)]),
            hovertemplate="%{x|%Y-%m-%d} · %{y:.0f} bps<extra>" + label + "</extra>"))
    # 衰退阴影:画在最底层
    for start, end in recessions:
        fig.add_vrect(x0=start, x1=end, fillcolor=T["muted"], opacity=0.16,
                      line_width=0, layer="below")
    fig = style_fig(fig, height)
    fig.add_hline(y=0, line=dict(color=T["txt"], width=1, dash="dash"))
    fig.update_layout(yaxis_title="bps")
    return fig


def page_curve_history():
    st.markdown('<div class="eyebrow">CURVE HISTORY</div>', unsafe_allow_html=True)
    st.markdown(f"## {t('ch_title')}")
    key = core.fred_key()
    if not key:
        st.markdown(f'<div class="note">{t("ch_need_key")}</div>', unsafe_allow_html=True)
        return
    st.caption(t("ch_sub"))

    try:
        s_2s10s = core.fred_series("T10Y2Y", start="1976-01-01")
        s_3m10s = core.fred_series("T10Y3M", start="1976-01-01")
        s_2y = core.fred_series("DGS2", start="1976-01-01")
        s_10y = core.fred_series("DGS10", start="1976-01-01")
        recessions = core.fred_recessions()
    except Exception:
        st.markdown(f'<div class="note">{t("fetch_fail", names="FRED")}</div>', unsafe_allow_html=True)
        return

    if s_2s10s.empty:
        st.markdown(f'<div class="note">{t("fetch_fail", names="T10Y2Y")}</div>', unsafe_allow_html=True)
        return

    # ── 卡片 ──
    def _last(s):
        s = s.dropna()
        return float(s.iloc[-1]) if not s.empty else None

    v_sp, v_3m, v_2y, v_10y = _last(s_2s10s), _last(s_3m10s), _last(s_2y), _last(s_10y)
    d_last = s_2s10s.dropna().index[-1]

    prev = s_2s10s[s_2s10s.index <= d_last - pd.Timedelta(days=30)].dropna()
    delta = f"{(v_sp - float(prev.iloc[-1])) * 100:+.0f} bps · {t('ch_vs_1m')}" if len(prev) else None

    sp_bp = v_sp * 100
    color = T["down"] if sp_bp < 0 else (T["gold"] if sp_bp < 30 else T["up"])
    state = t("ch_state_inv") if sp_bp < 0 else (t("ch_state_flat") if sp_bp < 30 else t("ch_state_norm"))

    items = [(t("ch_2s10s"), f"{sp_bp:+.0f} bps", delta, color)]
    if v_3m is not None:
        items.append((t("ch_3m10s"), f"{v_3m * 100:+.0f} bps", None,
                      T["down"] if v_3m < 0 else T["up"]))
    if v_2y is not None:
        items.append((t("ch_2y"), f"{v_2y:.3f}%", None, T["muted"]))
    if v_10y is not None:
        items.append((t("ch_10y"), f"{v_10y:.3f}%", None, T["muted"]))
    core.cards_row(items)

    st.markdown(f'<span class="pill" style="background:{color};color:#0a0d17">{state}</span>',
                unsafe_allow_html=True)
    st.caption(t("ch_latest", date=d_last.date()))

    st.divider()

    # ── 主图:1976 至今 ──
    st.markdown(f"#### {t('ch_chart_long')}")
    st.plotly_chart(_ch_curve_fig({t("ch_2s10s"): s_2s10s, t("ch_3m10s"): s_3m10s},
                                  recessions, 400),
                    use_container_width=True)

    # ── 放大图:最近 5 年 ──
    cut = pd.Timestamp.today() - pd.DateOffset(years=5)
    st.markdown(f"#### {t('ch_chart_zoom')}")
    st.plotly_chart(_ch_curve_fig({t("ch_2s10s"): s_2s10s[s_2s10s.index >= cut],
                                   t("ch_3m10s"): s_3m10s[s_3m10s.index >= cut]},
                                  [(a, b) for a, b in recessions if b >= cut], 320),
                    use_container_width=True)

    # ── 趋势:最近1年 + 20日均线 ──
    st.markdown(f"#### {t('ch_trend_title')}")
    cut1y = pd.Timestamp.today() - pd.DateOffset(years=1)
    raw = s_2s10s.dropna()
    ma = raw.rolling(20).mean()
    raw_1y, ma_1y = raw[raw.index >= cut1y], ma[ma.index >= cut1y].dropna()

    if len(ma_1y) > 25:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=raw_1y.index, y=raw_1y.values * 100, name=t("ch_trend_raw"),
            mode="lines", line=dict(width=1, color=T["muted"]),
            hovertemplate="%{x|%Y-%m-%d} · %{y:.0f} bps<extra></extra>"))
        fig.add_trace(go.Scatter(
            x=ma_1y.index, y=ma_1y.values * 100, name=t("ch_trend_ma"),
            mode="lines", line=dict(width=3, color=T["gold"]),
            hovertemplate="%{x|%Y-%m-%d} · %{y:.0f} bps<extra></extra>"))
        fig = style_fig(fig, 320)
        fig.add_hline(y=0, line=dict(color=T["txt"], width=1, dash="dash"))
        fig.update_layout(yaxis_title="bps")
        st.plotly_chart(fig, use_container_width=True)

        # 一句话结论:均线一个月的方向(20 个交易日)
        now_bp = float(ma_1y.iloc[-1]) * 100
        then_bp = float(ma_1y.iloc[-21]) * 100 if len(ma_1y) > 21 else float(ma_1y.iloc[0]) * 100
        chg = now_bp - then_bp
        if chg < -5:
            word, col = t("ch_trend_down"), T["down"]
        elif chg > 5:
            word, col = t("ch_trend_up"), T["up"]
        else:
            word, col = t("ch_trend_flat"), T["muted"]
        st.markdown(f'{t("ch_trend_verdict")}<span class="pill" style="background:{col};'
                    f'color:#0a0d17">{word}</span>', unsafe_allow_html=True)
        st.caption(t("ch_trend_detail", now=f"{now_bp:+.0f}",
                     then=f"{then_bp:+.0f}", chg=f"{chg:+.0f}"))
        st.markdown(f'<div class="note">{t("ch_trend_note")}</div>', unsafe_allow_html=True)

    st.divider()

    # ── 水平收益率 ──
    st.markdown(f"#### {t('ch_levels')}")
    fig = go.Figure()
    for label, s, col in [(t("ch_2y"), s_2y, T["down"]), (t("ch_10y"), s_10y, T["accent"])]:
        s = s[s.index >= cut].dropna()
        if s.empty:
            continue
        fig.add_trace(go.Scatter(x=s.index, y=s, name=label, mode="lines",
                                 line=dict(width=1.8, color=col),
                                 hovertemplate="%{x|%Y-%m-%d} · %{y:.2f}%<extra>" + label + "</extra>"))
    fig = style_fig(fig, 300)
    fig.update_layout(yaxis_title="%")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f'<div class="note">{t("ch_note")}</div>', unsafe_allow_html=True)

    out = pd.DataFrame({"T10Y2Y": s_2s10s, "T10Y3M": s_3m10s,
                        "DGS2": s_2y, "DGS10": s_10y}).dropna(how="all")
    st.download_button(t("ch_download"), out.to_csv().encode("utf-8"),
                       file_name=f"yield_curve_{dt.date.today():%Y%m%d}.csv", mime="text/csv")


# ════════════════════════════════════════════════════════════════════════════
# 页面:劳动力市场(初请失业金 4 周均值)
# 为什么是这一条:行政数据、周频、几乎不修正。每周四 08:30 美东发布。
# ════════════════════════════════════════════════════════════════════════════
def page_labor():
    st.markdown('<div class="eyebrow">LABOR MARKET</div>', unsafe_allow_html=True)
    st.markdown(f"## {t('lb_title')}")
    key = core.fred_key()
    if not key:
        st.markdown(f'<div class="note">{t("lb_need_key")}</div>', unsafe_allow_html=True)
        return
    st.caption(t("lb_sub"))

    L = C.LABOR
    try:
        s4 = core.fred_series(L["claims_4wk"], start="1970-01-01").dropna()
        s1 = core.fred_series(L["claims_raw"], start="1970-01-01").dropna()
        recessions = core.fred_recessions(start="1970-01-01")
    except Exception:
        st.markdown(f'<div class="note">{t("fetch_fail", names="FRED")}</div>', unsafe_allow_html=True)
        return

    if s4.empty:
        st.markdown(f'<div class="note">{t("fetch_fail", names=L["claims_4wk"])}</div>',
                    unsafe_allow_html=True)
        return

    def _k(v):
        return f"{v / 1000:,.0f}k"

    now = float(s4.iloc[-1])
    d_last = s4.index[-1]

    def _asof(days):
        w = s4[s4.index <= d_last - pd.Timedelta(days=days)]
        return float(w.iloc[-1]) if len(w) else None

    m1, y1 = _asof(30), _asof(365)

    # 状态:裂缝 / 留意 / 平静
    if now >= L["warn"]:
        state, color = t("lb_state_warn"), T["down"]
    elif now >= L["calm"]:
        state, color = t("lb_state_watch"), T["gold"]
    else:
        state, color = t("lb_state_calm"), T["up"]

    items = [(t("lb_card_4wk"), _k(now), state, color)]
    if not s1.empty:
        items.append((t("lb_card_raw"), _k(float(s1.iloc[-1])), None, T["muted"]))
    if m1 is not None:
        items.append((t("lb_card_1m"), _k(m1), f"{(now - m1) / 1000:+,.0f}k", T["muted"]))
    if y1 is not None:
        items.append((t("lb_card_1y"), _k(y1), f"{(now - y1) / 1000:+,.0f}k", T["muted"]))
    core.cards_row(items)

    st.markdown(f'<span class="pill" style="background:{color};color:#0a0d17">{state}</span>',
                unsafe_allow_html=True)
    st.caption(t("lb_latest", date=d_last.date()))

    st.divider()

    # ── 主图 ──
    cut = pd.Timestamp.today() - pd.DateOffset(years=L["years"])
    a4, a1 = s4[s4.index >= cut], s1[s1.index >= cut]
    st.markdown(f"#### {t('lb_chart', n=L['years'])}")
    fig = go.Figure()
    if not a1.empty:
        fig.add_trace(go.Scatter(x=a1.index, y=a1.values, name=t("lb_line_raw"),
                                 mode="lines", line=dict(width=1, color=T["muted"]),
                                 hovertemplate="%{x|%Y-%m-%d} · %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=a4.index, y=a4.values, name=t("lb_line_4wk"),
                             mode="lines", line=dict(width=3, color=T["gold"]),
                             hovertemplate="%{x|%Y-%m-%d} · %{y:,.0f}<extra></extra>"))
    for start, end in recessions:
        if end >= cut:
            fig.add_vrect(x0=max(start, cut), x1=end, fillcolor=T["muted"],
                          opacity=0.16, line_width=0, layer="below")
    fig = style_fig(fig, 380)
    fig.add_hline(y=L["warn"], line=dict(color=T["down"], width=1, dash="dot"),
                  annotation_text=t("lb_warn_line", v=int(L["warn"] / 1000)),
                  annotation_position="top left",
                  annotation_font=dict(color=T["down"], size=10))
    fig.add_hline(y=L["calm"], line=dict(color=T["up"], width=1, dash="dot"),
                  annotation_text=t("lb_calm_line", v=int(L["calm"] / 1000)),
                  annotation_position="bottom left",
                  annotation_font=dict(color=T["up"], size=10))
    # 2020 年那个 600 万的尖峰会把近年的变化压成一条平线,所以纵轴截断
    ymax = float(a4.max()) * 1.35
    fig.update_layout(yaxis_title="", yaxis=dict(range=[0, min(ymax, 700_000)],
                                                 gridcolor=T["line"], zeroline=False))
    st.plotly_chart(fig, use_container_width=True)

    # ── 一句话结论 ──
    if m1 is not None:
        chg = now - m1
        if chg > 5_000:
            word, col = t("lb_up"), T["down"]
        elif chg < -5_000:
            word, col = t("lb_down"), T["up"]
        else:
            word, col = t("lb_flat"), T["muted"]
        st.markdown(f'{t("lb_verdict")}<span class="pill" style="background:{col};'
                    f'color:#0a0d17">{word}</span>', unsafe_allow_html=True)
        st.caption(t("lb_detail", now=_k(now), then=_k(m1), chg=f"{chg / 1000:+,.0f}k"))

    st.markdown(f'<div class="note">{t("lb_note", warn=int(L["warn"] / 1000))}</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="note" style="margin-top:10px">{t("lb_note2")}</div>',
                unsafe_allow_html=True)

    out = pd.DataFrame({L["claims_4wk"]: s4, L["claims_raw"]: s1}).dropna(how="all")
    st.download_button(t("lb_download"), out.to_csv().encode("utf-8"),
                       file_name=f"jobless_claims_{dt.date.today():%Y%m%d}.csv", mime="text/csv")


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
    "desk": page_desk,
    "overview": page_overview, "rates": page_rates, "curve_hist": page_curve_history,
    "labor": page_labor, "ust": page_ust, "sentiment": page_sentiment,
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
