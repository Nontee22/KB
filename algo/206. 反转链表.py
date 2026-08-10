# 206. 反转链表
# 给你单链表的头节点head ，请你反转链表，并返回反转后的链表。
#
# 示例1：
# 输入：head = [1, 2, 3, 4, 5]
# 输出：[5, 4, 3, 2, 1]

class ListNode:
    def __init__(self, value = 0, next = None):
        self.value = value
        self.next = next

def fun(head):
    pre = None
    cur = head

    while cur:
        nxt = cur.next
        cur.next = pre
        pre = cur
        cur = nxt

    return pre

if __name__ == '__main__':
    head = ListNode(1)
    head.next = ListNode(2)
    head.next.next = ListNode(3)
    head.next.next.next = ListNode(4)
    head.next.next.next.next = ListNode(5)

    p0 = fun(head)
    while p0:
        print(p0.value)
        p0 = p0.next