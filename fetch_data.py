"""
A股数据拉取脚本 —— 将数据落到 data/ 目录
可用数据源（当前网络验证通过）：
  - 上交所官方接口：股票列表
  - 网易163：个股/指数历史行情
  - 东方财富：新闻、资金流向、龙虎榜、大盘资金
  - 巨潮资讯：分红
  - 宏观：货币供应量 M2、CPI
"""

import akshare as ak
import pandas as pd
from pathlib import Path
from datetime import date

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# 抓取的标的
STOCKS = [
    ("000001", "sz", "平安银行"),
    ("600519", "sh", "贵州茅台"),
    ("000858", "sz", "五 粮 液"),
]

DATE_START = "2022-01-01"
DATE_END   = str(date.today())


def save(df: pd.DataFrame, filename: str):
    path = DATA_DIR / filename
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  [saved] {filename}  shape={df.shape}")


def section(title):
    print(f"\n{'='*50}\n{title}")


# ─────────────────────────────────────────
# 1. 股票列表（上交所官方）
# ─────────────────────────────────────────
section("1. 股票列表")
df_sh_main = ak.stock_info_sh_name_code(symbol="主板A股")
df_sh_star = ak.stock_info_sh_name_code(symbol="科创板")
df_sse = pd.concat([df_sh_main, df_sh_star], ignore_index=True)
df_sse.insert(0, "market", "sh")
save(df_sse, "stock_list_sh.csv")

# ─────────────────────────────────────────
# 2. 指数历史行情（163数据源）
# ─────────────────────────────────────────
section("2. 指数历史行情")
for symbol, filename, name in [
    ("sh000001", "index_sh000001.csv", "上证指数"),
    ("sz399001", "index_sz399001.csv", "深证成指"),
    ("sz399006", "index_sz399006.csv", "创业板指"),
]:
    print(f"  拉取 {name}...")
    df = ak.stock_zh_index_daily(symbol=symbol)
    df = df[df["date"] >= DATE_START]
    save(df, filename)

# ─────────────────────────────────────────
# 3. 个股历史日K（163数据源，后复权）
# ─────────────────────────────────────────
section("3. 个股历史日K（后复权）")
for code, market, name in STOCKS:
    print(f"  拉取 {name}({code})...")
    df = ak.stock_zh_a_daily(symbol=f"{market}{code}", adjust="hfq")
    df = df[df["date"].astype(str) >= DATE_START]
    save(df, f"stock_{code}_daily_hfq.csv")

# ─────────────────────────────────────────
# 4. 个股资金流向
# ─────────────────────────────────────────
section("4. 个股资金流向")
for code, market, name in STOCKS:
    print(f"  拉取 {name}({code})...")
    df = ak.stock_individual_fund_flow(stock=code, market=market)
    save(df, f"stock_{code}_fund_flow.csv")

# ─────────────────────────────────────────
# 5. 大盘整体资金流向
# ─────────────────────────────────────────
section("5. 大盘资金流向")
df_mkt = ak.stock_market_fund_flow()
df_mkt = df_mkt[df_mkt["日期"].astype(str) >= DATE_START]
save(df_mkt, "market_fund_flow.csv")

# ─────────────────────────────────────────
# 6. 融资融券（上交所）
# ─────────────────────────────────────────
section("6. 融资融券（上交所）")
df_margin = ak.stock_margin_sse(start_date="20220101", end_date=DATE_END.replace("-", ""))
save(df_margin, "margin_sse.csv")

# ─────────────────────────────────────────
# 7. 龙虎榜统计
# ─────────────────────────────────────────
section("7. 龙虎榜统计")
for period in ["近一月", "近三月", "近六月"]:
    df = ak.stock_lhb_stock_statistic_em(symbol=period)
    save(df, f"lhb_{period}.csv")

# ─────────────────────────────────────────
# 8. 分红历史
# ─────────────────────────────────────────
section("8. 分红历史")
for code, market, name in STOCKS:
    print(f"  拉取 {name}({code})...")
    df = ak.stock_dividend_cninfo(symbol=code)
    save(df, f"stock_{code}_dividend.csv")

# ─────────────────────────────────────────
# 9. 个股新闻
# ─────────────────────────────────────────
section("9. 个股新闻")
for code, market, name in STOCKS:
    print(f"  拉取 {name}({code})...")
    df = ak.stock_news_em(symbol=code)
    save(df, f"stock_{code}_news.csv")

# ─────────────────────────────────────────
# 10. 宏观数据
# ─────────────────────────────────────────
section("10. 宏观数据")
df_m2 = ak.macro_china_money_supply()
save(df_m2, "macro_m2.csv")

df_cpi = ak.macro_china_cpi_monthly()
save(df_cpi, "macro_cpi.csv")

# ─────────────────────────────────────────
# 汇总
# ─────────────────────────────────────────
print(f"\n{'='*50}")
print(f"全部完成，数据已落到 {DATA_DIR}/")
files = sorted(DATA_DIR.glob("*.csv"))
for f in files:
    size_kb = f.stat().st_size // 1024
    print(f"  {f.name:<40} {size_kb:>5} KB")
