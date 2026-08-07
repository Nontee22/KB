# 300. 最长递增子序列
# 给你一个整数数组 nums ，找到其中最长严格递增子序列的长度。
# 子序列 是由数组派生而来的序列，删除（或不删除）数组中的元素而不改变其余元素的顺序。
# 例如，[3,6,2,7] 是数组 [0,3,1,6,2,2,7] 的子序列。
#
# 示例 1：
# 输入：nums = [10,9,2,5,3,7,101,18]
# 输出：4
# 解释：最长递增子序列是 [2,3,7,101]，因此长度为 4 。

from functools import cache


def fun(nums):
    # n = len(nums)
    #
    # @cache
    # def dfs(i):
    #     if i < 0:
    #         return 0
    #     res = 1
    #     for j in range(i):
    #         if nums[j] < nums[i]:
    #             res = max(res, dfs(j) + 1)
    #     return res
    #
    # if n == 0:
    #     return 0
    # return max(dfs(k) for k in range(n))

    n = len(nums)
    if n == 0:
        return 0

    f = [1] * n
    for i in range(n):
        for j in range(i):
            if nums[j] < nums[i]:
                f[i] = max(f[i], f[j] + 1)

    return max(f)


if __name__ == '__main__':
    nums = [10, 9, 2, 5, 3, 7, 101, 18]
    print(fun(nums))