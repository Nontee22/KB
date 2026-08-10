# 5. 最长回文子串
# 给你一个字符串 s，找到 s 中最长的 回文 子串。
#
# 示例 1：
# 输入：s = "babad"
# 输出："bab"
# 解释："aba" 同样是符合题意的答案。

def fun(s):
    n = len(s)
    res_len = 1
    res_left = 0

    def dfs(i, j):
        while i >= 0 and j < n and s[i] == s[j]:
            i -= 1
            j += 1
        return  j - i - 1

    for r, c in enumerate(s):
        max_len = max(dfs(r, r), dfs(r, r + 1))
        if max_len >= res_len:
            res_len = max_len
            res_left = r - (max_len - 1) // 2
    return s[res_left: res_left + res_len]

if __name__ == '__main__':
    s = "babad"
    print(fun(s))


