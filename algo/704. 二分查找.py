# 704. 二分查找
# 给定一个 n 个元素有序的（升序）整型数组 nums 和一个目标值 target
# 写一个函数搜索 nums 中的 target，如果 target 存在返回下标，否则返回 -1。
# 你必须编写一个具有 O(log n) 时间复杂度的算法。
#
# 示例 1:
# 输入: nums = [-1,0,3,5,9,12], target = 9
# 输出: 4
# 解释: 9 出现在 nums 中并且下标为 4

def fun(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] > target:
            right = mid - 1
        else:
            left = mid + 1
    return -1

if __name__ == '__main__':
    nums = [-1, 0, 3, 5, 9, 12]
    target = 9
    print(fun(nums, target))


