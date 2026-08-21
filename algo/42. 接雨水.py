# 42. 接雨水
# 给定 n 个非负整数表示每个宽度为 1 的柱子的高度图，计算按此排列的柱子，下雨之后能接多少雨水。
#
# 示例 1：
# 输入：height = [0,1,0,2,1,0,1,3,2,1,2,1]
# 输出：6
# 解释：上面是由数组 [0,1,0,2,1,0,1,3,2,1,2,1] 表示的高度图，在这种情况下，可以接 6 个单位的雨水（蓝色部分表示雨水）。

def fun(height):
    res = 0
    i, j = 0, len(height) - 1
    left_max, right_max = height[i], height[j]

    while i < j:
        if height[i] <= height[j]:
            if height[i] >= left_max:
                left_max = height[i]
            else:
                res += left_max - height[i]
            i += 1
        else:
            if height[j] >= right_max:
                right_max = height[j]
            else:
                res += right_max - height[j]
            j -= 1
    return res

if __name__ == '__main__':
    height = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]
    print(fun(height))

