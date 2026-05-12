"""
拉取 data/index_selected.csv 中所有指数及对应全收益指数的历史日K数据，
落到 data/index/price/{code}.csv。

数据源策略：
  - 中证体系（000xxx/930xxx/932xxx/H0xxxx/899xxx/多数399xxx）
    → stock_zh_index_hist_csindex，支持 start_date/end_date 精确拉取
  - 深交所自有指数（399001/399006/399303/399321/399324/399673）
    → stock_zh_index_daily（新浪），拉全量后按日期过滤

统一输出字段：date, open, high, low, close, volume, pct_chg

增量逻辑：
  - 文件已存在 → 读取最后日期，只追加新数据
  - 文件不存在 → 拉取全量历史

失败记录 → data/index_price_fetch_failed.txt

运行方式：
  python3 fetch_index_price.py --debug   # 只跑前3个指数，最近3个月
  python3 fetch_index_price.py           # 全量增量
"""

import argparse
import time
from datetime import date, timedelta
from pathlib import Path

import akshare as ak
import pandas as pd

ROOT        = Path(__file__).parent.parent
DATA_DIR    = ROOT / "data"
PRICE_DIR   = DATA_DIR / "index" / "price"
SELECTED_F  = DATA_DIR / "index_selected.csv"
FAIL_LOG    = DATA_DIR / "index_price_fetch_failed.txt"

PRICE_DIR.mkdir(parents=True, exist_ok=True)

# 深交所自有指数：需要用 stock_zh_index_daily（新浪）
SINA_CODES = {"399001", "399006", "399303", "399321", "399324", "399673"}

OUTPUT_COLS = ["date", "open", "high", "low", "close", "volume", "pct_chg"]


# ── 数据拉取 ────────────────────────────────────────────────────────

def fetch_csindex(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """中证接口：返回标准化 DataFrame。"""
    df = ak.stock_zh_index_hist_csindex(
        symbol=code, start_date=start_date, end_date=end_date
    )
    df = df.rename(columns={
        "日期": "date", "开盘": "open", "最高": "high",
        "最低": "low",  "收盘": "close", "成交量": "volume", "涨跌幅": "pct_chg",
    })
    df["date"] = pd.to_datetime(df["date"])
    return df[OUTPUT_COLS].drop_duplicates("date").sort_values("date")


def fetch_sina(code: str) -> pd.DataFrame:
    """新浪接口（深交所自有指数）：返回标准化 DataFrame。"""
    prefix = "sz" if code.startswith("3") else "sh"
    df = ak.stock_zh_index_daily(symbol=f"{prefix}{code}")
    df = df.rename(columns={"date": "date"})
    df["date"] = pd.to_datetime(df["date"])
    for col in ["open", "high", "low", "close", "volume"]:
        if col not in df.columns:
            df[col] = None
    if "pct_chg" not in df.columns:
        df["pct_chg"] = df["close"].pct_change() * 100
    return df[OUTPUT_COLS].drop_duplicates("date").sort_values("date")


# ── 单指数处理 ───────────────────────────────────────────────────────

def process_index(code: str, name: str, debug_months: int = None) -> str:
    """
    增量拉取单个指数，返回状态字符串。
    """
    f = PRICE_DIR / f"{code}.csv"
    today = date.today().strftime("%Y%m%d")
    use_sina = code in SINA_CODES

    if f.exists():
        old = pd.read_csv(f, parse_dates=["date"])
        last_date = old["date"].max()
        start_str = (last_date + timedelta(days=1)).strftime("%Y%m%d")

        if start_str > today:
            return "up-to-date"

        try:
            if use_sina:
                new_all = fetch_sina(code)
                new_rows = new_all[new_all["date"] > last_date]
            else:
                new_rows = fetch_csindex(code, start_str, today)
        except Exception:
            # csindex 对空区间（非交易日）可能返回异常，视为无新数据
            return "up-to-date"

        if debug_months:
            cutoff = pd.Timestamp.today() - pd.DateOffset(months=debug_months)
            new_rows = new_rows[new_rows["date"] >= cutoff]

        if new_rows.empty:
            return "up-to-date"

        new_rows.to_csv(f, mode="a", header=False, index=False)
        return f"appended +{len(new_rows)}rows"

    else:
        if use_sina:
            df = fetch_sina(code)
        else:
            df = fetch_csindex(code, "19900101", today)

        if debug_months:
            cutoff = pd.Timestamp.today() - pd.DateOffset(months=debug_months)
            df = df[df["date"] >= cutoff]

        df.to_csv(f, index=False)
        return f"new({len(df)}rows)"


# ── 主流程 ──────────────────────────────────────────────────────────

def build_task_list() -> list[dict]:
    """
    从 index_selected.csv 读取所有要拉取的指数（含全收益）。
    返回 [{"code": ..., "name": ..., "type": "price"/"tr"}]
    """
    df = pd.read_csv(SELECTED_F, dtype=str).fillna("")
    tasks = []
    seen = set()

    for _, row in df.iterrows():
        code = row["index_code"].strip()
        name = row["name"].strip()
        if code and code not in seen:
            tasks.append({"code": code, "name": name, "type": "price"})
            seen.add(code)

        tr_code = row.get("tr_code", "").strip()
        tr_name = row.get("tr_name", "").strip()
        if tr_code and tr_code not in seen:
            tasks.append({"code": tr_code, "name": tr_name or name + "全收益", "type": "tr"})
            seen.add(tr_code)

    return tasks


def main(debug: bool = False):
    tasks = build_task_list()
    print(f"共 {len(tasks)} 个指数待处理（价格+全收益）")

    if debug:
        tasks = tasks[:3]
        print(f"调试模式：前3个，最近3个月")

    counts = {"new": 0, "appended": 0, "up-to-date": 0, "fail": 0}
    failed = []

    for i, t in enumerate(tasks, 1):
        code, name, kind = t["code"], t["name"], t["type"]
        label = f"[{i}/{len(tasks)}] {code} {name}({'全收益' if kind == 'tr' else '价格'})"
        try:
            result = process_index(code, name, debug_months=3 if debug else None)
            tag = "appended" if result.startswith("appended") else \
                  "new"       if result.startswith("new")      else "up-to-date"
            counts[tag] += 1
            print(f"{label}  {result}")
            if not debug:
                time.sleep(0.2)
        except Exception as e:
            counts["fail"] += 1
            failed.append((code, name, str(e)[:100]))
            print(f"{label}  FAIL: {str(e)[:80]}")

    print(f"\n完成：新增={counts['new']}  追加={counts['appended']}  已最新={counts['up-to-date']}  失败={counts['fail']}")

    if failed:
        with open(FAIL_LOG, "w") as f:
            for code, name, err in failed:
                f.write(f"{code}\t{name}\t{err}\n")
        print(f"失败记录 → {FAIL_LOG}")

    if debug:
        code = tasks[0]["code"]
        csv_f = PRICE_DIR / f"{code}.csv"
        if csv_f.exists():
            print(f"\n--- {code} 后5行 ---")
            print(pd.read_csv(csv_f).tail(5).to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="调试：前3个指数，最近3个月")
    args = parser.parse_args()
    main(debug=args.debug)
