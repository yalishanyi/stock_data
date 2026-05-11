"""
拉取A股股票列表，落到 data/ 目录，支持增量更新。

增量逻辑：
  - 每个交易所 CSV 已存在时，对比新旧数据，检测新增股票和名称变更
  - 新增/改名股票打印 diff，最终保存最新快照
  - all 文件由各交易所最新数据合并生成

覆盖：
  - 上交所：主板A股、科创板（sse.com.cn）
  - 深交所：主板、创业板（szse.cn，国内网络）
  - 北交所（bse.cn，国内网络）
  - 退市：沪市、深市

运行方式：
  python3 fetch_stock_list.py
"""

import akshare as ak
import pandas as pd
import requests
from pathlib import Path
from datetime import date

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

SSE_HEADERS = {
    "Host": "query.sse.com.cn",
    "Referer": "https://www.sse.com.cn/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


def save(df: pd.DataFrame, filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"    [saved] {filename}  {len(df)} 条")
    return df


def diff_and_save(new_df: pd.DataFrame, filename: str, key: str = "code") -> pd.DataFrame:
    """对比已有 CSV 与新数据，打印 diff，保存最新快照。"""
    path = DATA_DIR / filename
    if path.exists():
        old_df = pd.read_csv(path, dtype={key: str})
        old_codes = set(old_df[key].str.zfill(6))
        new_codes = set(new_df[key].str.zfill(6))

        added   = new_codes - old_codes
        removed = old_codes - new_codes

        # 检测改名
        old_map = old_df.set_index(key)["name"].to_dict()
        new_map = new_df.set_index(key)["name"].to_dict()
        renamed = {
            code: (old_map[code], new_map[code])
            for code in old_codes & new_codes
            if old_map.get(code) != new_map.get(code)
        }

        if added or removed or renamed:
            print(f"    [diff] 新增 {len(added)} 条，移除 {len(removed)} 条，改名 {len(renamed)} 条")
            for code in sorted(added):
                name = new_map.get(code, "")
                print(f"      + {code} {name}")
            for code in sorted(removed):
                name = old_map.get(code, "")
                print(f"      - {code} {name}")
            for code, (old_name, new_name) in sorted(renamed.items()):
                print(f"      ~ {code} {old_name} → {new_name}")
        else:
            print(f"    [diff] 无变化")
    else:
        print(f"    [new]  首次写入")

    return save(new_df, filename)


# ─────────────────────────────────────────────────
# 上交所：主板A股 + 科创板
# ─────────────────────────────────────────────────
def fetch_sh() -> pd.DataFrame:
    print(">>> 上交所主板A股...")
    df_main = ak.stock_info_sh_name_code(symbol="主板A股")
    df_main["board"] = "主板"

    print(">>> 上交所科创板...")
    df_star = ak.stock_info_sh_name_code(symbol="科创板")
    df_star["board"] = "科创板"

    df = pd.concat([df_main, df_star], ignore_index=True)
    df.insert(0, "exchange", "SH")
    df.rename(columns={
        "证券代码": "code", "证券简称": "name",
        "证券全称": "full_name", "公司简称": "short_name",
        "公司全称": "company_full_name", "上市日期": "list_date",
    }, inplace=True)
    return diff_and_save(df, "stock_list_sh.csv")


# ─────────────────────────────────────────────────
# 深交所：主板 + 创业板（szse.cn，国内网络）
# ─────────────────────────────────────────────────
def fetch_sz() -> pd.DataFrame:
    print(">>> 深交所A股列表...")
    df = ak.stock_info_sz_name_code(symbol="A股列表")
    df.insert(0, "exchange", "SZ")
    df.rename(columns={
        "板块": "board", "A股代码": "code", "A股简称": "name",
        "A股上市日期": "list_date", "A股总股本": "total_shares",
        "A股流通股本": "float_shares", "所属行业": "industry",
    }, inplace=True)
    return diff_and_save(df, "stock_list_sz.csv")


# ─────────────────────────────────────────────────
# 北交所（bse.cn，国内网络）
# ─────────────────────────────────────────────────
def fetch_bj() -> pd.DataFrame:
    print(">>> 北交所股票列表...")
    df = ak.stock_info_bj_name_code()
    df.insert(0, "exchange", "BJ")
    df["board"] = "北交所"
    df.rename(columns={
        "证券代码": "code", "证券简称": "name",
        "上市日期": "list_date", "所属行业": "industry",
        "总股本": "total_shares", "流通股本": "float_shares",
        "地区": "province",
    }, inplace=True)
    return diff_and_save(df, "stock_list_bj.csv")


# ─────────────────────────────────────────────────
# 退市：沪市（直接调 SSE API）
# ─────────────────────────────────────────────────
def fetch_delist_sh() -> pd.DataFrame:
    print(">>> 沪市退市股票（SSE 接口）...")
    params = {
        "sqlId": "COMMON_SSE_CP_GPJCTPZ_GPLB_GP_L",
        "isPagination": "true",
        "STOCK_TYPE": "1,2,8",
        "COMPANY_STATUS": "3",
        "type": "inParams",
        "pageHelp.cacheSize": "1",
        "pageHelp.beginPage": "1",
        "pageHelp.pageSize": "2000",
        "pageHelp.pageNo": "1",
        "pageHelp.endPage": "1",
    }
    r = requests.get(
        "https://query.sse.com.cn/commonQuery.do",
        params=params, headers=SSE_HEADERS, timeout=15,
    )
    data = r.json()["result"]
    df = pd.DataFrame(data)
    df = df[["COMPANY_CODE", "COMPANY_ABBR", "LIST_DATE", "DELIST_DATE",
             "CSRC_CODE_DESC", "AREA_NAME_DESC"]].copy()
    df.columns = ["code", "name", "list_date", "delist_date", "industry", "province"]
    df.insert(0, "exchange", "SH")
    df.insert(3, "status", "退市")
    return diff_and_save(df, "stock_list_sh_delist.csv")


# ─────────────────────────────────────────────────
# 退市：深市（szse.cn，国内网络）
# ─────────────────────────────────────────────────
def fetch_delist_sz() -> pd.DataFrame:
    print(">>> 深市退市股票...")
    df = ak.stock_info_sz_delist()
    df.rename(columns={
        "证券代码": "code", "证券简称": "name",
        "上市日期": "list_date", "终止上市日期": "delist_date",
    }, inplace=True)
    df.insert(0, "exchange", "SZ")
    df.insert(0, "status", "退市")
    return diff_and_save(df, "stock_list_sz_delist.csv")


# ─────────────────────────────────────────────────
# 合并在市 → stock_list_listed_all.csv
# ─────────────────────────────────────────────────
def merge_listed(frames: list[pd.DataFrame]) -> pd.DataFrame:
    cols = ["exchange", "code", "name", "list_date", "board", "status"]
    slices = []
    for df in frames:
        df = df.copy()
        if "status" not in df.columns:
            df["status"] = "在市"
        slices.append(df[[c for c in cols if c in df.columns]])
    df_all = pd.concat(slices, ignore_index=True)
    df_all.sort_values("code", inplace=True)
    df_all.reset_index(drop=True, inplace=True)
    return save(df_all, "stock_list_listed_all.csv")


# ─────────────────────────────────────────────────
# 合并退市 → stock_list_delist_all.csv
# ─────────────────────────────────────────────────
def merge_delisted(frames: list[pd.DataFrame]) -> pd.DataFrame:
    cols = ["exchange", "code", "name", "list_date", "delist_date", "status"]
    slices = [df[[c for c in cols if c in df.columns]] for df in frames]
    df_all = pd.concat(slices, ignore_index=True)
    df_all.sort_values("code", inplace=True)
    df_all.reset_index(drop=True, inplace=True)
    return save(df_all, "stock_list_delist_all.csv")


# ─────────────────────────────────────────────────
# 全量合并 → stock_list_all.csv
# ─────────────────────────────────────────────────
def merge_all(listed_df: pd.DataFrame, delisted_df: pd.DataFrame) -> pd.DataFrame:
    cols = ["exchange", "code", "name", "list_date", "status"]
    df_all = pd.concat([
        listed_df[[c for c in cols if c in listed_df.columns]],
        delisted_df[[c for c in cols if c in delisted_df.columns]],
    ], ignore_index=True)
    df_all.sort_values("code", inplace=True)
    df_all.reset_index(drop=True, inplace=True)
    return save(df_all, "stock_list_all.csv")


if __name__ == "__main__":
    listed, delisted = [], []

    for label, fn in [("上交所", fetch_sh), ("深交所", fetch_sz), ("北交所", fetch_bj)]:
        try:
            listed.append(fn())
        except Exception as e:
            print(f"    [SKIP] {label} 获取失败（可能需国内网络）: {e}\n")

    for label, fn in [("沪市退市", fetch_delist_sh), ("深市退市", fetch_delist_sz)]:
        try:
            delisted.append(fn())
        except Exception as e:
            print(f"    [SKIP] {label} 获取失败: {e}\n")

    empty = pd.DataFrame(columns=["exchange", "code", "name", "list_date", "status"])
    listed_df   = merge_listed(listed)     if listed   else empty.copy()
    delisted_df = merge_delisted(delisted) if delisted else empty.copy()
    merge_all(listed_df, delisted_df)

    print(f"\n完成，data/ 目录文件：")
    for f in sorted(DATA_DIR.glob("stock_list*.csv")):
        print(f"  {f.name:<35} {f.stat().st_size // 1024:>4} KB")
