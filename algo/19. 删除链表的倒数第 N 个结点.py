# 19. 删除链表的倒数第 N 个结点
# 给你一个链表，删除链表的倒数第 n 个结点，并且返回链表的头结点。
#
# 示例 1：
# 输入：head = [1,2,3,4,5], n = 2
# 输出：[1,2,3,5]

class LinkedNode:
    def __init__(self, val = 0, next = None):
        self.val = val
        self.next = next

def fun(head, n):
    fast = slow = head
    for _ in range(n + 1):
        fast = fast.next

    while fast:
        fast = fast.next
        slow = slow.next

    slow.next = slow.next.next
    return head

if __name__ == '__main__':
    head = LinkedNode(1)
    head.next = LinkedNode(2)
    head.next.next = LinkedNode(3)
    head.next.next.next = LinkedNode(4)
    head.next.next.next.next = LinkedNode(5)
    n = 2

    res = fun(head, n)
    while res:
        print(res.val, end = ' ')
        res = res.next


