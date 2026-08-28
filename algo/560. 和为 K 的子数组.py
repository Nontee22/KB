# 560. 和为 K 的子数组
# 给你一个整数数组 nums 和一个整数 k ，请你统计并返回 该数组中和为 k 的子数组的个数 。
# 子数组是数组中元素的连续非空序列。
#
# 示例 1：
# 输入：nums = [1,1,1], k = 2
# 输出：2

from collections import defaultdict


def fun(nums, k):
    dic = defaultdict(int)
    dic[0] = 1
    res = 0
    pre_sum = 0

    for x in nums:
        pre_sum += x
        res += dic[pre_sum - k]
        dic[pre_sum] += 1

    return res

if __name__ == '__main__':
    nums = [1, 1, 1]
    k = 2
    print(fun(nums, k))
