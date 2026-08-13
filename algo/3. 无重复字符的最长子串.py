# 3. 无重复字符的最长子串
# 给定一个字符串 s ，请你找出其中不含有重复字符的 最长 子串 的长度。
#
# 示例 1:
# 输入: s = "abcabcbb"
# 输出: 3
# 解释: 因为无重复字符的最长子串是 "abc"，所以其长度为 3。注意 "bca" 和 "cab" 也是正确答案。

def fun(s):

    hashmap = {}
    l = 0
    res = 0
    for r, c in enumerate(s):
        if c in hashmap and hashmap[c] >= l:
            l = hashmap[c] + 1
        hashmap[c] = r
        res = max(res, r - l + 1)

    return res


if __name__ == '__main__':
    s = "abcabcbb"
    print(fun(s))