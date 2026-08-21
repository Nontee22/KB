# 141. 环形链表
# 给你一个链表的头节点 head ，判断链表中是否有环。
# 如果链表中有某个节点，可以通过连续跟踪 next 指针再次到达，则链表中存在环。 为了表示给定链表中的环，
# 评测系统内部使用整数 pos 来表示链表尾连接到链表中的位置（索引从 0 开始）。注意：pos 不作为参数进行传递 。仅仅是为了标识链表的实际情况。
# 如果链表中存在环 ，则返回 true 。 否则，返回 false 。
#
# 示例 1：
# 输入：head = [3,2,0,4], pos = 1
# 输出：true
# 解释：链表中有一个环，其尾部连接到第二个节点。

class LinkedNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def fun(head):
    fast = slow = head
    while fast and fast.next:
        fast = fast.next.next
        slow = slow.next
        if fast is slow:
            return True
    return False

if __name__ == '__main__':
    head = LinkedNode(3)
    node2 = LinkedNode(2)
    node0 = LinkedNode(0)
    node4 = LinkedNode(4)

    head.next = node2
    node2.next = node0
    node0.next = node4
    node4.next = node2

    print(fun(head))
