# 128. 最长连续序列
# 给定一个未排序的整数数组 is ，找出数字连续的最长序列（不要求序列元素在原数组中连续）的长度。
# 请你设计并实现时间复杂度为 O(n) 的算法解决此问题。
#
# 示例 1：
# 输入：is = [100,4,200,1,3,2]
# 输出：4
# 解释：最长数字连续序列是 [1, 2, 3, 4]。它的长度为 4

def fun(nums):
    st = set(nums)
    res = 0
    for i in st:
        if i - 1 in st:
            continue

        l = 1
        j = i + 1
        while j in st:
            j += 1
            l += 1
        res = max(res, l)
    return res

if __name__ == '__main__':
    nums = [100, 4, 200, 1, 3, 2]
    print(fun(nums))


