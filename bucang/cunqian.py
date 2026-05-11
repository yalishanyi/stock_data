ratios = [0.04, 0.08, 0.105]
# 长期来说股市的收益率其实是6.6+通胀3.5，大约10%
# ratios = [0.08]

nianshouru = 61.7
nianzhichu = 24
nianjieyu = nianshouru-nianzhichu

for ratio in ratios:
    touzibenjin = 77.1
    otherbenjin = 76

    touzitouru = nianjieyu
    othertouru = 0
    ziyou = False
    for i in range(7):
        touzibenjin = (touzibenjin+touzibenjin+touzitouru) / \
            2*(ratio)+touzibenjin+touzitouru
        print("收益率:{}，第{}年过去，投资本金为{}".format(ratio, i+1, touzibenjin))
        zongbenjin = touzibenjin+othertouru*(i+1)+otherbenjin
        print("收益率:{}，第{}年过去，总本金为{}".format(ratio, i+1, zongbenjin))
        if zongbenjin*ratio >= nianzhichu-3.6 and not ziyou:
            ziyou = True
            print("你自由了")
print("1年后投资124W，总本金200W，自由后---------------------------------------")
print("自由后---------------------------------------")
print("2年后投资177W，总本金253W，自由后---------------------------------------")
print("自由后---------------------------------------")


for ratio in ratios:
    # 年huaxiao
    nianhuaxiao = 20.4
    # 假设通胀率年3.5%，结论，考虑通胀的情况下，8%收益率或者300W是不够的，10%才勉强够，且会在30W后本金大量贬值，变成年支出的4倍，大约贬值一半多
    # 所以这种情况下，收益率需要达到3.5%通胀+7%支出=10.5%
    # 所以财务自由只有2种方式 1.增加本金，减少支出，最终减少支出率，控制在4.5%以下。2.增加收益率，控制在通胀+支出率之上
    # 6.5%的支出率需要450W，也就是最好是干6年，赚到457W。也就是2033年，那年我36了。
    # 如果换一份工作呢，这个工作需要多少的收入？年收入7.5W，也就是月薪6千。
    tongzhanglv = 1.035

    # nianhuaxiao=20
    qiquan = 27
    touzibenjin = 177+qiquan
    zongbenjin = 253

    # 假设500W，在8%的收益下基本是够的，而且本金和通胀速度差不多，仍是支出的25倍
    # zongbenjin = 500
    # touzibenjin = zongbenjin

    otherbenjin = zongbenjin-touzibenjin

    touzitouru = 0
    othertouru = 0
    for i in range(30):
        nianhuaxiao = nianhuaxiao*tongzhanglv
        # print("收益率:{}，第{}年过去，支出为{}".format(ratio, i+1, nianhuaxiao))
        touzibenjin = touzibenjin*(1+ratio)+touzitouru-nianhuaxiao
        print("收益率:{}，第{}年过去，投资本金为{}".format(ratio, i+1, touzibenjin))
        zongbenjin = touzibenjin+otherbenjin
        print("收益率:{}，第{}年过去，总本金为{}".format(ratio, i+1, zongbenjin))


# 理想情况，年支出20W的十倍200W，还是要赚点钱，大约需要赚年7.2W，月6K。还需要干1年
# 合理情况下，年支出20W的25倍500W。还需要干9年
