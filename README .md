# 宏观作战室 · Macro War Room (Phase 1)

个人投资作战室。Phase 1 上线:跨资产盯盘 + 利率曲线 + 市场情绪 + **宏观日历与事件研究** + CPI 详情。
私人使用(密码门),可分享给 1–2 人。后续 Phase 2(持仓监测)、Phase 3(智能新闻简报)已留好接口。

## 五个模块(Phase 1)
- **市场总览** — 黄金/白银/铜/原油/美元/美日/美人民币/标普/VIX/美债10年,实时价 + 日变动 + 基准化走势。
- **利率与曲线** — 美债 3M–30Y 收益率曲线、10Y 实际收益率(TIPS,黄金头号变量)、2s10s 利差。
- **情绪 / 风险** — VIX、MOVE、高收益债信用利差,外加一个 risk-on / risk-off 风险开关。
- **宏观日历 & 事件研究** — 看未来事件;点事件类型(FOMC / 美联储变动利率 / 日本加息 / CPI / 非农),自动跑**事件研究**:历史上这类事件前后,你选的资产平均怎么走、上涨概率多少。
- **CPI 详情** — 整体/核心/能源/食品/住房 同比 + 历史走势。

## 两个 Key(都免费)
| Key | 作用 | 不设的后果 |
|---|---|---|
| `APP_PASSWORD` | 访问密码 | 用默认密码 `gold2026`(请改) |
| `FRED_API_KEY` | 利率/CPI/事件发布日历 | 市场总览、情绪(VIX)仍可用;利率/CPI/CPI事件受限 |

- 行情(黄金、股、汇、VIX)走 **yfinance,不需要任何 key**。
- 利率曲线、CPI 分项、CPI/非农的历史发布日走 **FRED**(免费 key:https://fredaccount.stlouisfed.org/ → API Keys)。
- FOMC、日本加息日期已写死在 `config.py`(已核对到 2026),无需联网。

## 本地运行
```bash
pip install -r requirements.txt
export FRED_API_KEY=你的key
export APP_PASSWORD=你的密码
streamlit run app.py
```

## 部署成公开链接(Streamlit Community Cloud)
和之前一样:四…五个文件传到 GitHub 仓库根目录 → share.streamlit.io → New app 选 `app.py` →
**Advanced settings → Secrets** 里粘贴:
```toml
FRED_API_KEY = "你的key"
APP_PASSWORD = "你设的密码"
```
Deploy 后得到 `https://xxx.streamlit.app`,把链接+密码发给那 1–2 个人即可。

> 文件清单:`app.py` `core.py` `events.py` `config.py` `requirements.txt`(README 可选)。
> 这几个 .py 要在**同一层**。

## 怎么扩容(都改 `config.py`)
- **加资产**:`ASSETS` 加一行(写 yfinance 代码即可)。
- **加事件**:`EVENTS` 加一项(`manual` 写死日期 / `fred_release` 用发布日历 / `fred_change` 用利率变动日)。
- **加 CPI 分项**:`CPI_COMPONENTS` 加 FRED 序列。
- **加页面(Phase 2/3)**:`PAGES` 加一行 + 在 `app.py` 写个 `page_xxx()` 函数,注册进 `PAGE_FUNCS`。
  - 数据层 `core.py` 的 `yf_*` / `fred_*` 可直接复用,不用重写取数。

## Phase 2 / 3 预留
- **Phase 2 持仓**:你维护一个组合(可放 config 或 Google Sheet),页面盯实时盈亏、与宏观事件的暴露。
- **Phase 3 智能简报**:接 Claude API(建议 Haiku 筛新闻 + Sonnet 写简报),自动标出 MU/HBM 等催化剂,
  每天生成结合你仓位的简报。需要再加一个后台定时任务(GitHub Actions)做主动提醒。

## 数据口径与免责
- 事件研究纵轴 = 基准化到事件日 T0=100 的平均路径;价格类用 % 变动,收益率(美债)用 bps。
- CPI 同比按 FRED 月度指数计算(季调口径,展示用)。
- **本工具仅供研究,不构成投资建议。** 历史规律不代表未来。
