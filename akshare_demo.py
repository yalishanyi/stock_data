"""
AKShare A股数据 Demo
覆盖：指数行情、资金流向、融资融券、龙虎榜、分红、新闻、宏观
注意：东方财富系接口(stock_zh_a_hist 等)在国内网络正常可用，
     当前网络环境下该类接口被拒绝，已替换为可用数据源。
"""

import akshare as ak
import pandas as pd

pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 120)
pd.set_option("display.float_format", "{:.4f}".format)

STOCK  = "000001"   # 平安银行
MARKET = "sz"       # sz=深市 sh=沪市
SEP = "\n" + "=" * 60 + "\n"


def show(title, df_or_val):
    print(SEP + f"【{title}】")
    if isinstance(df_or_val, pd.DataFrame):
        print(f"shape: {df_or_val.shape}")
        print(df_or_val.head(5).to_string())
    else:
        print(df_or_val)


# ──────────────────────────────────────────────
# 1. 指数历史行情（沪深指数，163 数据源）
# ──────────────────────────────────────────────
df_index = ak.stock_zh_index_daily(symbol="sh000001")
df_index = df_index.tail(10)
show("上证指数近10日行情", df_index)

df_sz = ak.stock_zh_index_daily(symbol="sz399001")
show("深证成指近10日行情", df_sz.tail(10))

# ──────────────────────────────────────────────
# 2. 个股历史行情（163 数据源，含后复权）
#    stock_zh_a_daily 返回全部历史，用 tail 截取
# ──────────────────────────────────────────────
df_stock = ak.stock_zh_a_daily(symbol=f"{MARKET}{STOCK}", adjust="hfq")
show(f"{STOCK} 后复权历史日K（近10日）", df_stock.tail(10))

# ──────────────────────────────────────────────
# 3. 个股资金流向（近 30 日超/大/中/小单）
# ──────────────────────────────────────────────
df_flow = ak.stock_individual_fund_flow(stock=STOCK, market=MARKET)
show(f"{STOCK} 个股资金流向（近30日）", df_flow.tail(10))

# ──────────────────────────────────────────────
# 4. 大盘整体资金流向
# ──────────────────────────────────────────────
df_mkt = ak.stock_market_fund_flow()
show("大盘资金流（主力/超大/大/中/小单）", df_mkt.tail(10))

# ──────────────────────────────────────────────
# 5. 融资融券（上交所，按日统计）
# ──────────────────────────────────────────────
df_margin = ak.stock_margin_sse(start_date="20240102", end_date="20240110")
show("融资融券（上交所 2024-01）", df_margin)

# ──────────────────────────────────────────────
# 6. 龙虎榜统计（近一月上榜频次）
# ──────────────────────────────────────────────
df_lhb = ak.stock_lhb_stock_statistic_em(symbol="近一月")
show("龙虎榜统计（近一月）", df_lhb.head(10))

# ──────────────────────────────────────────────
# 7. 分红历史
# ──────────────────────────────────────────────
df_div = ak.stock_dividend_cninfo(symbol=STOCK)
show(f"{STOCK} 历史分红", df_div)

# ──────────────────────────────────────────────
# 8. 个股新闻
# ──────────────────────────────────────────────
df_news = ak.stock_news_em(symbol=STOCK)
show(f"{STOCK} 最新新闻", df_news[["新闻标题", "发布时间", "文章来源"]].head(10))

# ──────────────────────────────────────────────
# 9. 宏观 —— 货币供应量 M0/M1/M2
# ──────────────────────────────────────────────
df_m2 = ak.macro_china_money_supply()
show("货币供应量 M0/M1/M2（近10期）", df_m2.tail(10))

print(SEP + "Demo 完成！")
print("可用接口汇总：")
print("  行情: stock_zh_index_daily / stock_zh_a_daily(163源)")
print("  资金: stock_individual_fund_flow / stock_market_fund_flow")
print("  融券: stock_margin_sse")
print("  龙虎: stock_lhb_stock_statistic_em")
print("  分红: stock_dividend_cninfo")
print("  新闻: stock_news_em")
print("  宏观: macro_china_money_supply")
print("\n东方财富系接口(stock_zh_a_hist/财务报表等)需在国内网络使用")
