# 146. LRU 缓存
# 请你设计并实现一个满足  LRU (最近最少使用) 缓存 约束的数据结构。
# 实现 LRUCache 类：
# LRUCache(int capacity) 以 正整数 作为容量 capacity 初始化 LRU 缓存
# int get(int key) 如果关键字 key 存在于缓存中，则返回关键字的值，否则返回 -1。
# void put(int key, int value) 如果关键字 key 已经存在，则变更其数据值 value；
# 如果不存在，则向缓存中插入该组 key-value 。如果插入操作导致关键字数量超过 capacity ，则应该 逐出 最久未使用的关键字。
# 函数 get 和 put 必须以 O(1) 的平均时间复杂度运行。
#
# 示例：
# 输入
# ["LRUCache", "put", "put", "get", "put", "get", "put", "get", "get", "get"]
# [[2], [1, 1], [2, 2], [1], [3, 3], [2], [4, 4], [1], [3], [4]]
# 输出
# [null, null, null, 1, null, -1, null, -1, 3, 4]

class LinkedNode:
    def __init__(self, key=0, val=0, next=None, prev=None):
        self.key = key
        self.val = val
        self.next = next
        self.prev = prev

class LRU:
    def __init__(self, capacity):
        self.size = 0
        self.capacity = capacity
        self.hashmap = {}

        self.head = LinkedNode()
        self.tail = LinkedNode()
        self.head.next = self.tail
        self.tail.prev = self.head

    def delNode(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def addHead(self, node):
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def moveHead(self, node):
        self.delNode(node)
        self.addHead(node)

    def get(self, key):
        if key in self.hashmap:
            node = self.hashmap[key]
            self.moveHead(node)
            return node.val
        return -1

    def put(self, key, value):
        if key in self.hashmap:
            node = self.hashmap[key]
            self.moveHead(node)
            node.val = value
        else:
            newNode = LinkedNode(key, value)
            self.hashmap[key] = newNode
            self.size += 1
            self.addHead(newNode)

            if self.size > self.capacity:
                oldNode = self.tail.prev
                del self.hashmap[oldNode.key]
                self.delNode(oldNode)
                self.size -= 1

if __name__ == "__main__":
    cache = LRU(2)
    results = []

    results.append(cache.put(1, 1)) 
    results.append(cache.put(2, 2)) 
    results.append(cache.get(1))
    results.append(cache.put(3, 3)) 
    results.append(cache.get(2))
    results.append(cache.put(4, 4)) 
    results.append(cache.get(1))
    results.append(cache.get(3))
    results.append(cache.get(4))

    print(results)