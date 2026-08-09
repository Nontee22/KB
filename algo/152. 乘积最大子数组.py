# 152. 乘积最大子数组
#
# 给你一个整数数组 nums ，请你找出数组中乘积最大的非空连续 子数组（该子数组中至少包含一个数字），并返回该子数组所对应的乘积。
# 测试用例的答案是一个 32-位 整数。
# 请注意，一个只包含一个元素的数组的乘积是这个元素的值。
#
# 示例 1:
# 输入: nums = [2,3,-2,4]
# 输出: 6
# 解释: 子数组 [2,3] 有最大乘积 6。

def fun(nums):
    pre_max = pre_min = res = nums[0]
    for i in range(1, len(nums)):
        cur_max = max(pre_max * nums[i], pre_min * nums[i], nums[i])
        cur_min = min(pre_max * nums[i], pre_min * nums[i], nums[i])
        pre_max, pre_min = cur_max, cur_min
        res = max(res, pre_max)
    return res

if __name__ == '__main__':
    nums = [2, 3, -2, 4]
    print(fun(nums))

