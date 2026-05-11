
# nums1=[1]
# print(nums1[0:0])

# print(nums1[1:1])

# nums1=[1,2,3,4,5,6]
# nums1=[1]
# print(nums1[1:0])


x = 0.8
ratio_one = 0.8**(1/10)
print(ratio_one)

start = 1

for i in range(10):
    start = start*ratio_one
    print(f"第{i+1}次买入")
    # print(start)
    print(round((1-start)*100, 1))
    print(round(start*11920))


"""
结果：
第1次买入
2.2
11657
第2次买入
4.4
11400
第3次买入
6.5
11148
第4次买入
8.5
10902
第5次买入
10.6
10662
第6次买入
12.5
10426
第7次买入
14.5
10196
第8次买入
16.3
9971
第9次买入
18.2
9751
第10次买入
20.0
9536                                                                                                                                          ──(三,1224)─┘
"""
