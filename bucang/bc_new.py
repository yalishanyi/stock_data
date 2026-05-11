"""
curl 'https://qieman.com/pmdj/v2/long-win/plan?prodCode=LONG_WIN' \
  -H 'Accept: application/json' \
  -H 'Accept-Language: zh-CN,zh;q=0.9' \
  -H 'Authorization: Bearer null' \
  -H 'Cache-Control: no-store' \
  -H 'Connection: keep-alive' \
  -H 'Referer: https://qieman.com/longwin/compositions/LONG_WIN' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sensors-anonymous-id: 19818772fd41376-0a22c8720f07a8-17525636-1930176-19818772fd5174a' \
  -H 'x-request-id: albus.93978B917CA1544CFAFA' \
  -H 'x-sign: 17637995542512F9C4B76000EE8849083477AF8B062B0'
"""

import time
import requests
from datetime import datetime
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

now = datetime.now()
end = now.strftime("%Y-%m-%d")
nowTs = time.time()*1000

sign = '1778076814920176E1C6B88E3BCA78A47129355865563'

headers = {
    'Accept': 'application/json',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Authorization': 'Bearer null',
    'Cache-Control': 'no-store',
    'Connection': 'keep-alive',
    'Referer': 'https://qieman.com/longwin/compositions/LONG_WIN',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sensors-anonymous-id': '19818772fd41376-0a22c8720f07a8-17525636-1930176-19818772fd5174a',
    'x-request-id': 'albus.93978B917CA1544CFAFA',
    'x-sign': sign
}

boduan = False
save_in_file = True


def save_file(resp, file_name):
    with open(DATA_DIR / f"{file_name}.json", mode="w") as f:
        json.dump(resp, f, indent=4, ensure_ascii=False)


def get_file(file_name):
    resp = {}
    with open(DATA_DIR / f"{file_name}.json", mode="r") as f:
        resp = json.load(f)
    return resp


def get_plan(plan_name):
    if save_in_file:
        # 被waf拦截了
        time.sleep(5)
        r = requests.get(
            f'https://qieman.com/pmdj/v2/long-win/plan?prodCode={plan_name}', headers=headers)
        resp = r.json()
        save_file(resp, plan_name)
    else:
        resp = get_file(plan_name)
    return resp


def get_fund_nav_history(fundCode):
    if save_in_file:
        time.sleep(3)
        r = requests.get(
            f'https://qieman.com/pmdj/v1/funds/{fundCode}/nav-history?start=2015-07-01&end={end}', headers=headers)
        resp = r.json()
        save_file(resp, fundCode)
    else:
        resp = get_file(fundCode)
    return resp


def get_boduan_res(fundCode):
    resp = get_fund_nav_history(fundCode)
    max_nav = 0
    max_date = None
    for nh in resp:
        nav = nh["adjNav"]
        date = nh["date"]
        # 过滤近一年达到最大价格的
        if date > nowTs-360*24*3600*1000:
            continue
        # 获取最大的净值的那天
        if nav >= max_nav:
            max_nav = nav
            max_date = date

    # 从最大净值跌了5%开始做波段
    buy_nav = max_nav*0.95
    buy_list = []
    # 最大持仓份数
    max_buy_count = 0
    max_lirun = -1000
    min_lirun = 1000
    for nh in resp:
        nav = nh["adjNav"]
        date = nh["date"]
        if date <= max_date:
            continue
        # 低于买入价格，进行买入
        if nav <= buy_nav:
            buy_list.append({
                # 买入预期价格
                "buy_nav": buy_nav,
                # 买入实际价格
                "buy_nav_real": nav,
                # 买入时间
                "buy_date": date,
                # 预期卖出价格
                "sale_nav": buy_nav*1.05,
            })
            # 买入预期价格，往下一网
            buy_nav = buy_nav*0.95
        # 高于卖出价格，进行卖出
        for buy_one in buy_list:
            if "sale_nav_real" in buy_one:
                continue
            if nav >= buy_one["sale_nav"]:
                # 触发卖出
                buy_one.update({
                    "sale_nav_real": nav,
                    "sale_date": date,
                    # 持股时间
                    "cost_time": date-buy_one["buy_date"],
                    # 利润率
                    "ratio": (nav-buy_one["buy_nav_real"])/buy_one["buy_nav_real"],
                })
        # 计算成本、回撤
        # 最大持仓份数，相当于最大投入份数
        max_buy_count = max(max_buy_count, sum(
            [1 for x in buy_list if "sale_nav_real" not in x]))
        # 回撤，相当于最大亏损，单位为1份
        lirun = 0
        for buy_one in buy_list:
            if "sale_nav_real" in buy_one:
                # 已经卖出的，直接计算利润
                # 暂时不考虑留利润
                lirun += buy_one["ratio"]
            else:
                lirun += (nav-buy_one["buy_nav_real"])/buy_one["buy_nav_real"]
        max_lirun = max(max_lirun, lirun)
        min_lirun = min(min_lirun, lirun)

    return {
        "buy_list": buy_list,
        "max_buy_count": max_buy_count,
        "max_lirun": max_lirun,
        "min_lirun": min_lirun,
    }


def sort_price(plan_name="LONG_WIN"):
    resp = get_plan(plan_name)
    compPriceList = []
    # resp['composition'][0]['compList'][0]
    if boduan:
        print(f"{'计划名称':<10} {plan_name} 波段计算")
        print(f"{'品种':<10} {'最大份数':<10} {'最大利润':<10} {'最大回撤':<10} ")

    for composition in resp['composition']:
        for comp in composition['compList']:
            if 'fund' not in comp:
                continue
            fundName = comp['fund']['fundName']
            fundCode = comp['fund']['fundCode']
            planUnit = comp['planUnit']
            # 中文名称简称
            variety = comp['variety']
            # 当前价格
            nowPrice = comp['nav']
            # 购买价格
            buyPrice = comp.get('unitValue')
            if not nowPrice or not buyPrice:
                continue
            # 涨幅
            changeRate = nowPrice/buyPrice-1

            # 历史波段信息
            boduan_res = {}
            if boduan:
                boduan_res = get_boduan_res(fundCode)
            comPrice = {
                'fundName': fundName,
                'fundCode': fundCode,
                'variety': variety,
                'nowPrice': nowPrice,
                'buyPrice': buyPrice,
                'changeRate': changeRate,
                'planUnit': planUnit
            }
            comPrice.update(boduan_res)
            compPriceList.append(comPrice)
            xingjiabi = 0
            if comPrice.get('min_lirun'):
                xingjiabi = comPrice['max_lirun']/comPrice['min_lirun']
            # print(f"{comPrice['variety']} 最大份数：{comPrice['max_buy_count']} 最大利润{comPrice['max_lirun']:.2%} 最大跌幅：{comPrice['min_lirun']:.2%} 最大利润/最大跌幅：{xingjiabi}")

    # 按涨幅倒序
    compPriceList.sort(key=lambda x: x['changeRate'], reverse=False)
    # 打印结果
    print(f"{'计划名称':<10} {plan_name}")
    print(f"{'涨幅':<10} {'基金名称':<20} {'基金代码':<10} {'品种':<10} {'当前价格':<10} {'购买价格':<10} {'计划份数':<10}")
    for compPrice in compPriceList:
        print(f"{compPrice['changeRate']:.2%} {compPrice['variety']} {compPrice['fundName']}({compPrice['fundCode']}) 当前价格: {compPrice['nowPrice']} 购买价格: {compPrice['buyPrice']} {compPrice['planUnit']}")


def main():
    sort_price('LONG_WIN')
    sort_price('LONG_WIN_S')


if __name__ == '__main__':
    main()
