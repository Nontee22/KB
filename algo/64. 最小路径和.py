# 64. 最小路径和
# 给定一个包含非负整数的 m x n 网格 grid ，请找出一条从左上角到右下角的路径，使得路径上的数字总和为最小。
# 说明：每次只能向下或者向右移动一步。
#
# 示例 1：
# 输入：grid = [[1,3,1],[1,5,1],[4,2,1]]
# 输出：7
# 解释：因为路径 1→3→1→1→1 的总和最小

from functools import cache

def fun(grid):
    m, n = len(grid), len(grid[0])
    # @cache
    # def dfs(i, j):
    #     if i == 0 and j == 0:
    #         return grid[i][j]
    #     if i < 0 or j < 0:
    #         return float('inf')
    #
    #     return min(dfs(i - 1, j), dfs(i, j - 1)) + grid[i][j]
    # return dfs(m - 1, n - 1)
    f = [[float('inf')] * (n + 1) for i in range(m + 1)]
    f[1][0] = f[0][1] = 0
    for i in range(m):
        for j in range(n):
            f[i + 1][j + 1] = min(f[i][j + 1], f[i + 1][j]) + grid[i][j]
    return f[m][n]

if __name__ == '__main__':
    grid = [[1, 3, 1], [1, 5, 1], [4, 2, 1]]
    print(fun(grid))