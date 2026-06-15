"""
events.py —— 事件研究(event study)纯算法层
只依赖 pandas / numpy,不碰 streamlit / 网络,方便单测。
网络相关的"取事件日期"在 core.py 里(因为要打 FRED)。
"""
import pandas as pd
import numpy as np


def parse_dates(date_list):
    """manual 事件:字符串日期 → 排序后的 Timestamp 列表。"""
    return sorted(pd.Timestamp(d).normalize() for d in date_list)


def rate_change_dates(series: pd.Series):
    """fred_change 事件:给定政策利率日序列,返回数值发生变化的日期。"""
    s = series.dropna().sort_index()
    changed = s[s.diff().fillna(0) != 0]
    return [pd.Timestamp(d).normalize() for d in changed.index]


def _nearest_pos(index: pd.DatetimeIndex, when: pd.Timestamp):
    """找到 <= when 的最后一个交易日位置(事件日当天没数据就取前一日)。"""
    pos = index.searchsorted(when, side="right") - 1
    if pos < 0:
        return None
    return pos


def event_study(price_dict: dict, event_dates, pre: int = 5, post: int = 10,
                yield_flags: dict = None):
    """
    price_dict : {asset_code: pd.Series(收盘价, index=DatetimeIndex 升序)}
    event_dates: 事件日期列表
    返回:
      avg_path : DataFrame(index = 相对日 -pre..+post, columns = 资产) 均值,基准化到 T0=100
      moves    : DataFrame 每次事件、每个资产在 T+1/T+5/T+10 的原生变动
                 (价格用 %,收益率用 bps)
      n        : 实际用上的事件次数
    """
    yield_flags = yield_flags or {}
    rel = list(range(-pre, post + 1))
    paths = {a: [] for a in price_dict}          # 每个资产:多次事件的基准化路径
    move_rows = []
    used = 0

    for ev in event_dates:
        ev = pd.Timestamp(ev).normalize()
        ok_any = False
        row_per_asset = {}
        path_per_asset = {}
        for a, s in price_dict.items():
            s = s.dropna()
            if s.empty:
                continue
            idx = s.index
            pos = _nearest_pos(idx, ev)
            if pos is None or pos - pre < 0 or pos + post >= len(s):
                continue
            window = s.iloc[pos - pre: pos + post + 1].astype(float)
            base = window.iloc[pre]               # T0 基准
            if base == 0 or pd.isna(base):
                continue
            path_per_asset[a] = (window.values / base * 100.0)
            # 原生变动
            t0 = base
            def mv(k):
                v = window.iloc[pre + k]
                if yield_flags.get(a):            # 收益率:bps 变动
                    return (v - t0) * 100.0
                return (v / t0 - 1) * 100.0       # 价格:百分比
            row_per_asset[a] = {"T+1": mv(1), "T+5": mv(5), "T+10": mv(10)}
            ok_any = True
        if ok_any:
            used += 1
            for a, p in path_per_asset.items():
                paths[a].append(p)
            move_rows.append({"event": ev.date(), **{f"{a}_{k}": row_per_asset[a][k]
                              for a in row_per_asset for k in ("T+1", "T+5", "T+10")}})

    avg = {}
    for a, lst in paths.items():
        if lst:
            avg[a] = np.nanmean(np.vstack(lst), axis=0)
    avg_path = pd.DataFrame(avg, index=rel) if avg else pd.DataFrame(index=rel)
    moves = pd.DataFrame(move_rows)
    return avg_path, moves, used


def summarize_moves(moves: pd.DataFrame, asset: str):
    """某资产:均值变动 + 上涨概率(基于 T+1)。"""
    out = {}
    for k in ("T+1", "T+5", "T+10"):
        col = f"{asset}_{k}"
        if col in moves:
            vals = moves[col].dropna()
            out[k] = {"mean": float(vals.mean()) if len(vals) else float("nan"),
                      "win": float((vals > 0).mean() * 100) if len(vals) else float("nan")}
    return out
