# 1143. 最长公共子序列
# 给定两个字符串 text1 和 text2，返回这两个字符串的最长 公共子序列 的长度。如果不存在 公共子序列 ，返回 0 。
# 例如，"ace" 是 "abcde" 的子序列，但 "aec" 不是 "abcde" 的子序列。
# 两个字符串的 公共子序列 是这两个字符串所共同拥有的子序列。
#
# 示例 1：
# 输入：text1 = "abcde", text2 = "ace"
# 输出：3
# 解释：最长公共子序列是 "ace" ，它的长度为 3 。
from functools import cache

def fun(text1, text2):
    # @cache
    # def dfs(i, j):
    #     if i < 0 or j < 0:
    #         return 0
    #
    #     if text1[i] == text2[j]:
    #         return dfs(i - 1, j - 1) + 1
    #     else:
    #         return max(dfs(i - 1, j), dfs(i, j - 1))
    #
    # return dfs(len(text1) - 1, len(text2) - 1)

    m, n = len(text1), len(text2)
    f = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m):
        for j in range(n):
            if text1[i] == text2[j]:
                f[i + 1][j + 1] = f[i][j] + 1
            else:
                f[i + 1][j + 1] = max(f[i + 1][j], f[i][j + 1])
    return f[m][n]

if __name__ == '__main__':
    text1 = "abcde"
    text2 = "ace"
    print(fun(text1, text2))



