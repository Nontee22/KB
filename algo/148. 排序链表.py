# 148. 排序链表
# 给你链表的头结点 head ，请将其按 升序 排列并返回 排序后的链表 。
#
# 示例 1：
# 输入：head = [4,2,1,3]
# 输出：[1,2,3,4]

class LinkedNode:
    def __init__(self, val = 0, next = None):
        self.val = val
        self.next = next

def merged(list1, list2):
    cur = d = LinkedNode()
    while list1 and list2:
        if list1.val < list2.val:
            cur.next = list1
            list1 = list1.next
        else:
            cur.next = list2
            list2 = list2.next
        cur = cur.next

    cur.next = list1 or list2
    return d.next

def fun(head):
    if not head or not head.next:
        return head

    slow = head
    fast = head.next
    while fast and fast.next:
        fast = fast.next.next
        slow = slow.next

    head2 = slow.next
    slow.next = None

    left = fun(head)
    right = fun(head2)

    return merged(left, right)

if __name__ == '__main__':
    node3 = LinkedNode(3)
    node1 = LinkedNode(1, node3)
    node2 = LinkedNode(2, node1)
    head = LinkedNode(4, node2)

    res = fun(head)
    while res:
        print(res.val, end = ' ')
        res = res.next












