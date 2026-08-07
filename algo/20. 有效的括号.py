# 20. 有效的括号
# 给定一个只包括 '('，')'，'{'，'}'，'['，']'的字符串s，判断字符串是否有效。
# 有效字符串需满足：
# 左括号必须用相同类型的右括号闭合。
# 左括号必须以正确的顺序闭合。
# 每个右括号都有一个对应的相同类型的左括号。
#
# 示例 1：
# 输入：s = "()"
# 输出：true

def fun(s):
    dic = {'(' : ')', '{' : '}', '[' : ']'}
    stack = []
    for c in s:
        if c in dic:
            stack.append(c)
        else:
            if not stack or dic[stack.pop()] != c:
                return False

    return not stack

if __name__ == '__main__':
    s = "()"
    print(fun(s))

