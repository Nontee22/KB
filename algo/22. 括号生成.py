# 22. 括号生成
# 数字 n 代表生成括号的对数，请你设计一个函数，用于能够生成所有可能的并且 有效的 括号组合。
#
# 示例 1：
# 输入：n = 3
# 输出：["((()))","(()())","(())()","()(())","()()()"]

def fun(n):
    res = []
    def dfs(i, j, path):
        if i == n and j == n:
            res.append(path)
            return

        if i < n:
            dfs(i + 1, j, path + '(')

        if j < i:
            dfs(i, j + 1, path + ')')

    dfs(0, 0, '')
    return res

if __name__ == '__main__':
    n = 3
    print(fun(n))



