"""
拉取全量A股指数列表，落到 data/index_list.csv。

数据源优先级：
  1. index_csindex_all()  → 中证指数官网，2000+ 条（含中证2000、中证A50、红利低波100）
  2. index_stock_info()   → 中证指数备用，726 条

北证50（899050）由北交所发布，不在中证体系内，单独追加。

字段：index_code, display_name, publish_date

增量逻辑：
  - 对比已有文件，打印新增/移除/改名 diff
  - 保存最新快照

运行方式：
  python3 fetch_index_list.py
"""

import akshare as ak
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

INDEX_LIST_FILE = DATA_DIR / "index_list.csv"

# 北交所指数单独追加（不在中证体系内）
EXTRA_INDICES = [
    {"index_code": "899050", "display_name": "北证50", "publish_date": "2022-11-21"},
    {"index_code": "899001", "display_name": "北证综指", "publish_date": "2022-04-29"},
]


def fetch_index_list() -> pd.DataFrame:
    df = None

    print(">>> 拉取全量指数列表（中证指数 index_csindex_all）...")
    try:
        raw = ak.index_csindex_all()
        df = raw[["指数代码", "指数简称", "发布时间"]].copy()
        df.columns = ["index_code", "display_name", "publish_date"]
        print(f"    index_csindex_all: {len(df)} 条")
    except Exception as e:
        print(f"    [SKIP] index_csindex_all 失败: {e}")

    if df is None:
        print(">>> 降级到 index_stock_info()...")
        try:
            raw = ak.index_stock_info()
            raw.columns = ["index_code", "display_name", "publish_date"]
            df = raw.copy()
            print(f"    index_stock_info: {len(df)} 条")
        except Exception as e:
            print(f"    [FAIL] index_stock_info 也失败: {e}")
            return pd.DataFrame(columns=["index_code", "display_name", "publish_date"])

    # 追加北交所等非中证指数
    extra_df = pd.DataFrame(EXTRA_INDICES)
    existing_codes = set(df["index_code"].astype(str))
    extra_new = extra_df[~extra_df["index_code"].isin(existing_codes)]
    if not extra_new.empty:
        df = pd.concat([df, extra_new], ignore_index=True)
        print(f"    追加非中证指数: {len(extra_new)} 条（北交所等）")

    df["index_code"] = df["index_code"].astype(str).str.zfill(6)
    df.sort_values("index_code", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def diff_and_save(new_df: pd.DataFrame) -> pd.DataFrame:
    if INDEX_LIST_FILE.exists():
        old_df = pd.read_csv(INDEX_LIST_FILE, dtype={"index_code": str})
        old_df["index_code"] = old_df["index_code"].str.zfill(6)
        old_codes = set(old_df["index_code"])
        new_codes = set(new_df["index_code"])

        added   = new_codes - old_codes
        removed = old_codes - new_codes

        old_map = old_df.set_index("index_code")["display_name"].to_dict()
        new_map = new_df.set_index("index_code")["display_name"].to_dict()
        renamed = {
            code: (old_map[code], new_map[code])
            for code in old_codes & new_codes
            if old_map.get(code) != new_map.get(code)
        }

        if added or removed or renamed:
            print(f"[diff] 新增 {len(added)} 条，移除 {len(removed)} 条，改名 {len(renamed)} 条")
            for code in sorted(added)[:20]:
                print(f"  + {code} {new_map.get(code, '')}")
            if len(added) > 20:
                print(f"  ... 共 {len(added)} 条新增")
            for code in sorted(removed)[:10]:
                print(f"  - {code} {old_map.get(code, '')}")
            for code, (old_name, new_name) in sorted(renamed.items()):
                print(f"  ~ {code} {old_name} → {new_name}")
        else:
            print("[diff] 无变化")
    else:
        print("[new]  首次写入")

    new_df.to_csv(INDEX_LIST_FILE, index=False, encoding="utf-8-sig")
    print(f"[saved] index_list.csv  {len(new_df)} 条 → {INDEX_LIST_FILE}")
    return new_df


if __name__ == "__main__":
    try:
        df = fetch_index_list()
        diff_and_save(df)
        print("\n--- 前10条 ---")
        print(df.head(10).to_string(index=False))
    except Exception as e:
        print(f"[FAIL] {e}")
