"""
config.py —— 全局配置中心
══════════════════════════════════════════════════════════════════════════════
想加资产 / 加事件 / 加页面 / 改阈值,基本都只改这个文件。
Phase 2(持仓)、Phase 3(新闻简报)以后也在这里登记。
"""

# ── 密码门 ───────────────────────────────────────────────────────────────────
# 部署时在 Streamlit Secrets 写 APP_PASSWORD = "你的密码";没设则用下面这个默认值。
DEFAULT_PASSWORD = "gold2026"

# ── 资产(yfinance 代码)────────────────────────────────────────────────────
# 加一个资产 = 加一行。is_yield=True 表示这是收益率(用 bps 变动而非 % 变动)。
ASSETS = {
    "gold":   {"name": "黄金 COMEX",  "ticker": "GC=F",     "grp": "金属", "fmt": "{:,.1f}"},
    "silver": {"name": "白银 COMEX",  "ticker": "SI=F",     "grp": "金属", "fmt": "{:,.2f}"},
    "copper": {"name": "铜 COMEX",    "ticker": "HG=F",     "grp": "金属", "fmt": "{:,.3f}"},
    "wti":    {"name": "WTI 原油",    "ticker": "CL=F",     "grp": "能源", "fmt": "{:,.2f}"},
    "dxy":    {"name": "美元指数",     "ticker": "DX-Y.NYB", "grp": "外汇", "fmt": "{:,.2f}"},
    "usdjpy": {"name": "美元/日元",   "ticker": "JPY=X",    "grp": "外汇", "fmt": "{:,.2f}"},
    "usdcny": {"name": "美元/人民币", "ticker": "CNY=X",    "grp": "外汇", "fmt": "{:,.3f}"},
    "spx":    {"name": "标普500",     "ticker": "^GSPC",    "grp": "股票", "fmt": "{:,.0f}"},
    "vix":    {"name": "VIX 恐慌",    "ticker": "^VIX",     "grp": "波动率", "fmt": "{:,.2f}"},
    "ust10":  {"name": "美债10年收益率", "ticker": "^TNX", "fred": "DGS10", "grp": "利率", "fmt": "{:,.2f}", "is_yield": True},
}

# 事件研究默认观察的资产(可在界面里改)
DEFAULT_REACTION_ASSETS = ["gold", "dxy", "spx", "ust10", "usdjpy"]

# ── 国债收益率曲线(FRED 序列)───────────────────────────────────────────────
TREASURY = {
    "3M":  "DGS3MO", "2Y": "DGS2", "5Y": "DGS5", "10Y": "DGS10", "30Y": "DGS30",
}
REAL_YIELD_10Y = "DFII10"  # 10年期实际收益率(TIPS)——黄金头号变量,单列

# ── CPI 分项(FRED 序列,按月,自动算同比)──────────────────────────────────
CPI_COMPONENTS = {
    "整体 CPI":   "CPIAUCSL",
    "核心 CPI":   "CPILFESL",
    "能源":       "CPIENGSL",
    "食品":       "CPIUFDSL",
    "住房(shelter)": "CUSR0000SAH1",
}

# ── 事件定义 ─────────────────────────────────────────────────────────────────
# source: manual=用下面写死的 dates;fred_release=用FRED发布日历;fred_change=FRED中利率变动日
EVENTS = {
    "FOMC": {
        "label": "美联储 FOMC 决议", "source": "manual",
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
        "label": "美联储实际变动利率", "source": "fred_change", "series": "DFEDTARU",
    },
    "BOJ_HIKE": {
        "label": "日本央行加息", "source": "manual",
        "dates": ["2024-03-19", "2024-07-31", "2025-01-24", "2025-12-19"],
    },
    "CPI": {
        "label": "美国 CPI 公布", "source": "fred_release", "release_id": 10,
    },
    "NFP": {
        "label": "美国非农就业", "source": "fred_release", "release_id": 50,
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
PAGES = [
    ("市场总览",        "overview",  True),
    ("利率与曲线",      "rates",     True),
    ("情绪 / 风险",     "sentiment", True),
    ("宏观日历 & 事件研究", "events", True),
    ("CPI 详情",        "cpi",       True),
    ("持仓监测 (Phase 2)", "portfolio", False),   # 占位
    ("智能简报 (Phase 3)", "brief",     False),   # 占位
]

# ── 配色(与投资时钟保持一致)──────────────────────────────────────────────
THEME = {
    "ink": "#0a0d17", "panel": "#10141f", "panel2": "#0d111b", "line": "#1e2434",
    "txt": "#e8ecf4", "muted": "#8a93a8", "up": "#34d399", "down": "#f87171",
    "gold": "#e8b84b", "accent": "#38bdf8",
}
