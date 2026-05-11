"""
AKShare A股数据全面 Demo
覆盖：行情、财务、估值、资金流、股东、宏观等
运行前确保已安装：pip install akshare pandas
"""

import akshare as ak
import pandas as pd

pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 120)
pd.set_option("display.float_format", "{:.2f}".format)

STOCK = "000001"   # 平安银行
STOCK_NAME = "平安银行"
START = "20240101"
END   = "20240110"

SEPARATOR = "\n" + "=" * 60 + "\n"


def section(title):
    print(f"{SEPARATOR}【{title}】")


def safe_run(title, fn):
    section(title)
    result = fn()
    if isinstance(result, pd.DataFrame):
        print(f"shape: {result.shape}")
        print(result.head(5).to_string())
    else:
        print(result)


# ──────────────────────────────────────────────
# 1. 历史行情 —— 日K线（不复权 / 前复权 / 后复权）
# ──────────────────────────────────────────────
safe_run(
    "历史日K线（前复权）",
    lambda: ak.stock_zh_a_hist(
        symbol=STOCK, period="daily",
        start_date=START, end_date=END,
        adjust="qfq"         # qfq=前复权 hfq=后复权 ""=不复权
    )
)

safe_run(
    "历史周K线（不复权）",
    lambda: ak.stock_zh_a_hist(
        symbol=STOCK, period="weekly",
        start_date=START, end_date=END,
        adjust=""
    )
)

# ──────────────────────────────────────────────
# 2. 实时行情
# ──────────────────────────────────────────────
safe_run(
    "A股全市场实时行情（前5条）",
    lambda: ak.stock_zh_a_spot_em().head(5)
)

safe_run(
    "单股实时报价",
    lambda: ak.stock_bid_ask_em(symbol=STOCK)
)

# ──────────────────────────────────────────────
# 3. 财务数据 —— 三大报表
# ──────────────────────────────────────────────
safe_run(
    "利润表（新浪，近8季）",
    lambda: ak.stock_profit_sheet_by_report_em(symbol=STOCK)
)

safe_run(
    "资产负债表（新浪，近8季）",
    lambda: ak.stock_balance_sheet_by_report_em(symbol=STOCK)
)

safe_run(
    "现金流量表（新浪，近8季）",
    lambda: ak.stock_cash_flow_sheet_by_report_em(symbol=STOCK)
)

# ──────────────────────────────────────────────
# 4. 财务指标 —— 估值 & 核心指标
# ──────────────────────────────────────────────
safe_run(
    "市盈率/市净率/ROE 等主要指标（东财）",
    lambda: ak.stock_financial_abstract_ths(symbol=STOCK, indicator="按年度")
)

safe_run(
    "每股指标（EPS/BPS/每股现金流）",
    lambda: ak.stock_per_share_index_em(symbol=STOCK)
)

# ──────────────────────────────────────────────
# 5. 估值历史 —— PE/PB 历史走势
# ──────────────────────────────────────────────
safe_run(
    "PE-TTM 历史（近3年）",
    lambda: ak.stock_a_pe(symbol=STOCK).tail(10)
)

# ──────────────────────────────────────────────
# 6. 资金流向