# 23. 合并 K 个升序链表
# 给你一个链表数组，每个链表都已经按升序排列。
# 请你将所有链表合并到一个升序链表中，返回合并后的链表。
#
# 示例 1：
# 输入：lists = [[1,4,5],[1,3,4],[2,6]]
# 输出：[1,1,2,3,4,4,5,6]
# 解释：链表数组如下：
# [
#   1->4->5,
#   1->3->4,
#   2->6
# ]
# 将它们合并到一个有序链表中得到。
# 1->1->2->3->4->4->5->6

import heapq

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def fun(lists):
    heap = []
    dummy = ListNode()
    cur = dummy

    for i, node in enumerate(lists):
        if node:
            heapq.heappush(heap, (node.val, i, node))

    while heap:
        val, idx, node = heapq.heappop(heap)
        cur.next = node
        cur = cur.next

        if node.next:
            heapq.heappush(heap, (node.next.val, idx, node.next))

    return dummy.next


if __name__ == '__main__':
    list1 = ListNode(1)
    list1.next = ListNode(4)
    list1.next.next = ListNode(5)

    list2 = ListNode(1)
    list2.next = ListNode(3)
    list2.next.next = ListNode(4)

    list3 = ListNode(2)
    list3.next = ListNode(6)

    lists = [list1, list2, list3]

    res = fun(lists)


    while res:
        print(res.val)
        res = res.next