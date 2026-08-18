# 76. 最小覆盖子串
# 给定两个字符串 s 和 t，长度分别是 m 和 n，返回 s 中的 最短窗口 子串，使得该子串包含 t 中的每一个字符（包括重复字符）。
# 如果没有这样的子串，返回空字符串 ""。
# 测试用例保证答案唯一。
#
# 示例 1：
# 输入：s = "ADOBECODEBANC", t = "ABC"
# 输出："BANC"
# 解释：最小覆盖子串 "BANC" 包含来自字符串 t 的 'A'、'B' 和 'C'。

from collections import Counter


def fun(s, t):
    cnt_s = Counter()
    cnt_t = Counter(t)
    need = len(cnt_t)
    have = 0
    left = 0
    res = float('inf')
    res_left = 0

    for right, ch in enumerate(s):
        cnt_s[ch] += 1
        if cnt_s[ch] == cnt_t[ch]:
            have += 1

        while have == need:
            if right - left + 1 < res:
                res = right - left + 1
                res_left = left

            cnt_s[s[left]] -= 1
            if cnt_s[s[left]] < cnt_t[s[left]]:
                have -= 1
            left += 1

    return s[res_left:res_left + res] if res != float('inf') else ''

if __name__ == '__main__':
    s = "ADOBECODEBANC"
    t = "ABC"
    print(fun(s, t))


