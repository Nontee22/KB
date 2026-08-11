# 53. 最大子数组和
# 给你一个整数数组 nums ，请你找出一个具有最大和的连续子数组（子数组最少包含一个元素），返回其最大和。
# 子数组是数组中的一个连续部分。
#
# 示例 1：
# 输入：nums = [-2,1,-3,4,-1,2,1,-5,4]
# 输出：6
# 解释：连续子数组 [4,-1,2,1] 的和最大，为 6 。

def fun(nums):
    n = len(nums)
    pre_sum = 0
    res = nums[0]

    for i in range(n):
        pre_sum = max(pre_sum + nums[i], nums[i], 0)
        res = max(res, pre_sum)

    return res

if __name__ == '__main__':
    nums = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
    print(fun(nums))