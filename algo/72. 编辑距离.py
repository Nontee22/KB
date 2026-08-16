# 72. 编辑距离
# 给你两个单词 word1 和 word2， 请返回将 word1 转换成 word2 所使用的最少操作数  。
# 你可以对一个单词进行如下三种操作：
# 插入一个字符
# 删除一个字符
# 替换一个字符
#
# 示例 1：
# 输入：word1 = "horse", word2 = "ros"
# 输出：3
# 解释：
# horse -> rorse (将 'h' 替换为 'r')
# rorse -> rose (删除 'r')
# rose -> ros (删除 'e')

from functools import cache



def fun(word1, word2):
    # n, m = len(word1), len(word2)
    #
    # @cache
    # def dfs(i, j):
    #     if i < 0:
    #         return j + 1
    #     if j < 0:
    #         return i + 1
    #
    #     if word1[i] == word2[j]:
    #         return dfs(i - 1, j - 1)
    #     else:
    #         return min(dfs(i - 1, j - 1), dfs(i - 1, j), dfs(i, j - 1)) + 1
    #
    # return dfs(n - 1, m - 1)

    n, m = len(word1), len(word2)
    f = [[0] * (m + 1) for _ in range(n + 1)]
    f[0] = list(range(m + 1))

    for i in range(n):
        f[i + 1][0] = i + 1
        for j in range(m):
            if word1[i] == word2[j]:
                f[i + 1][j + 1] = f[i][j]
            else:
                f[i + 1][j + 1] = min(f[i][j], f[i][j + 1], f[i + 1][j]) + 1
    return f[n][m]

if __name__ == '__main__':
    word1 = "horse"
    word2 = "ros"
    print(fun(word1, word2))