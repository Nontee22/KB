# 24. 两两交换链表中的节点
# 给你一个链表，两两交换其中相邻的节点，并返回交换后链表的头节点。你必须在不修改节点内部的值的情况下完成本题（即，只能进行节点交换）。
#
# 示例 1：
# 输入：head = [1,2,3,4]
# 输出：[2,1,4,3]

class LinkedNode:
    def __init__(self, val = 0, next = None):
        self.val = val
        self.next = next

def fun(head):
    n = 0
    node = head
    while node:
        n += 1
        node = node.next

    d = p0 = LinkedNode(0, head)
    cur = head
    pre = None
    while n >= 2:
        n -= 2

        for _ in range(2):
            nxt = cur.next
            cur.next = pre
            pre = cur
            cur = nxt

        nxt = p0.next
        p0.next = pre
        nxt.next = cur
        p0 = nxt

    return d.next

if __name__ == '__main__':
    node4 = LinkedNode(4)
    node3 = LinkedNode(3, node4)
    node2 = LinkedNode(2, node3)
    head = LinkedNode(1, node2)

    res = fun(head)
    while res:
        print(res.val, end=' ')
        res = res.next