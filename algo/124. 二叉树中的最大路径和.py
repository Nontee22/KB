# 124. 二叉树中的最大路径和
# 二叉树中的 路径 被定义为一条节点序列，序列中每对相邻节点之间都存在一条边。
# 同一个节点在一条路径序列中 至多出现一次 。该路径 至少包含一个 节点，且不一定经过根节点。
# 路径和 是路径中各节点值的总和。
# 给你一个二叉树的根节点 root ，返回其 最大路径和 。
#
# 示例 1：
# 输入：root = [1,2,3]
# 输出：6
# 解释：最优路径是 2 -> 1 -> 3 ，路径和为 2 + 1 + 3 = 6

class TreeNode:
    def __init__(self, val = 0, left = None, right = None):
        self.val = val
        self.left = left
        self.right = right

def fun(root):
    res = float("-inf")

    def dfs(node):
        nonlocal res
        if not node:
            return 0

        left = max(dfs(node.left), 0)
        right = max(dfs(node.right), 0)

        res = max(res, node.val + left + right)

        return node.val + max(left, right)

    dfs(root)
    return res

if __name__ == '__main__':
    node2 = TreeNode(2, None,None)
    node3 = TreeNode(3, None,None)
    root = TreeNode(1, node2, node3)
    print(fun(root))




