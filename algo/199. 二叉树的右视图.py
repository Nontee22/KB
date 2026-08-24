# 199. 二叉树的右视图
# 给定一个二叉树的 根节点 root，想象自己站在它的右侧，按照从顶部到底部的顺序，返回从右侧所能看到的节点值。
#
# 示例 1：
# 输入：root = [1,2,3,null,5,null,4]
# 输出：[1,3,4]

from collections import deque
from platform import node


class TreeNode:
    def __init__(self, left = None, right = None, value = 0):
        self.left = left
        self.right = right
        self.value = value

def fun(root):
    if not root:
        return []

    q = deque([root])
    res = []
    while q:
        n = len(q)
        for _ in range(n):
            node = q.popleft()
            if node.left:
                q.append(node.left)
            if node.right:
                q.append(node.right)
        res.append(node.value)
    return res

if __name__ == '__main__':
    node5 = TreeNode(None, None,5)
    node2 = TreeNode(None, node5, 2)
    node4 = TreeNode(None, None,4)
    node3 = TreeNode(None, node4, 3)
    root = TreeNode(node2, node3, 1)
    print(fun(root))