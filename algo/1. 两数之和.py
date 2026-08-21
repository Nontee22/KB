# 1. 两数之和
# 给定一个整数数组 nums 和一个整数目标值 target，请你在该数组中找出 和为目标值 target  的那 两个 整数，并返回它们的数组下标。
# 你可以假设每种输入只会对应一个答案，并且你不能使用两次相同的元素。
# 你可以按任意顺序返回答案。
#
# 示例 1：
# 输入：nums = [2,7,11,15], target = 9
# 输出：[0,1]
# 解释：因为 nums[0] + nums[1] == 9 ，返回 [0, 1] 。

def fun(nums, target):
    dic = {}
    for i, x in enumerate(nums):
        need_x = target - x
        if need_x in dic:
            return [dic[need_x], i]
        dic[x] = i
    return []

if __name__ == '__main__':
    nums = [2, 7, 11, 15]
    target = 9
    print(fun(nums, target))


