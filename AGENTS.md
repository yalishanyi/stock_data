# AGENTS.md — AI 编码规范与项目说明

本文件供 AI Agent（Claude、Codex 等）在参与本项目时遵守。

---

## 项目简介

A股数据拉取与分析工具，使用 AKShare 作为数据源，覆盖：
- 股票列表（沪/深/北交所 在市 + 退市）
- 历史价格（日K、月K，后复权）
- 资金流向、融资融券、龙虎榜、分红、新闻、宏观数据

---

## 目录结构

```
stock_demo/
├── AGENTS.md                  # 本文件
├── README.md
├── .gitignore
├── bucang/                    # 补仓策略相关脚本（独立业务模块）
│   ├── bc.py                  # 读取 longwin.json，分析持仓涨跌
│   ├── bc_new.py              # 拉取龙赢基金数据，分析波段策略
│   ├── cunqian.py             # 储蓄/财务自由测算
│   ├── longwin.json           # 龙赢持仓数据（本地缓存）
│   └── test.py                # 临时计算脚本
├── history/                   # 数据拉取脚本（所有拉取脚本均在此）
│   ├── fetch_stock_list.py    # 拉取全市场股票列表 → data/stock_list_*.csv
│   ├── fetch_price.py         # 拉取历史价格（日K + 月K）→ data/price/
│   ├── fetch_data.py          # 拉取行情/资金/宏观等综合数据
│   ├── akshare_demo.py        # AKShare 接口探索 demo
│   └── history_data.py        # 历史数据相关工具
└── data/                      # 数据目录（git ignore，不提交）
    ├── stock_list_listed_all.csv   # 在市股票全量（沪+深+北合并）
    ├── stock_list_delist_all.csv   # 退市股票全量（沪退+深退合并）
    ├── stock_list_all.csv          # 全量（在市+退市）
    ├── stock_list_sh.csv           # 上交所（主板+科创板）
    ├── stock_list_sz.csv           # 深交所（主板+创业板）
    ├── stock_list_bj.csv           # 北交所
    ├── stock_list_sh_delist.csv    # 沪市退市
    ├── stock_list_sz_delist.csv    # 深市退市
    └── price/
        ├── daily/{code}.csv        # 个股日K（后复权）
        └── monthly/{code}.csv      # 个股月K末日收盘价
```

---

## 数据规范

### 股票列表统一字段

| 字段 | 说明 |
|---|---|
| `exchange` | 交易所：`SH` / `SZ` / `BJ` |
| `code` | 6位股票代码（补零对齐） |
| `name` | 证券简称 |
| `list_date` | 上市日期 |
| `delist_date` | 退市日期（退市表专有） |
| `board` | 板块：主板 / 科创板 / 创业板 / 北交所 |
| `status` | `在市` / `退市` |

### 价格数据字段

日K（`data/price/daily/{code}.csv`）：`date, open, high, low, close, volume`，后复权。

月K（`data/price/monthly/{code}.csv`）：`date, close_monthly`，每月最后一个交易日收盘价。

### 163数据源股票代码格式

`{前缀}{6位code}`，前缀规则：`SH→sh`，`SZ→sz`，`BJ→bj`。

---

## AI 编码注意事项

### 目录规范
- **数据拉取脚本统一放在 `history/` 目录**，不放根目录。
- `bucang/` 是独立业务模块，不放数据拉取逻辑。

### 路径写法
- 所有脚本必须用 `Path(__file__)` 计算路径，禁止硬编码相对路径。
- `history/` 下的脚本：`DATA_DIR = Path(__file__).parent.parent / "data"`
- `bucang/` 下的脚本：`DATA_DIR = Path(__file__).parent.parent / "data"`，本地 JSON 文件用 `Path(__file__).parent / "xxx.json"`

```python
# 正确
from pathlib import Path
DATA_DIR = Path(__file__).parent.parent / "data"

# 错误（依赖工作目录，换目录运行会出错）
open("data/xxx.csv")
open("bucang/longwin.json")
```

### 列名规范
- AKShare 返回中文列名时，必须 rename 为英文统一字段名（见上方数据规范表）。
- 新增交易所/数据源时，对照现有 rename 逻辑保持一致。

### 网络容错
- 数据拉取脚本中，每个数据源用 `try/except` 包裹，失败打印原因并继续，不中断整体流程。
- 东方财富（eastmoney.com）、深交所（szse.cn）、北交所（bse.cn）在国际网络下不可达，需要 `[SKIP]` 提示。
- 上交所（sse.com.cn）和网易163在当前网络可用。

### 增量模式
- 价格拉取脚本检查文件是否已存在，存在则跳过，支持断点续跑。
- 全量拉取时在请求间加 `time.sleep(0.3)` 避免触发限流。

### 不要做的事
- 不修改 `data/` 目录下已有的 CSV 文件结构（列名、顺序）。
- 不在根目录新建数据拉取脚本。
- 不把 `data/` 目录提交到 git（已在 `.gitignore` 中）。
- 不删除 `history/` 下已有脚本，只新增或修改。
