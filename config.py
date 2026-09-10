"""
config.py —— 全局配置中心
══════════════════════════════════════════════════════════════════════════════
想加资产 / 加事件 / 加页面 / 改阈值 / 改中英文文案,基本都只改这个文件。
Phase 2(持仓)、Phase 3(新闻简报)以后也在这里登记。

中 / 英双语说明:
  · 侧栏最上面有 中文 / English 切换;网址后面加 ?lang=en 可以直接打开英文版。
  · 资产:name = 中文,name_en = 英文。事件:label = 中文,label_en = 英文。
  · CPI 分项:name / name_en / fred。页面:PAGES 每行 = (中文名, 英文名, key, 是否启用)。
  · 其余界面文字(标题、提示、表头……)都在本文件最底部的 TEXT 里,zh / en 一一对应。
"""

# ── 密码门 ───────────────────────────────────────────────────────────────────
# 部署时在 Streamlit Secrets 写 APP_PASSWORD = "你的密码";没设则用下面这个默认值。
DEFAULT_PASSWORD = "gold2026"

# ── 语言 ─────────────────────────────────────────────────────────────────────
DEFAULT_LANG = "zh"                       # 默认打开哪种语言("zh" 或 "en")
LANGS = {"zh": "中文", "en": "English"}    # 侧栏切换按钮上显示的文字

# ── 资产(yfinance 代码)────────────────────────────────────────────────────
# 加一个资产 = 加一行(name 中文,name_en 英文)。is_yield=True 表示这是收益率(用 bps 变动而非 % 变动)。
ASSETS = {
    "gold":   {"name": "黄金 COMEX",     "name_en": "Gold (COMEX)",      "ticker": "GC=F",     "grp": "金属",   "fmt": "{:,.1f}"},
    "silver": {"name": "白银 COMEX",     "name_en": "Silver (COMEX)",    "ticker": "SI=F",     "grp": "金属",   "fmt": "{:,.2f}"},
    "copper": {"name": "铜 COMEX",       "name_en": "Copper (COMEX)",    "ticker": "HG=F",     "grp": "金属",   "fmt": "{:,.3f}"},
    "wti":    {"name": "WTI 原油",       "name_en": "WTI Crude",         "ticker": "CL=F",     "grp": "能源",   "fmt": "{:,.2f}"},
    "dxy":    {"name": "美元指数",        "name_en": "US Dollar Index",   "ticker": "DX-Y.NYB", "grp": "外汇",   "fmt": "{:,.2f}"},
    "usdjpy": {"name": "美元/日元",      "name_en": "USD/JPY",           "ticker": "JPY=X",    "grp": "外汇",   "fmt": "{:,.2f}"},
    "usdcny": {"name": "美元/人民币",    "name_en": "USD/CNY",           "ticker": "CNY=X",    "grp": "外汇",   "fmt": "{:,.3f}"},
    "spx":    {"name": "标普500",        "name_en": "S&P 500",           "ticker": "^GSPC",    "grp": "股票",   "fmt": "{:,.0f}"},
    "vix":    {"name": "VIX 恐慌",       "name_en": "VIX",               "ticker": "^VIX",     "grp": "波动率", "fmt": "{:,.2f}"},
    "ust10":  {"name": "美债10年收益率", "name_en": "US 10Y Yield",      "ticker": "^TNX", "fred": "DGS10", "grp": "利率", "fmt": "{:,.2f}", "is_yield": True},
}

# 事件研究默认观察的资产(可在界面里改)
DEFAULT_REACTION_ASSETS = ["gold", "dxy", "spx", "ust10", "usdjpy"]

# ── 国债收益率曲线(FRED 序列)───────────────────────────────────────────────
TREASURY = {
    "3M":  "DGS3MO", "2Y": "DGS2", "5Y": "DGS5", "10Y": "DGS10", "30Y": "DGS30",
}
REAL_YIELD_10Y = "DFII10"  # 10年期实际收益率(TIPS)——黄金头号变量,单列

# ── CPI 分项(FRED 序列,按月,自动算同比)──────────────────────────────────
# 加一个分项 = 加一行:key 随便起个英文名,name 中文,name_en 英文,fred 是 FRED 序列号。
CPI_COMPONENTS = {
    "headline": {"name": "整体 CPI",      "name_en": "Headline CPI", "fred": "CPIAUCSL"},
    "core":     {"name": "核心 CPI",      "name_en": "Core CPI",     "fred": "CPILFESL"},
    "energy":   {"name": "能源",          "name_en": "Energy",       "fred": "CPIENGSL"},
    "food":     {"name": "食品",          "name_en": "Food",         "fred": "CPIUFDSL"},
    "shelter":  {"name": "住房(shelter)", "name_en": "Shelter",      "fred": "CUSR0000SAH1"},
}
CPI_HEADLINE_KEY = "headline"   # 页面底部那张 5 年走势图画的是哪一项

# ── 事件定义 ─────────────────────────────────────────────────────────────────
# source: manual=用下面写死的 dates;fred_release=用FRED发布日历;fred_change=FRED中利率变动日
EVENTS = {
    "FOMC": {
        "label": "美联储 FOMC 决议", "label_en": "FOMC Decision", "source": "manual",
        "dates": [  # 决议日(两天会议的第二天)
            "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31",
            "2024-09-18", "2024-11-07", "2024-12-18",
            "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30",
            "2025-09-17", "2025-10-29", "2025-12-10",
            "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29",
            "2026-09-16", "2026-10-28", "2026-12-09",
        ],
    },
    "FED_CHANGE": {
        "label": "美联储实际变动利率", "label_en": "Fed Rate Change", "source": "fred_change", "series": "DFEDTARU",
    },
    "BOJ_HIKE": {
        "label": "日本央行加息", "label_en": "BoJ Rate Hike", "source": "manual",
        "dates": ["2024-03-19", "2024-07-31", "2025-01-24", "2025-12-19"],
    },
    "CPI": {
        "label": "美国 CPI 公布", "label_en": "US CPI Release", "source": "fred_release", "release_id": 10,
    },
    "NFP": {
        "label": "美国非农就业", "label_en": "US Nonfarm Payrolls", "source": "fred_release", "release_id": 50,
    },
}

# ── 情绪 / 风险 ──────────────────────────────────────────────────────────────
SENTIMENT = {
    "vix_ticker": "^VIX",
    "move_ticker": "^MOVE",            # 债市波动率,取不到会优雅跳过
    "hy_oas_fred": "BAMLH0A0HYM2",     # 高收益债信用利差(真正的"压力"信号)
    # 风险开关阈值
    "vix_calm": 16, "vix_stress": 26,
    "oas_calm": 3.5, "oas_stress": 5.5,
}

# ── 导航(加页面 = 加一行 + 在 app.py 写个 render 函数)──────────────────────
# 每行 = (中文名, 英文名, key, 是否启用)
PAGES = [
    ("市场总览",            "Market Overview",        "overview",  True),
    ("利率与曲线",          "Rates & Curve",          "rates",     True),
    ("情绪 / 风险",         "Sentiment / Risk",       "sentiment", True),
    ("宏观日历 & 事件研究", "Calendar & Event Study", "events",    True),
    ("CPI 详情",            "CPI Detail",             "cpi",       True),
    ("持仓监测 (Phase 2)",  "Portfolio (Phase 2)",    "portfolio", False),   # 占位
    ("智能简报 (Phase 3)",  "Briefing (Phase 3)",     "brief",     False),   # 占位
]

# ── 配色(与投资时钟保持一致)──────────────────────────────────────────────
THEME = {
    "ink": "#0a0d17", "panel": "#10141f", "panel2": "#0d111b", "line": "#1e2434",
    "txt": "#e8ecf4", "muted": "#8a93a8", "up": "#34d399", "down": "#f87171",
    "gold": "#e8b84b", "accent": "#38bdf8",
}

# ── 界面文字(中 / 英)────────────────────────────────────────────────────────
# 改措辞只改这里;zh 和 en 的 key 必须一一对应。带 {xxx} 的是占位符,程序运行时填数。
TEXT = {
    "zh": {
        # 通用 / 侧栏 / 密码门
        "app_title":       "宏观作战室",
        "gate_caption":    "私人工具,请输入访问密码",
        "gate_pw":         "密码",
        "gate_enter":      "进入",
        "gate_wrong":      "密码不对",
        "sidebar_data":    "数据:yfinance(免费)+ FRED(免费key)",
        "fred_status":     "FRED key 状态:",
        "fred_ok":         "✅ 已配置",
        "fred_missing":    "⚠️ 未配置(部分页受限)",
        "refresh":         "🔄 清缓存刷新",
        "footer":          "数据更新 {date} · 仅供研究,不构成投资建议",
        # 市场总览
        "overview_title":  "市场总览",
        "fetch_fail":      "取数失败:{names}(可能是行情源临时不可用或需 FRED key;刷新或稍后再试)。",
        "trend_6m":        "6 个月走势(基准化 = 100)",
        "pick_assets":     "选择对比资产",
        # 利率与曲线
        "rates_title":     "利率与曲线",
        "rates_need_key":  "本页需要免费 FRED key(在 Secrets 设 FRED_API_KEY)。没设的话,市场总览/情绪页仍可用。",
        "real10":          "10Y 实际(TIPS)",
        "gold_driver":     "黄金头号变量",
        "spread_2s10s":    "2s10s 利差",
        "inverted":        "倒挂",
        "normal":          "正常",
        "curve_now":       "当前收益率曲线",
        "nominal_vs_real": "10Y 名义 vs 实际收益率",
        "nominal10":       "10Y 名义",
        "real10_short":    "10Y 实际",
        # 情绪 / 风险
        "sent_title":      "情绪 / 风险",
        "vix_card":        "VIX 股市波动",
        "pct_1y":          "1年分位 {pc}%",
        "move_card":       "MOVE 债市波动",
        "hy_card":         "高收益债利差",
        "credit_signal":   "信用压力信号",
        "risk_on":         "RISK-ON · 风险偏好",
        "risk_off":        "RISK-OFF · 避险",
        "neutral":         "中性 · 观望",
        "risk_switch":     "当前风险开关:",
        "vix_2y":          "VIX 走势(2 年)",
        "oas_need_key":    "信用利差需 FRED key;VIX 不需要。",
        # 宏观日历 & 事件研究
        "events_title":    "宏观日历 & 事件研究",
        "upcoming":        "📅 即将到来",
        "col_event":       "事件",
        "col_next":        "下次日期",
        "col_days":        "剩余天数",
        "no_upcoming":     "暂无即将到来的事件(CPI/非农需 FRED key 才能取发布日历)。",
        "study_title":     "🔬 事件研究:历史上这类事件,你的资产怎么反应?",
        "event_type":      "事件类型",
        "watch_assets":    "观察资产",
        "post_days":       "事件后天数",
        "pick_one":        "选至少一个资产",
        "no_dates":        "该事件暂无可用历史日期(CPI/非农需 FRED key)。",
        "sample":          "样本:{label} · 共 {n} 次(2024 年至今)",
        "not_enough":      "窗口内数据不足,换个事件或缩短天数试试。",
        "x_rel":           "相对事件日(交易日)",
        "y_note":          "纵轴 = 基准化到事件日(T0)=100 的平均路径。",
        "col_asset":       "资产",
        "col_t1":          "T+1 均值({unit})",
        "col_t1_win":      "T+1 上涨概率",
        "col_t5":          "T+5 均值({unit})",
        "col_t10":         "T+10 均值({unit})",
        "study_note":      "价格类资产为百分比变动,收益率类(美债)为 bps 变动。历史规律不代表未来,仅供研判参考,不构成投资建议。",
        # CPI
        "cpi_title":       "CPI 详情(美国)",
        "cpi_need_key":    "本页需要 FRED key。",
        "yoy":             " 同比",
        "cpi_chart":       "整体 CPI 同比(近 5 年)",
        "cpi_note":        "同比由 FRED 月度指数计算(季调口径,展示用)。想看更细分项,在 config.py 的 CPI_COMPONENTS 里加 FRED 序列即可。",
        # 占位页
        "portfolio_title": "持仓监测 (Phase 2)",
        "portfolio_desc":  "下一步:你选好组合,这里盯实时盈亏、相关性、与宏观事件的暴露。架构已留好接口。",
        "brief_title":     "智能简报 (Phase 3)",
        "brief_desc":      "再下一步:接 Claude API,自动筛 MU/HBM 等催化剂新闻,每天生成结合你仓位的简报。",
    },
    "en": {
        # General / sidebar / password gate
        "app_title":       "Macro War Room",
        "gate_caption":    "Private tool — please enter the access password",
        "gate_pw":         "Password",
        "gate_enter":      "Enter",
        "gate_wrong":      "Wrong password",
        "sidebar_data":    "Data: yfinance (free) + FRED (free key)",
        "fred_status":     "FRED key: ",
        "fred_ok":         "✅ configured",
        "fred_missing":    "⚠️ not set (some pages limited)",
        "refresh":         "🔄 Clear cache & refresh",
        "footer":          "Data as of {date} · For research only — not investment advice",
        # Market overview
        "overview_title":  "Market Overview",
        "fetch_fail":      "Could not load: {names} (the data source may be temporarily down or needs a FRED key — refresh or try again later).",
        "trend_6m":        "6-Month Trend (rebased to 100)",
        "pick_assets":     "Select assets to compare",
        # Rates & curve
        "rates_title":     "Rates & Yield Curve",
        "rates_need_key":  "This page needs a free FRED key (set FRED_API_KEY in Secrets). Without it, Market Overview and Sentiment still work.",
        "real10":          "10Y Real (TIPS)",
        "gold_driver":     "No.1 driver for gold",
        "spread_2s10s":    "2s10s Spread",
        "inverted":        "Inverted",
        "normal":          "Normal",
        "curve_now":       "Current Yield Curve",
        "nominal_vs_real": "10Y Nominal vs Real Yield",
        "nominal10":       "10Y Nominal",
        "real10_short":    "10Y Real",
        # Sentiment / risk
        "sent_title":      "Sentiment / Risk",
        "vix_card":        "VIX (Equity Vol)",
        "pct_1y":          "1Y percentile {pc}%",
        "move_card":       "MOVE (Bond Vol)",
        "hy_card":         "HY Credit Spread",
        "credit_signal":   "Credit stress signal",
        "risk_on":         "RISK-ON · Risk appetite",
        "risk_off":        "RISK-OFF · Defensive",
        "neutral":         "NEUTRAL · Wait and see",
        "risk_switch":     "Current risk switch: ",
        "vix_2y":          "VIX (2 years)",
        "oas_need_key":    "Credit spread needs a FRED key; VIX does not.",
        # Calendar & event study
        "events_title":    "Macro Calendar & Event Study",
        "upcoming":        "📅 Upcoming",
        "col_event":       "Event",
        "col_next":        "Next date",
        "col_days":        "Days left",
        "no_upcoming":     "No upcoming events (the CPI / NFP release calendar needs a FRED key).",
        "study_title":     "🔬 Event Study: how did your assets react to this kind of event in the past?",
        "event_type":      "Event type",
        "watch_assets":    "Assets to watch",
        "post_days":       "Days after event",
        "pick_one":        "Pick at least one asset",
        "no_dates":        "No historical dates for this event yet (CPI / NFP need a FRED key).",
        "sample":          "Sample: {label} · {n} events (2024 to date)",
        "not_enough":      "Not enough data in the window — try another event or fewer days.",
        "x_rel":           "Days relative to event (trading days)",
        "y_note":          "Y-axis = average path rebased to event day (T0) = 100.",
        "col_asset":       "Asset",
        "col_t1":          "T+1 avg ({unit})",
        "col_t1_win":      "T+1 up probability",
        "col_t5":          "T+5 avg ({unit})",
        "col_t10":         "T+10 avg ({unit})",
        "study_note":      "Price assets are shown in % change; yield assets (Treasuries) in bps. Past patterns do not guarantee the future — for reference only, not investment advice.",
        # CPI
        "cpi_title":       "CPI Detail (US)",
        "cpi_need_key":    "This page needs a FRED key.",
        "yoy":             " YoY",
        "cpi_chart":       "Headline CPI YoY (last 5 years)",
        "cpi_note":        "YoY is computed from the FRED monthly index (seasonally adjusted, for display). To add sub-components, add FRED series to CPI_COMPONENTS in config.py.",
        # Placeholder pages
        "portfolio_title": "Portfolio Monitor (Phase 2)",
        "portfolio_desc":  "Next step: once you pick a portfolio, this page will track live P&L, correlations and exposure to macro events. The hooks are already in place.",
        "brief_title":     "Smart Briefing (Phase 3)",
        "brief_desc":      "Later: connect the Claude API to screen catalyst news (e.g. MU / HBM) and generate a daily briefing tied to your positions.",
    },
}
