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
    # 下面四个只有 FRED 有,yfinance 没有对应代码,所以 ticker 留空(取不到会优雅跳过)
    "ust2":   {"name": "美债2年收益率",  "name_en": "US 2Y Yield",       "ticker": "", "fred": "DGS2",   "grp": "利率", "fmt": "{:,.2f}", "is_yield": True},
    "ust10r": {"name": "10Y 实际收益率", "name_en": "10Y Real Yield",    "ticker": "", "fred": "DFII10", "grp": "利率", "fmt": "{:,.2f}", "is_yield": True},
    "be10":   {"name": "10Y 盈亏平衡",   "name_en": "10Y Breakeven",     "ticker": "", "fred": "T10YIE", "grp": "通胀", "fmt": "{:,.2f}", "is_yield": True},
    "hyoas":  {"name": "高收益债利差",   "name_en": "HY Credit Spread",  "ticker": "", "fred": "BAMLH0A0HYM2", "grp": "信用", "fmt": "{:,.2f}", "is_yield": True},
}

# ── 市场总览的排布 ───────────────────────────────────────────────────────────
# 按宏观功能分组,而不是平铺一排:四象限(增长 × 通胀)的位置一眼能读出来。
# 想加回白银/日元/人民币,把 code 填进对应的组就行。
OVERVIEW_GROUPS = [
    ("ov_grp_policy", ["ust2", "ust10", "ust10r"]),   # 政策与利率
    ("ov_grp_growth", ["spx", "copper", "hyoas"]),    # 增长轴
    ("ov_grp_infl",   ["wti", "be10"]),               # 通胀轴
    ("ov_grp_usd",    ["dxy", "gold", "vix"]),        # 美元与避险
]
# 收益率画原始 %(不做基准化——4.5%→4.97% 基准化后是 +10%,视觉上会被严重放大)
OVERVIEW_YIELD_CHART = ["ust10", "ust2", "ust10r"]
# 价格类才做基准化 = 100
OVERVIEW_PRICE_CHART = ["gold", "wti", "dxy", "spx"]
OVERVIEW_WINDOWS = {"3个月": 90, "6个月": 180, "1年": 365}
OVERVIEW_WINDOWS_EN = {"3 Months": 90, "6 Months": 180, "1 Year": 365}
OVERVIEW_DEFAULT_WINDOW = "6个月"

# 事件研究默认观察的资产(可在界面里改)
DEFAULT_REACTION_ASSETS = ["gold", "dxy", "spx", "ust10", "usdjpy"]

# ── 国债收益率曲线(FRED 序列)───────────────────────────────────────────────
TREASURY = {
    "3M":  "DGS3MO", "2Y": "DGS2", "5Y": "DGS5", "10Y": "DGS10", "30Y": "DGS30",
}
REAL_YIELD_10Y = "DFII10"  # 10年期实际收益率(TIPS)——黄金头号变量,单列

# ── 美债实验室(新增页面 "ust")─────────────────────────────────────────────
# 对应《美债研究手册》五层框架的前四层。想换序列只改这里,app.py 不用动。
UST = {
    # 第一层 · 第一刀:名义 = 实际 + 通胀补偿
    "nominal_10y":     "DGS10",       # 10年名义
    "real_10y":        "DFII10",      # 10年实际(TIPS)
    "breakeven_10y":   "T10YIE",      # 10年盈亏平衡通胀
    "breakeven_5y5y":  "T5YIFR",      # 5年后的5年远期盈亏平衡(看长期通胀中枢有没有脱锚)
    # 第一层 · 第二刀:名义 = 预期短端路径 + 期限溢价
    # 注意口径:期限溢价是针对"零息债"算的,所以要配同一个模型的零息拟合收益率来减,
    # 不能拿 DGS10(附息、半年付息、投资基准报价)去减,那样 A 会带一个系统性偏差。
    "fitted_zero_10y":  "THREEFY10",    # Kim-Wright 10年零息拟合收益率
    "term_premium_10y": "THREEFYTP10",  # 同一模型的期限溢价(估计值,会回溯修正)
    # 第二层 · 曲线
    "nominal_2y":      "DGS2",
    "nominal_3m":      "DGS3MO",
    "spread_2s10s":    "T10Y2Y",
    "spread_3m10s":    "T10Y3M",
    # 第四层 · 定价检验
    "move_ticker":     "^MOVE",       # 债市波动率,取不到会优雅跳过
}

# 归因 / 形态判定的回看窗口(交易日)
UST_WINDOWS = {"1个月": 21, "3个月": 63, "6个月": 126, "1年": 252}
UST_WINDOWS_EN = {"1 Month": 21, "3 Months": 63, "6 Months": 126, "1 Year": 252}
UST_DEFAULT_WINDOW = "3个月"

# 曲线形态:水平变动和利差变动都小于这个幅度(bps),就判为"横盘",不硬套四象限
UST_REGIME_MIN_BP = 5.0
# 归因:主导通道的判定门槛——某一通道贡献占比超过这个值才叫"主导"
UST_DOMINANT_SHARE = 0.60

# ── 拍卖监测(TreasuryDirect 公开接口,不需要 key)──────────────────────────
AUCTION_API = "https://www.treasurydirect.gov/TA_WS/securities/auctioned"
AUCTION_TYPES = ["Note", "Bond"]          # 先只看付息债;要加短债就加 "Bill"
AUCTION_LOOKBACK_DAYS = 500               # 往回取多久(要够算基准均值)
AUCTION_BASELINE_N = 6                    # bid-to-cover 跟同期限过去几次比
AUCTION_SHOW_N = 12                       # 表格里显示最近几场
# 一级交易商承接率高于这个值标红(被动兜底比例高 = 真实需求弱)
AUCTION_DEALER_WARN = 20.0

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
    ("市场总览",            "Market Overview",        "overview",   True),
    ("利率与曲线",          "Rates & Curve",          "rates",      True),
    ("曲线历史",            "Curve History",          "curve_hist", True),
    ("美债实验室",          "Treasury Lab",           "ust",        True),
    ("情绪 / 风险",         "Sentiment / Risk",       "sentiment",  True),
    ("宏观日历 & 事件研究", "Calendar & Event Study", "events",     True),
    ("CPI 详情",            "CPI Detail",             "cpi",        True),
    ("持仓监测 (Phase 2)",  "Portfolio (Phase 2)",    "portfolio",  False),   # 占位
    ("智能简报 (Phase 3)",  "Briefing (Phase 3)",     "brief",      False),   # 占位
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
        "ov_grp_policy":   "政策与利率",
        "ov_grp_growth":   "增长",
        "ov_grp_infl":     "通胀",
        "ov_grp_usd":      "美元与避险",
        "ov_window":       "时间窗口",
        "ov_chart_yield":  "收益率走势(%)",
        "ov_chart_price":  "价格类走势(基准化 = 100)",
        "ov_chart_note":   "收益率单独画原始 %:4.5% 涨到 4.97% 做成基准化是 +10%,看起来会和标普涨 10% 一样大,但意思完全不同。",
        "ov_quad_hint":    "读法:增长那一组和通胀那一组同时看,就是四象限里的位置。铜和高收益债利差比股指诚实——股指里混了估值。",
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
        # 曲线历史
        "ch_title":        "曲线历史",
        "ch_sub":          "10年期 − 2年期。跌破零 = 倒挂,1976 年以来每次美国衰退之前都出现过。灰色区间是 NBER 认定的衰退期。",
        "ch_need_key":     "本页需要免费 FRED key(在 Secrets 设 FRED_API_KEY)。",
        "ch_2s10s":        "10Y − 2Y",
        "ch_3m10s":        "10Y − 3M",
        "ch_2y":           "2年期",
        "ch_10y":          "10年期",
        "ch_vs_1m":        "对比一个月前",
        "ch_state_inv":    "曲线已倒挂",
        "ch_state_flat":   "曲线偏平",
        "ch_state_norm":   "曲线正常",
        "ch_chart_long":   "1976 至今(灰色 = 衰退期)",
        "ch_chart_zoom":   "最近 5 年(当前周期)",
        "ch_levels":       "收益率水平(最近 5 年)",
        "ch_latest":       "最新数据:{date}",
        "ch_download":     "下载 CSV",
        "ch_note":         "每天看的不是这个数字本身,是方向:持续往 0 走 = 市场越来越认为政策过紧;持续走宽 = 市场越来越不这么认为。3m10s 在学术研究里预测衰退比 2s10s 更准,两条一起看。",
        # 美债实验室
        "ust_title":        "美债实验室",
        "ust_need_key":     "本页需要免费 FRED key(在 Secrets 设 FRED_API_KEY)。",
        "ust_window":       "回看窗口",
        "ust_nom10":        "10Y 名义",
        "ust_real10":       "10Y 实际",
        "ust_be10":         "10Y 盈亏平衡",
        "ust_be5y5y":       "5年后5年 远期",
        "ust_tp10":         "10Y 期限溢价",
        "ust_2s10s":        "2s10s 利差",
        "ust_3m10s":        "3m10s 利差",
        "ust_move":         "MOVE 债市波动",
        "ust_tp_note":      "模型估计值,会修正",
        "ust_anchor":       "长期通胀中枢",
        # 第一层
        "ust_decomp_title": "第一层 · 收益率分解归因",
        "ust_decomp_sub":   "{win}内,10Y 名义收益率变动 {bp} bps。两刀拆开看它是什么构成的:",
        "ust_cut1":         "第一刀:实际利率 + 通胀补偿",
        "ust_cut2":         "第二刀:预期短端路径 + 期限溢价",
        "ust_bar_nominal":  "名义变动",
        "ust_bar_real":     "实际利率贡献",
        "ust_bar_be":       "通胀补偿贡献",
        "ust_bar_path":     "预期路径贡献",
        "ust_bar_tp":       "期限溢价贡献",
        "ust_read_a":       "**A 政策路径主导** —— 市场在重新定价美联储。风险资产通常同步受压,美元偏强,黄金承压。",
        "ust_read_b":       "**B 期限溢价主导** —— 供给 / 财政 / 不确定性的故事。常见股债双杀,美元和黄金的反应可能与 A 情形相反。",
        "ust_read_c":       "**C 通胀补偿主导** —— 实际利率未必动,黄金反而可能受益。去看 5年后5年远期有没有跟着走;只有短端在动,那就只是油价。",
        "ust_read_real":    "**实际利率主导** —— 名义变动主要来自实际利率,不是通胀预期。但要分清是 A(政策路径)还是 B(期限溢价),得看第二刀。",
        "ust_read_mix":     "没有单一通道主导(最大贡献占比不足 {pct}%)。这一段是混合驱动,别急着讲故事。",
        "ust_read_flat":    "{win}内 10Y 基本没动({bp} bps),没有值得归因的变动。",
        "ust_bar_zero":     "零息拟合收益率变动",
        "ust_tp_lag":       "两刀的口径不同,数字对不上是正常的:第一刀用 DGS10(附息、固定期限),第二刀用 Kim-Wright 的零息拟合收益率——因为期限溢价是针对零息债算的,必须配同口径的收益率来减。加上期限溢价发布有滞后,两边窗口末端也差几天。",
        "ust_tp_missing":   "期限溢价或零息拟合收益率暂时取不到,第二刀跳过(Kim-Wright 发布本身有滞后)。",
        "ust_verify":       "交叉验证:如果归因指向期限溢价,那么下面的拍卖数据里应该能看到一级交易商承接率上升、需求转弱。看不到,说明这个故事讲错了。",
        # 第二层
        "ust_regime_title": "第二层 · 曲线形态",
        "ust_bull_steep":   "牛陡 · 宽松预期启动",
        "ust_bull_flat":    "牛平 · 避险 / 增长恐慌",
        "ust_bear_steep":   "熊陡 · 财政 / 供给 / 再通胀",
        "ust_bear_flat":    "熊平 · 紧缩预期加码",
        "ust_steepen":      "陡化 · 水平没动,只有斜率在走",
        "ust_flatten":      "平坦化 · 水平没动,只有斜率在走",
        "ust_bear_par":     "熊市平移 · 整条曲线上移,斜率基本没变",
        "ust_bull_par":     "牛市平移 · 整条曲线下移,斜率基本没变",
        "ust_regime_flat":  "横盘 · 变动不足 {bp} bps,不判方向",
        "ust_regime_now":   "当前形态:",
        "ust_regime_detail": "{win}内:2Y {d2} bps · 10Y {d10} bps · 利差 {ds} bps",
        "ust_quad_title":   "四象限轨迹(过去 1 年,每周一个点)",
        "ust_quad_x":       "利差变动(bps) · 右=陡化,左=平坦化",
        "ust_quad_y":       "水平变动(bps) · 上=熊,下=牛",
        "ust_quad_note":    "亮色是最新一周。形态发生切换时记一条:日期、切到哪一格、**查数据之前**先写下预期的资产反应、事后写实际反应。",
        # 第三层
        "ust_auction_title": "第三层 · 拍卖监测",
        "ust_auction_sub":  "每场拍卖都是一次真实的需求测试。数据直接取自 TreasuryDirect 公开接口,不需要 key。",
        "ust_col_date":     "拍卖日",
        "ust_col_term":     "期限",
        "ust_col_yield":    "中标利率",
        "ust_col_btc":      "投标倍数",
        "ust_col_btc_diff": "对比近{n}次",
        "ust_col_dealer":   "一级交易商承接",
        "ust_col_indirect": "间接投资者",
        "ust_auction_fail": "拍卖数据暂时取不到(TreasuryDirect 接口可能临时不可用或字段有变)。不影响本页其他内容。",
        "ust_auction_note": "投标倍数的绝对值没有意义,只跟**同期限**过去 {n} 次比。一级交易商是被动兜底方,承接率高说明真实需求没接住,通常伴随 tail 走扩。注意:tail(中标利率减 when-issued)这里算不出来——TreasuryDirect 不提供 when-issued 价格,要看 tail 得另找数据源。",
        # 第四层
        "ust_check_title":  "第四层 · 定价检验",
        "ust_move_note":    "MOVE 是债市版的 VIX。它快速上行不只是情绪——基差交易杠杆很高,波动率飙升会触发保证金追缴和平仓,反过来放大债市本身的波动。它也是区分「流动性事件」和「基本面重定价」的工具。",
        "ust_cot_note":     "期货持仓(CFTC 周度)还没接进来,暂时在 notebook 里做。提醒自己:利率期货里杠杆基金的巨额净空头大多是基差交易,不是方向性看空;要看的是**资产管理人净多头**的历史分位。",
        "ust_handbook":     "本页对应《美债研究手册》的第一到第四层。第五层(票息 / 骑乘 / 融资 / 久期 / 凸性 → 仓位)在手册里,不在这个页面。",
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
        "ov_grp_policy":   "Policy & Rates",
        "ov_grp_growth":   "Growth",
        "ov_grp_infl":     "Inflation",
        "ov_grp_usd":      "Dollar & Haven",
        "ov_window":       "Window",
        "ov_chart_yield":  "Yields (%)",
        "ov_chart_price":  "Price assets (rebased to 100)",
        "ov_chart_note":   "Yields are plotted at their raw level: 4.5% rising to 4.97% is +10% once rebased, which looks as big as the S&P gaining 10% but means something entirely different.",
        "ov_quad_hint":    "How to read it: the growth row and the inflation row together give you the quadrant. Copper and credit spreads are more honest than the index — equities carry a valuation component.",
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
        # Curve history
        "ch_title":        "Curve History",
        "ch_sub":          "10-year minus 2-year. Below zero = inverted; every US recession since 1976 was preceded by one. Grey bands are NBER recessions.",
        "ch_need_key":     "This page needs a free FRED key (set FRED_API_KEY in Secrets).",
        "ch_2s10s":        "10Y − 2Y",
        "ch_3m10s":        "10Y − 3M",
        "ch_2y":           "2-year",
        "ch_10y":          "10-year",
        "ch_vs_1m":        "vs 1 month ago",
        "ch_state_inv":    "Curve is INVERTED",
        "ch_state_flat":   "Curve is flat",
        "ch_state_norm":   "Curve is normal",
        "ch_chart_long":   "Since 1976 (grey = recessions)",
        "ch_chart_zoom":   "Last 5 years (current cycle)",
        "ch_levels":       "Yield levels (last 5 years)",
        "ch_latest":       "Latest data: {date}",
        "ch_download":     "Download CSV",
        "ch_note":         "What to watch daily is not the level but the direction: grinding toward zero means the market increasingly thinks policy is too tight; widening means the opposite. Academic work finds 3m10s predicts recessions better than 2s10s — watch both.",
        # Treasury Lab
        "ust_title":        "Treasury Lab",
        "ust_need_key":     "This page needs a free FRED key (set FRED_API_KEY in Secrets).",
        "ust_window":       "Lookback window",
        "ust_nom10":        "10Y Nominal",
        "ust_real10":       "10Y Real",
        "ust_be10":         "10Y Breakeven",
        "ust_be5y5y":       "5y5y Forward",
        "ust_tp10":         "10Y Term Premium",
        "ust_2s10s":        "2s10s Spread",
        "ust_3m10s":        "3m10s Spread",
        "ust_move":         "MOVE (Bond Vol)",
        "ust_tp_note":      "Model estimate — gets revised",
        "ust_anchor":       "Long-run inflation anchor",
        # Layer 1
        "ust_decomp_title": "Layer 1 · Yield Decomposition",
        "ust_decomp_sub":   "Over the past {win}, the 10Y nominal yield moved {bp} bps. Two ways to cut it:",
        "ust_cut1":         "Cut one: real yield + inflation compensation",
        "ust_cut2":         "Cut two: expected policy path + term premium",
        "ust_bar_nominal":  "Nominal move",
        "ust_bar_real":     "Real yield contribution",
        "ust_bar_be":       "Breakeven contribution",
        "ust_bar_path":     "Expected path contribution",
        "ust_bar_tp":       "Term premium contribution",
        "ust_read_a":       "**Channel A — policy path dominates.** The market is repricing the Fed. Risk assets usually come under pressure together, the dollar firms, gold struggles.",
        "ust_read_b":       "**Channel B — term premium dominates.** A supply / fiscal / uncertainty story. Often stocks and bonds fall together, and the dollar and gold can react opposite to the Channel A case.",
        "ust_read_c":       "**Channel C — inflation compensation dominates.** Real yields may not have moved at all, and gold can actually benefit. Check whether 5y5y forward moved too; if only the front end moved, it is just oil.",
        "ust_read_real":    "**Real yields dominate** — the nominal move came from real yields, not inflation expectations. Separating Channel A (policy path) from Channel B (term premium) takes cut two.",
        "ust_read_mix":     "No single channel dominates (the largest contribution is under {pct}%). This stretch is mixed — don't reach for a story yet.",
        "ust_read_flat":    "The 10Y barely moved over the past {win} ({bp} bps) — nothing worth attributing.",
        "ust_bar_zero":     "Fitted zero-coupon move",
        "ust_tp_lag":       "The two cuts use different conventions, so the numbers won't match: cut one uses DGS10 (coupon-bearing, constant maturity), cut two uses the Kim-Wright fitted zero-coupon yield — the term premium is computed on a zero-coupon bond, so it has to be subtracted from a yield on the same basis. The term premium is also published with a lag, so the windows end a few days apart.",
        "ust_tp_missing":   "Term premium or fitted zero-coupon yield unavailable right now, so cut two is skipped (Kim-Wright is published with a lag).",
        "ust_verify":       "Cross-check: if the attribution points to term premium, the auction data below should show primary dealer takedown rising. If it doesn't, the story is wrong.",
        # Layer 2
        "ust_regime_title": "Layer 2 · Curve Regime",
        "ust_bull_steep":   "Bull steepener · easing expectations",
        "ust_bull_flat":    "Bull flattener · flight to quality",
        "ust_bear_steep":   "Bear steepener · fiscal / supply / reflation",
        "ust_bear_flat":    "Bear flattener · tightening repriced",
        "ust_steepen":      "Steepening · level flat, only the slope moved",
        "ust_flatten":      "Flattening · level flat, only the slope moved",
        "ust_bear_par":     "Bear parallel shift · whole curve up, slope unchanged",
        "ust_bull_par":     "Bull parallel shift · whole curve down, slope unchanged",
        "ust_regime_flat":  "Range-bound · moves under {bp} bps, no call",
        "ust_regime_now":   "Current regime: ",
        "ust_regime_detail": "Over {win}: 2Y {d2} bps · 10Y {d10} bps · spread {ds} bps",
        "ust_quad_title":   "Regime map (past year, one point per week)",
        "ust_quad_x":       "Spread change (bps) · right = steepening, left = flattening",
        "ust_quad_y":       "Level change (bps) · up = bear, down = bull",
        "ust_quad_note":    "The bright point is the latest week. When the regime flips, log it: date, which quadrant, the asset reaction you expect written down **before** you check, then what actually happened.",
        # Layer 3
        "ust_auction_title": "Layer 3 · Auction Monitor",
        "ust_auction_sub":  "Every auction is a live demand test. Data comes straight from the TreasuryDirect public API — no key needed.",
        "ust_col_date":     "Auction date",
        "ust_col_term":     "Term",
        "ust_col_yield":    "High yield",
        "ust_col_btc":      "Bid-to-cover",
        "ust_col_btc_diff": "vs last {n}",
        "ust_col_dealer":   "Dealer takedown",
        "ust_col_indirect": "Indirect bidders",
        "ust_auction_fail": "Auction data unavailable right now (the TreasuryDirect API may be down or its fields may have changed). The rest of this page is unaffected.",
        "ust_auction_note": "The absolute bid-to-cover means nothing — compare it only with the **same tenor's** last {n} auctions. Primary dealers are the backstop buyer, so a high takedown means real demand didn't show up, usually alongside a wider tail. Note: tail (high yield minus when-issued) can't be computed here — TreasuryDirect doesn't publish when-issued levels, so tail needs another data source.",
        # Layer 4
        "ust_check_title":  "Layer 4 · Positioning Check",
        "ust_move_note":    "MOVE is the bond market's VIX. A fast move up is not just sentiment — basis trades are highly levered, so a vol spike triggers margin calls and unwinds that amplify bond volatility itself. It also separates a liquidity event from a fundamental repricing.",
        "ust_cot_note":     "Futures positioning (weekly CFTC) isn't wired in yet — still done in the notebook. Reminder: the huge leveraged-fund net shorts in rate futures are mostly basis trades, not directional bearishness. What to watch is the **asset manager net long** and its historical percentile.",
        "ust_handbook":     "This page covers Layers 1–4 of the Treasury research handbook. Layer 5 (carry / roll-down / financing / duration / convexity → position sizing) lives in the handbook, not here.",
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
