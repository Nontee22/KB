# 92. 反转链表 II
# 给你单链表的头指针 head 和两个整数 left 和 right ，其中 left <= right 。
# 请你反转从位置 left 到位置 right 的链表节点，返回 反转后的链表 。
#
# 示例 1：
# 输入：head = [1,2,3,4,5], left = 2, right = 4
# 输出：[1,4,3,2,5]

class ListNode:
    def __init__(self, val = 0, next = None):
        self.val = val
        self.next = next

def fun(head, left, right):
    d = p0 = ListNode(0, head)
    for _ in range(left - 1):
        p0 = p0.next

    pre = None
    cur = p0.next
    for _ in range(right - left + 1):
        nxt = cur.next
        cur.next = pre
        pre = cur
        cur = nxt 

    nxt = p0.next
    nxt.next = cur
    p0.next = pre

    return d.next

if __name__ == '__main__':
    head = ListNode(1)
    head.next = ListNode(2)
    head.next.next = ListNode(3)
    head.next.next.next = ListNode(4)
    head.next.next.next.next = ListNode(5)

    node = fun(head, 2, 4)
    while node:
        print(node.val, end = " ")
        node = node.next






