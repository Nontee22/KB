# 165. 比较版本号
# 给你两个 版本号字符串 version1 和 version2 ，请你比较它们。版本号由被点 '.' 分开的修订号组成。
# 修订号的值 是它 转换为整数 并忽略前导零。
# 比较版本号时，请按 从左到右的顺序 依次比较它们的修订号。如果其中一个版本字符串的修订号较少，则将缺失的修订号视为 0。
# 返回规则如下：
# 如果 version1 < version2 返回 -1，
# 如果 version1 > version2 返回 1，
# 除此之外返回 0。
#
# 示例 1：
# 输入：version1 = "1.2", version2 = "1.10"
# 输出：-1
# 解释：
# version1 的第二个修订号为 "2"，version2 的第二个修订号为 "10"：2 < 10，所以 version1 < version2。

def fun(version1, version2):
    v1 = version1.split('.')
    v2 = version2.split('.')

    m, n = len(v1), len(v2)
    i = j = 0

    while i < m or j < n:
        val1 = int(v1[i]) if i < m else 0
        val2 = int(v2[j]) if j < n else 0
        i += 1
        j += 1
        if val1 > val2:
            return 1
        elif val2 > val1:
            return -1

    return 0

if __name__ == '__main__':
    version1 = "1.2"
    version2 = "1.10"
    print(fun(version1, version2))