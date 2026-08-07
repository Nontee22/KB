# 21. 合并两个有序链表
# 将两个升序链表合并为一个新的 升序 链表并返回。新链表是通过拼接给定的两个链表的所有节点组成的。

# 示例 1:
# 输入：l1 = [1,2,4], l2 = [1,3,4]
# 输出：[1,1,2,3,4,4]

class LinkedNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def fun(head1, head2):
    d = cur = LinkedNode()

    while head1 and head2:
        if head1.val < head2.val:
            cur.next = head1
            head1 = head1.next
        else:
            cur.next = head2
            head2 = head2.next
        cur = cur.next

    cur.next = head1 or head2

    return d.next


if __name__ == '__main__':
    l1 = LinkedNode(1)
    l1.next = LinkedNode(2)
    l1.next.next = LinkedNode(4)

    l2 = LinkedNode(1)
    l2.next = LinkedNode(3)
    l2.next.next = LinkedNode(4)

    merged = fun(l1, l2)
    while merged:
        print(merged.val)
        merged = merged.next