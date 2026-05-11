

import json
from pathlib import Path

v_list = []
with open(Path(__file__).parent / "longwin.json", mode="r") as f:
    longwin = json.load(f)
    for composition in longwin["composition"]:
        for compList in composition["compList"]:
            if "nav" not in compList:
                continue
            now_value = compList["nav"]
            get_value = compList["unitValue"]
            zhangfu = 0

            if now_value and get_value:
                zhangfu = (now_value-get_value)/get_value
            if not zhangfu:
                continue

            zhangfu = round(zhangfu*100, 2)
            zhangfu = zhangfu
            fundCode, fundName = None, None
            if "fund" in compList:
                fundCode = compList["fund"]["fundCode"]
                fundName = compList["fund"]["fundName"]
                variety = compList["variety"]
                planUnit = f"份数：{compList['planUnit']}"

            v_list.append([zhangfu, fundName, fundCode, variety, planUnit])


v_list = sorted(v_list, key=lambda x: x[0])
for v in v_list:
    v[0] = f"{v[0]}%"
    print(" ".join(v))


def get_nav_his(fundCode):
    import requests
    import datetime

    today = datetime.date.today()
    url = f"https://qieman.com/pmdj/v1/funds/{fundCode}/nav-history?start=2015-07-01&end={today}"

    payload = {}
    headers = {
        'Accept': 'application/json',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Authorization': 'Bearer null',
        'Cache-Control': 'no-store',
        'Connection': 'keep-alive',
        'Referer': 'https://qieman.com/longwin/funds/100032?prodCode=LONG_WIN',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sensors-anonymous-id': '190de024c6419d-037bc4b9227c082-19525637-2007040-190de024c65ce8',
        'x-request-id': 'albus.9AB0A5F766C83C8F5F66',
        # 这个鉴权信息需要更新
        'x-sign': '1766157385221FBF714278B42FE6C6E08E4FD6F66754B',
        'Cookie': 'acw_tc=ac11000117421256766992325e0110f210996340a68462c9add2830e263c25'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


print("计算比高点低的最多的项目----------------")
# 计算比高点低的最多的项目


def get_most_low():
    for v in v_list:
        print(v)
        zhangfu, fundName, fundCode, variety = v[:4]
        nav_his = get_nav_his(fundCode)
        new_nav = nav_his[-1]["nav"]
        nav_his = sorted(nav_his, key=lambda x: x["nav"])
        max_nav = nav_his[-1]["nav"]
        max_date = nav_his[-1]["date"]

        print(nav_his[-1])
        nav_his = [x for x in nav_his if x["date"] >= max_date]
        min_nav = nav_his[0]["nav"]

        max_low_diefu = (max_nav-new_nav)/max_nav
        max_low_diefu = round(max_low_diefu, 4)
        v.append(max_low_diefu)

        v.append(round((max_nav-min_nav)/max_nav, 4))
        print(f"跌了：{v[-1]*100}%  {v[0]} {v[1]} {v[2]}  {v[3]} ")
        pass

    pass


get_most_low()
print("计算当前比高点跌的最多的项目----------------排序后")
v_list = sorted(v_list, key=lambda x: x[5], reverse=True)
for v in v_list:
    print(f"跌了：{v[5]*100}%  {v[0]} {v[1]} {v[2]}  {v[3]}")

print("计算比最低点比高点跌的最多的项目----------------排序后")

v_list = sorted(v_list, key=lambda x: x[6], reverse=True)
for v in v_list:
    print(f"跌了：{v[6]*100}%  {v[0]} {v[1]} {v[2]}  {v[3]}")
