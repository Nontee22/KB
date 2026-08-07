# 415. 字符串相加
# 给定两个字符串形式的非负整数 num1 和num2 ，计算它们的和并同样以字符串形式返回。
# 你不能使用任何內建的用于处理大整数的库（比如 BigInteger）， 也不能直接将输入的字符串转换为整数形式。
#
# 示例 1：
# 输入：num1 = "11", num2 = "123"
# 输出："134"

def fun(num1, num2):
    i, j = len(num1) - 1, len(num2) - 1
    carry = 0
    result = []

    while i >= 0 or j >= 0 or carry > 0:
        digit1 = ord(num1[i]) - 48 if i >= 0 else 0
        digit2 = ord(num2[j]) - 48 if j >= 0 else 0

        total = digit1 + digit2 + carry
        result.append(str(total % 10))
        carry = total // 10

        i -= 1
        j -= 1

    res = ''.join(result)
    return res[::-1]

if __name__ == '__main__':
    num1 = "11"
    num2 = "123"
    print(fun(num1, num2))