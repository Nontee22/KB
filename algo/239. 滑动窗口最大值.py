# 239. 滑动窗口最大值
# 给你一个整数数组 nums，有一个大小为 k 的滑动窗口从数组的最左侧移动到数组的最右侧。
# 你只可以看到在滑动窗口内的 k 个数字。滑动窗口每次只向右移动一位。
# 返回 滑动窗口中的最大值 。
#
# 示例 1：
# 输入：nums = [1,3,-1,-3,5,3,6,7], k = 3
# 输出：[3,3,5,5,6,7]
# 解释：
# 滑动窗口的位置                最大值
# ---------------               -----
# [1  3  -1] -3  5  3  6  7       3
#  1 [3  -1  -3] 5  3  6  7       3
#  1  3 [-1  -3  5] 3  6  7       5
#  1  3  -1 [-3  5  3] 6  7       5
#  1  3  -1  -3 [5  3  6] 7       6
#  1  3  -1  -3  5 [3  6  7]      7
from collections import deque


def fun(nums, k):
    n = len(nums)
    q = deque()
    res = []
    for i in range(n):
        if q and q[0] < i - k:
            q.popleft()

        while q and nums[i] > nums[q[-1]]:
            q.pop()
        q.append(i)

        if i >= k - 1:
            res.append(nums[q[0]])

    return res

if __name__ == '__main__':
    nums = [1, 3, -1, -3, 5, 3, 6, 7]
    k = 3
    print(fun(nums, k))

