# 236. 二叉树的最近公共祖先
# 给定一个二叉树, 找到该树中两个指定节点的最近公共祖先。
# 百度百科中最近公共祖先的定义为：“对于有根树 T 的两个节点 p、q，
# 最近公共祖先表示为一个节点 x，满足 x 是 p、q 的祖先且 x 的深度尽可能大（一个节点也可以是它自己的祖先）。”
#
# 示例 1：
# 输入：root = [3,5,1,6,2,0,8,null,null,7,4], p = 5, q = 1
# 输出：3
# 解释：节点 5 和节点 1 的最近公共祖先是节点 3 。

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def fun(root, p, q):
    def dfs(node, p, q):
        if node in (None, p, q):
            return node

        left = dfs(node.left, p, q)
        right = dfs(node.right, p, q)
        if left and right:
            return node

        return left or right

    return dfs(root, p, q)


if __name__ == '__main__':

    root = TreeNode(3)
    root.left = TreeNode(5)
    root.right = TreeNode(1)
    root.left.left = TreeNode(6)
    root.left.right = TreeNode(2)
    root.right.left = TreeNode(0)
    root.right.right = TreeNode(8)
    root.left.right.left = TreeNode(7)
    root.left.right.right = TreeNode(4)

    p = root.left
    q = root.right

    res = fun(root, p, q)
    print(res.val)