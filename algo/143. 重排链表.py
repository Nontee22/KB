# 143. 重排链表
# 给定一个单链表 L 的头节点 head ，单链表 L 表示为：
# L0 → L1 → … → Ln - 1 → Ln
# 请将其重新排列后变为：
# L0 → Ln → L1 → Ln - 1 → L2 → Ln - 2 → …
# 不能只是单纯的改变节点内部的值，而是需要实际的进行节点交换。
#
# 示例 1：
# 输入：head = [1,2,3,4]
# 输出：[1,4,2,3]

class ListNode:
    def __init__(self, value=0, next=None):
        self.value = value
        self.next = next

def fun(head):
    fast = slow = head
    while fast and fast.next:
        fast = fast.next.next
        slow = slow.next

    def reverse(node):
        pre = None
        cur = node
        while cur:
            nxt = cur.next
            cur.next = pre
            pre = cur
            cur = nxt
        return pre

    head1 = head
    head2 = reverse(slow)

    while head2 and head2.next:
        nxt1 = head1.next
        nxt2 = head2.next
        head1.next = head2
        head2.next = nxt1
        head1 = nxt1
        head2 = nxt2

    return head

if __name__ == '__main__':
    head = ListNode(1)
    head.next = ListNode(2)
    head.next.next = ListNode(3)
    head.next.next.next = ListNode(4)
    head.next.next.next.next = ListNode(5)

    res = fun(head)
    while res:
        print(res.value)
        res = res.next