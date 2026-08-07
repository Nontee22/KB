# 46. 全排列
# 给定一个不含重复数字的数组 nums ，返回其 所有可能的全排列 。你可以 按任意顺序 返回答案。
#
# 示例 1：
# 输入：nums = [1,2,3]
# 输出：[[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]

def fun(nums):
    n = len(nums)
    res = []
    vals = [0] * n
    flag = [False] * n

    def dfs(i):
        if i == n:
            res.append(vals[:])
            return
        for j in range(n):
            if not flag[j]:
                vals[i] = nums[j]
                flag[j] = True
                dfs(i + 1)
                flag[j] = False

    dfs(0)
    return res

if __name__ == '__main__':
    nums = [1, 2, 3]
    print(fun(nums))





