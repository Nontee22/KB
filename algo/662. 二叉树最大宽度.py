# 662. 二叉树最大宽度
# 给你一棵二叉树的根节点 root ，返回树的 最大宽度 。
# 树的 最大宽度 是所有层中最大的 宽度 。
# 每一层的 宽度 被定义为该层最左和最右的非空节点（即，两个端点）之间的长度。
# 将这个二叉树视作与满二叉树结构相同，两端点间会出现一些延伸到这一层的 null 节点，这些 null 节点也计入长度。
# 题目数据保证答案将会在  32 位 带符号整数范围内。
#
# 示例 1：
# 输入：root = [1,3,2,5,3,null,9]
# 输出：4
# 解释：最大宽度出现在树的第 3 层，宽度为 4 (5,3,null,9) 。

from collections import deque


class TreeNode:
    def __init__(self, val = 0, left = None, right = None):
        self.val = val
        self.left = left
        self.right = right

def fun(root):
    if not root:
        return 0

    q = deque([[root, 1]])
    res = 0
    while q:
        n = len(q)
        left, right = q[0][1], q[-1][1]
        res = max(res, right - left + 1)

        for _ in range(n):
            node, idx = q.popleft()
            i = idx - left
            if node.left:
                q.append([node.left, i * 2])
            if node.right:
                q.append([node.right, i * 2 + 1])

    return res

if __name__ == '__main__':
    root = TreeNode(1)
    root.left = TreeNode(3)
    root.right = TreeNode(2)
    root.left.left = TreeNode(5)
    root.left.right = TreeNode(3)
    root.right.right = TreeNode(9)

    print(fun(root))



