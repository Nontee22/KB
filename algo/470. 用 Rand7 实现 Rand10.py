# 470. 用 Rand7() 实现 Rand10()
# 给定方法 rand7 可生成 [1,7] 范围内的均匀随机整数，试写一个方法 rand10 生成 [1,10] 范围内的均匀随机整数。
# 你只能调用 rand7() 且不能调用其他方法。请不要使用系统的 Math.random() 方法。
# 每个测试用例将有一个内部参数 n，即你实现的函数 rand10() 在测试时将被调用的次数。请注意，这不是传递给 rand10() 的参数。
#
# 示例 1:
# 输入: 1
# 输出: [2]

import random

def rand7():
    return random.randint(1, 7)

def fun():
    while True:
        i = (rand7() - 1) * 7 + rand7()
        if i <= 40:
            return (i - 1) % 10 + 1

if __name__ == '__main__':
    res = [0] * 11
    for _ in range(1000000):
        num = fun()
        res[num] += 1
    print(res)
