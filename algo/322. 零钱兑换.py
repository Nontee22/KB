# 322. 零钱兑换
# 给你一个整数数组 coins ，表示不同面额的硬币；以及一个整数 amount ，表示总金额。
# 计算并返回可以凑成总金额所需的 最少的硬币个数 。如果没有任何一种硬币组合能组成总金额，返回 -1 。
# 你可以认为每种硬币的数量是无限的。
#
# 示例 1：
# 输入：coins = [1, 2, 5], amount = 11
# 输出：3
# 解释：11 = 5 + 5 + 1

from functools import cache


def fun(coins, amount):
    # @cache
    # def dfs(i, j):
    #     if j == 0:
    #         return 0
    #
    #     if j < 0 or i < 0:
    #         return float('inf')
    #
    #     if coins[i] > j:
    #         return dfs(i - 1, j)
    #     else:
    #         return min(dfs(i - 1, j), dfs(i, j - coins[i]) + 1)
    # res = dfs(len(coins) - 1, amount)
    # return res if res != float('inf') else -1

    m, n = len(coins), amount
    f = [[float('inf')] * (n + 1) for _ in range(m + 1)]
    for i in range(m):
        f[i][0] = 0
        for j in range(n + 1):
            if coins[i] > j:
                f[i + 1][j] = f[i][j]
            else:
                f[i + 1][j] = min(f[i][j], f[i + 1][j - coins[i]] + 1)
    return f[m][n] if f[m][n] != float('inf') else -1

if __name__ == '__main__':
    coins = [1, 2, 5]
    amount = 11
    print(fun(coins, amount))



