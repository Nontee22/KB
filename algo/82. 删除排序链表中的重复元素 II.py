# 82. 删除排序链表中的重复元素 II
# 给定一个已排序的链表的头 head ， 删除原始链表中所有重复数字的节点，只留下不同的数字 。返回 已排序的链表 。
#
# 示例 1：
# 输入：head = [1,2,3,3,4,4,5]
# 输出：[1,2,5]

class LinkedNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def fun(head):
    res = d = LinkedNode(0, head)
    while res and res.next and res.next.next:
        if res.next.val == res.next.next.val:
            v = res.next.val
            while res.next and res.next.val == v:
                res.next = res.next.next
        else:
            res = res.next

    return d.next


if __name__ == '__main__':
    head = LinkedNode(1)
    head.next = LinkedNode(2)
    head.next.next = LinkedNode(3)
    head.next.next.next = LinkedNode(3)
    head.next.next.next.next = LinkedNode(4)
    head.next.next.next.next.next = LinkedNode(4)
    head.next.next.next.next.next.next = LinkedNode(5)

    res = fun(head)
    while res:
        print(res.val, end=" ")
        res = res.next