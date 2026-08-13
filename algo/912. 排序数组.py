# 912. 排序数组
# 给你一个整数数组 nums，请你将该数组升序排列。
# 你必须在 不使用任何内置函数 的情况下解决问题，时间复杂度为 O(nlog(n))，并且空间复杂度尽可能小。
#
# 示例 1：
# 输入：nums = [5,2,3,1]
# 输出：[1,2,3,5]
# 解释：数组排序后，某些数字的位置没有改变（例如，2 和 3），而其他数字的位置发生了改变（例如，1 和 5）。
import random

def fun(nums, left, right):
    if left >= right:
        return

    rand = random.randint(left, right)
    p = nums[rand]

    lt = left
    i = left
    gt = right

    while i <= gt:
        if nums[i] < p:
            nums[lt], nums[i] = nums[i], nums[lt]
            i += 1
            lt += 1
        elif nums[i] > p:
            nums[gt], nums[i] = nums[i], nums[gt]
            gt -= 1
        else:
            i += 1

    fun(nums, left, lt - 1)
    fun(nums, gt + 1, right)

if __name__ == '__main__':
    nums = [5, 2, 3, 1]
    fun(nums, 0, len(nums) - 1)
    print(nums)