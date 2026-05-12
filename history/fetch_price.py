"""
拉取全部在市A股历史价格数据（日K + 月K收盘价），落到 data/price/ 目录。

优化后增量逻辑：
  1. 启动时从已有文件中推断「最近交易日」（无需联网）
  2. 已有数据且最新日期 >= 最近交易日 → 直接跳过，不发网络请求
  3. 需要更新时，仅查询 last_date+1 ~ today 的范围，减少数据量
  4. 新股（文件不存在）：拉取全量历史

股票列表从 data/stock_list_listed_all.csv 读取，不重新拉取。
网络失败自动跳过并记录到 data/price_fetch_failed.txt。
所有网络请求 30 秒超时，防止单只股票挂起整个流程。

运行方式：
  python3 fetch_price.py --debug    # 调试：1只股票，最近2个月
  python3 fetch_price.py            # 全量增量更新
"""

import argparse
import socket
import time
from pathlib import Path

import akshare as ak
import pandas as pd

socket.setdefaulttimeout(30)

ROOT        = Path(__file__).parent.parent
DATA_DIR    = ROOT / "data"
DAILY_DIR   = DATA_DIR / "price" / "daily"
MONTHLY_DIR = DATA_DIR / "price" / "monthly"
LIST_FILE   = DATA_DIR / "stock_list_listed_all.csv"

DAILY_DIR.mkdir(parents=True, exist_ok=True)
MONTHLY_DIR.mkdir(parents=True, exist_ok=True)

EXCHANGE_PREFIX = {"SH": "sh", "SZ": "sz", "BJ": "bj"}


def load_stock_list() -> pd.DataFrame:
    df = pd.read_csv(LIST_FILE, dtype={"code": str})
    df["code"] = df["code"].str.zfill(6)
    return df


def get_latest_trading_day() -> pd.Timestamp:
    """
    从已有日K文件中采样，推断最近交易日。
    取多个文件最新日期的众数（最常见值），避免个别新股/停牌股拉低结果。
    """
    files = list(DAILY_DIR.glob("*.csv"))
    if not files:
        return pd.Timestamp("1990-01-01")
    sample = files[:50]
    dates = []
    for f in sample:
        try:
            df = pd.read_csv(f, usecols=["date"], parse_dates=["date"])
            if not df.empty:
                dates.append(df["date"].max())
        except Exception:
            pass
    if not dates:
        return pd.Timestamp("1990-01-01")
    return pd.Series(dates).mode()[0]


def fetch_daily(symbol_163: str, start_date: str = "19900101",
                end_date: str = "21001231") -> pd.DataFrame:
    """从 163 数据源拉取后复权日K，支持日期范围。"""
    df = ak.stock_zh_a_daily(
        symbol=symbol_163, start_date=start_date, end_date=end_date, adjust="hfq"
    )
    df["date"] = pd.to_datetime(df["date"])
    return df[["date", "open", "high", "low", "close", "volume"]].sort_values("date")


def update_monthly(daily_f: Path, monthly_f: Path, from_date: pd.Timestamp = None):
    """
    从 daily CSV 重建月K。
    from_date：只重算该日期所在月起的数据（增量时传入上次月K最后日期）。
    """
    df_daily = pd.read_csv(daily_f, parse_dates=["date"])
    df_daily = df_daily.set_index("date").sort_index()

    if from_date is not None and monthly_f.exists():
        recalc_start = from_date.to_period("M").to_timestamp()
        new_monthly = (
            df_daily.loc[recalc_start:, "close"]
            .resample("ME").last()
            .dropna()
            .reset_index()
            .rename(columns={"close": "close_monthly"})
        )
        old_monthly = pd.read_csv(monthly_f, parse_dates=["date"])
        old_monthly = old_monthly[old_monthly["date"] < recalc_start]
        result = pd.concat([old_monthly, new_monthly], ignore_index=True)
    else:
        result = (
            df_daily["close"]
            .resample("ME").last()
            .dropna()
            .reset_index()
            .rename(columns={"close": "close_monthly"})
        )

    result.to_csv(monthly_f, index=False)


def process_stock(code: str, exchange: str,
                  latest_td: pd.Timestamp = None,
                  debug_months: int = None) -> str:
    prefix    = EXCHANGE_PREFIX.get(exchange, "sz")
    symbol    = f"{prefix}{code}"
    daily_f   = DAILY_DIR   / f"{code}.csv"
    monthly_f = MONTHLY_DIR / f"{code}.csv"

    if daily_f.exists():
        old_daily = pd.read_csv(daily_f, parse_dates=["date"])
        last_date = old_daily["date"].max()

        # ── 快速跳过：已达最近交易日，无需联网 ──────────
        if latest_td is not None and last_date >= latest_td:
            return "up-to-date"

        # ── 增量：仅拉取缺失日期范围 ──────────────────
        start_str = (last_date + pd.Timedelta(days=1)).strftime("%Y%m%d")
        end_str   = pd.Timestamp.today().strftime("%Y%m%d")
        new_rows  = fetch_daily(symbol, start_date=start_str, end_date=end_str)

        if new_rows.empty:
            return "up-to-date"

        new_rows.to_csv(daily_f, mode="a", header=False, index=False)

        if monthly_f.exists():
            old_monthly = pd.read_csv(monthly_f, parse_dates=["date"])
            recalc_from = old_monthly["date"].max() if not old_monthly.empty else last_date
        else:
            recalc_from = last_date

        update_monthly(daily_f, monthly_f, from_date=recalc_from)
        return f"appended +{len(new_rows)}rows"

    else:
        # ── 首次拉取全量 ──────────────────────────────
        df = fetch_daily(symbol)

        if debug_months:
            cutoff = df["date"].max() - pd.DateOffset(months=debug_months)
            df = df[df["date"] >= cutoff]

        if df.empty:
            return "empty"

        df.to_csv(daily_f, index=False)
        update_monthly(daily_f, monthly_f)
        return f"new({len(df)}rows)"


def main(debug: bool = False):
    stocks = load_stock_list()
    print(f"股票列表加载完成，共 {len(stocks)} 条")

    latest_td = get_latest_trading_day()
    print(f"最近交易日（本地推断）：{latest_td.date()}")

    if debug:
        stocks = stocks.head(1)
        print(f"调试模式：{stocks.iloc[0]['code']} {stocks.iloc[0]['name']}，最近2个月")

    counts  = {"new": 0, "appended": 0, "up-to-date": 0, "fail": 0, "empty": 0}
    failed  = []
    total   = len(stocks)

    for i, row in stocks.iterrows():
        code, exchange, name = row["code"], row["exchange"], row["name"]
        try:
            result = process_stock(
                code, exchange,
                latest_td=latest_td,
                debug_months=2 if debug else None,
            )
            if result.startswith("appended"):
                tag = "appended"
            elif result.startswith("new"):
                tag = "new"
            else:
                tag = result
            counts[tag] = counts.get(tag, 0) + 1
            print(f"[{i+1}/{total}] {code} {name:<10}  {result}")
            if not debug and tag != "up-to-date":
                time.sleep(0.3)
        except Exception as e:
            counts["fail"] += 1
            failed.append((code, name, str(e)[:100]))
            print(f"[{i+1}/{total}] {code} {name:<10}  FAIL: {str(e)[:80]}")

    print(
        f"\n完成：新增={counts['new']}  追加={counts['appended']}"
        f"  已最新={counts['up-to-date']}  失败={counts['fail']}"
    )

    if failed:
        fail_log = DATA_DIR / "price_fetch_failed.txt"
        with open(fail_log, "w") as f:
            for code, name, err in failed:
                f.write(f"{code}\t{name}\t{err}\n")
        print(f"失败记录 → {fail_log}")

    if debug:
        code = stocks.iloc[0]["code"]
        print("\n--- 日K（后5行）---")
        print(pd.read_csv(DAILY_DIR / f"{code}.csv").tail(5).to_string(index=False))
        print("\n--- 月K（后5行）---")
        print(pd.read_csv(MONTHLY_DIR / f"{code}.csv").tail(5).to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="调试模式：1只股票，最近2个月")
    args = parser.parse_args()
    main(debug=args.debug)
