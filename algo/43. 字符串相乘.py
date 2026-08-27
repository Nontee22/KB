# 43. 字符串相乘
# 给定两个以字符串形式表示的非负整数 num1 和 num2，返回 num1 和 num2 的乘积，它们的乘积也表示为字符串形式。
# 注意：不能使用任何内置的 BigInteger 库或直接将输入转换为整数。
#
# 示例 1:
# 输入: num1 = "2", num2 = "3"
# 输出: "6"

def fun(num1, num2):
    if num1 == "0" or num2 == "0":
        return "0"

    m, n = len(num1), len(num2)
    res = [0] * (m + n)
    for i in range(m - 1, -1, -1):
        for j in range(n - 1, -1, -1):
            res[i + j + 1] += (ord(num1[i]) - 48) * (ord(num2[j]) - 48)

    for k in range(m + n - 1, 0, -1):
        if k > 0:
            res[k - 1] += res[k] // 10
            res[k] = res[k] % 10

    start = 0
    while start < len(res) and res[start] == 0:
        start += 1

    return ''.join(map(str, res[start:]))

if __name__ == '__main__':
    num1 = "2"
    num2 = "3"
    print(fun(num1, num2))