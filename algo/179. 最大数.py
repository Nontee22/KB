# 179. 最大数
# 给定一组非负整数 nums，重新排列每个数的顺序（每个数不可拆分）使之组成一个最大的整数。
# 注意：输出结果可能非常大，所以你需要返回一个字符串而不是整数。
#
# 示例 1：
# 输入：nums = [10,2]
# 输出："210"

from functools import cmp_to_key


def fun(nums):
    def f(a, b):
        if a + b > b + a:
            return -1
        elif a + b < b + a:
            return 1
        else:
            return 0
    arr = list(map(str, nums))
    arr.sort(key = cmp_to_key(f))

    if arr and arr[0] == '0':
        return 0
    return ''.join(arr)

if __name__ == '__main__':
    nums = [10, 2]
    print(fun(nums))