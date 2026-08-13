# 215. 数组中的第K个最大元素
# 给定整数数组 nums 和整数 k，请返回数组中第 k 个最大的元素。
# 请注意，你需要找的是数组排序后的第 k 个最大的元素，而不是第 k 个不同的元素。
# 你必须设计并实现时间复杂度为 O(n) 的算法解决此问题。
#
# 示例 1:
# 输入: [3,2,1,5,6,4], k = 2
# 输出: 5
import random

def fun(nums, left, right, k):
    m = len(nums) - k
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

    if lt <= m <= gt:
        return nums[m]
    elif m < lt:
        return fun(nums, left, lt - 1, k)
    else:
        return fun(nums, gt + 1, right, k)

if __name__ == '__main__':
    nums = [3,2,1,5,6,4]
    k = 2
    print(fun(nums, 0, len(nums) - 1, k))