"""
拉取全部在市A股历史价格数据（日K + 月K收盘价），落到 data/price/ 目录。

股票列表从 data/stock_list_listed_all.csv 读取，不重新拉取。
已存在的文件跳过（增量模式），网络失败自动跳过并记录。

运行方式：
  # 调试模式（1只股票，2个月）
  python3 fetch_price.py --debug

  # 全量
  python3 fetch_price.py
"""

import argparse
import time
import akshare as ak
import pandas as pd
from pathlib import Path

ROOT     = Path(__file__).parent
DATA_DIR = ROOT / "data"
DAILY_DIR   = DATA_DIR / "price" / "daily"
MONTHLY_DIR = DATA_DIR / "price" / "monthly"
LIST_FILE   = DATA_DIR / "stock_list_listed_all.csv"

DAILY_DIR.mkdir(parents=True, exist_ok=True)
MONTHLY_DIR.mkdir(parents=True, exist_ok=True)

# 163数据源前缀
EXCHANGE_PREFIX = {"SH": "sh", "SZ": "sz", "BJ": "bj"}


def load_stock_list() -> pd.DataFrame:
    df = pd.read_csv(LIST_FILE, dtype={"code": str})
    df["code"] = df["code"].str.zfill(6)
    return df


def fetch_daily(symbol_163: str) -> pd.DataFrame:
    """拉取后复权日K，返回 date/open/high/low/close/volume"""
    df = ak.stock_zh_a_daily(symbol=symbol_163, adjust="hfq")
    df["date"] = pd.to_datetime(df["date"])
    return df[["date", "open", "high", "low", "close", "volume"]]


def to_monthly(df_daily: pd.DataFrame) -> pd.DataFrame:
    """日K → 月K（每月最后一个交易日收盘价）"""
    df = df_daily.set_index("date").sort_index()
    monthly = df["close"].resample("ME").last().dropna()
    monthly.index.name = "date"
    return monthly.reset_index().rename(columns={"close": "close_monthly"})


def process_stock(code: str, exchange: str, debug_months: int = None):
    prefix   = EXCHANGE_PREFIX.get(exchange, "sz")
    symbol   = f"{prefix}{code}"
    daily_f  = DAILY_DIR   / f"{code}.csv"
    monthly_f = MONTHLY_DIR / f"{code}.csv"

    if daily_f.exists() and monthly_f.exists():
        return "skip"

    df = fetch_daily(symbol)

    if debug_months:
        cutoff = df["date"].max() - pd.DateOffset(months=debug_months)
        df = df[df["date"] >= cutoff]

    df.to_csv(daily_f, index=False)

    df_monthly = to_monthly(df)
    df_monthly.to_csv(monthly_f, index=False)

    return "ok"


def main(debug: bool = False):
    stocks = load_stock_list()
    print(f"股票列表加载完成，共 {len(stocks)} 条")

    if debug:
        stocks = stocks.head(1)
        debug_months = 2
        print(f"调试模式：只处理 {stocks.iloc[0]['code']} {stocks.iloc[0]['name']}，最近 {debug_months} 个月")
    else:
        debug_months = None

    ok_count = skip_count = fail_count = 0
    failed = []

    for i, row in stocks.iterrows():
        code, exchange, name = row["code"], row["exchange"], row["name"]
        try:
            result = process_stock(code, exchange, debug_months)
            if result == "skip":
                skip_count += 1
                print(f"[{i+1}/{len(stocks)}] {code} {name}  SKIP（已存在）")
            else:
                ok_count += 1
                print(f"[{i+1}/{len(stocks)}] {code} {name}  OK")
            if not debug:
                time.sleep(0.3)
        except Exception as e:
            fail_count += 1
            failed.append((code, name, str(e)[:80]))
            print(f"[{i+1}/{len(stocks)}] {code} {name}  FAIL: {str(e)[:60]}")

    print(f"\n完成：OK={ok_count}  SKIP={skip_count}  FAIL={fail_count}")
    if failed:
        fail_log = DATA_DIR / "price_fetch_failed.txt"
        with open(fail_log, "w") as f:
            for code, name, err in failed:
                f.write(f"{code}\t{name}\t{err}\n")
        print(f"失败记录已写入 {fail_log}")

    # 调试时打印结果
    if debug:
        code = stocks.iloc[0]["code"]
        print("\n--- 日K（后5行）---")
        print(pd.read_csv(DAILY_DIR / f"{code}.csv").tail(5).to_string(index=False))
        print("\n--- 月K（后5行）---")
        print(pd.read_csv(MONTHLY_DIR / f"{code}.csv").tail(5).to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="调试模式：1只股票2个月数据")
    args = parser.parse_args()
    main(debug=args.debug)
