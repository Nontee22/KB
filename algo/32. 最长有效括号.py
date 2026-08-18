# 32. 最长有效括号
# 给你一个只包含 '(' 和 ')' 的字符串，找出最长有效（格式正确且连续）括号 子串 的长度。
# 左右括号匹配，即每个左括号都有对应的右括号将其闭合的字符串是格式正确的，比如 "(()())"。
#
# 示例 1：
# 输入：s = "(()"
# 输出：2
# 解释：最长有效括号子串是 "()"

def fun(s):
    stack = [-1]
    max_len = 0

    for i, c in enumerate(s):
        if c == '(':
            stack.append(i)
        else:
            stack.pop()
            if not stack:
                stack.append(i)
            else:
                max_len = max(max_len, i - stack[-1])

    return max_len

if __name__ == '__main__':
    s = "(()"
    print(fun(s))