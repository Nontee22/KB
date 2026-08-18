# 103. 二叉树的锯齿形层序遍历
# 给你二叉树的根节点 root ，返回其节点值的 锯齿形层序遍历 。
# （即先从左往右，再从右往左进行下一层遍历，以此类推，层与层之间交替进行）。
#
# 示例 1：
# 输入：root = [3,9,20,null,null,15,7]
# 输出：[[3],[20,9],[15,7]]

from collections import deque


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def fun(root):
    if not root:
        return []

    q = deque([root])
    res = []
    flag = True

    while q:
        n = len(q)
        vals = []

        for _ in range(n):
            node = q.popleft()
            vals.append(node.val)

            if node.left:
                q.append(node.left)
            if node.right:
                q.append(node.right)

        if flag:
            res.append(vals)
        else:
            res.append(vals[::-1])

        flag = not flag

    return res


if __name__ == '__main__':
    node15 = TreeNode(15)
    node7 = TreeNode(7)
    node9 = TreeNode(9)
    node20 = TreeNode(20, node15, node7)
    root = TreeNode(3, node9, node20)

    result = fun(root)
    print(result)