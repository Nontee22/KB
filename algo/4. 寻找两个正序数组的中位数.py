# 4. 寻找两个正序数组的中位数
# 给定两个大小分别为 m 和 n 的正序（从小到大）数组 nums1 和 nums2。请你找出并返回这两个正序数组的 中位数 。
# 算法的时间复杂度应该为 O(log (m+n)) 。
#
# 示例 1：
# 输入：nums1 = [1,3], nums2 = [2]
# 输出：2.00000
# 解释：合并数组 = [1,2,3] ，中位数 2

def fun(nums1, nums2):
    if len(nums2) < len(nums1):
        nums1, nums2 = nums2, nums1
    m, n = len(nums1), len(nums2)
    total_left = (m + n + 1) // 2
    left, right = 0, m

    while left <= right:
        i1 = (left + right) // 2
        i2 = total_left - i1

        nums1_left_max = nums1[i1 - 1] if i1 > 0 else float('-inf')
        nums1_right_min = nums1[i1] if i1 < m else float('inf')
        nums2_left_max = nums2[i2 - 1] if i2 > 0 else float('-inf')
        nums2_right_min = nums2[i2] if i2 < n else float('inf')

        if nums1_left_max <= nums2_right_min and nums2_left_max <= nums1_right_min:
            left_max = max(nums1_left_max, nums2_left_max)
            right_min = min(nums1_right_min, nums2_right_min)

            if (m + n) % 2 == 0:
                return (left_max + right_min) / 2.0
            else:
                return left_max / 1.0
        elif nums1_left_max > nums2_right_min:
            right = i1 - 1
        else:
            left = i1 + 1


if __name__ == '__main__':
    nums1 = [1, 3]
    nums2 = [2]
    print(fun(nums1, nums2))