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
END = "20240110"

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
# safe_run(
#     "A股全市场实时行情（前5条）",
#     lambda: ak.stock_zh_a_spot_em().head(5)
# )

# safe_run(
#     "单股实时报价",
#     lambda: ak.stock_bid_ask_em(symbol=STOCK)
# )

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
# ──────────────────────────────────────────────
safe_run(
    "个股资金流向（近10日）",
    lambda: ak.stock_individual_fund_flow(
        stock=STOCK, market="sh" if STOCK.startswith("6") else "sz")
)

safe_run(
    "行业资金流向（今日）",
    lambda: ak.stock_sector_fund_flow_rank(
        indicator="今日", sector_type="行业资金流向")
)

# ──────────────────────────────────────────────
# 7. 股东信息
# ──────────────────────────────────────────────
safe_run(
    "十大流通股东（最新季）",
    lambda: ak.stock_gdfx_free_top_10_em(symbol=STOCK)
)

safe_run(
    "机构持股变动",
    lambda: ak.stock_institute_hold_detail(stock=STOCK, quarter="20241")
)

# ──────────────────────────────────────────────
# 8. 分红配股
# ──────────────────────────────────────────────
safe_run(
    "历史分红数据",
    lambda: ak.stock_dividend_cninfo(symbol=STOCK)
)

# ──────────────────────────────────────────────
# 9. 龙虎榜 / 大宗交易
# ──────────────────────────────────────────────
safe_run(
    "龙虎榜（近期上榜记录）",
    lambda: ak.stock_lhb_detail_em(
        symbol=STOCK, start_date=START, end_date=END)
)

safe_run(
    "大宗交易（近期）",
    lambda: ak.stock_dzjy_mrmx(type_="买入", date="20241231")
)

# ──────────────────────────────────────────────
# 10. 公告 & 新闻
# ──────────────────────────────────────────────
safe_run(
    "公司公告列表（近10条）",
    lambda: ak.stock_notice_report(symbol=STOCK, date="20241231").head(10)
)

safe_run(
    "个股新闻（近5条）",
    lambda: ak.stock_news_em(symbol=STOCK).head(5)
)

# ──────────────────────────────────────────────
# 11. 宏观数据
# ──────────────────────────────────────────────
safe_run(
    "CPI 月度数据（近10条）",
    lambda: ak.macro_china_cpi_monthly().tail(10)
)

safe_run(
    "M2 货币供应量",
    lambda: ak.macro_china_money_supply().tail(10)
)

safe_run(
    "上证指数历史行情",
    lambda: ak.stock_zh_index_daily(symbol="sh000001").tail(5)
)

# ──────────────────────────────────────────────
# 12. 股票列表 & 基本信息
# ──────────────────────────────────────────────
safe_run(
    "A股全部股票列表（前5条）",
    lambda: ak.stock_info_a_code_name().head(5)
)

safe_run(
    "股票基本信息（上市日期、总股本等）",
    lambda: ak.stock_individual_info_em(symbol=STOCK)
)

print(f"{SEPARATOR}Demo 完成！")
