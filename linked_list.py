# Complete

class Node:
    def __init__(self, value: str|int|bool, pointer: "Node" = None) -> None:
        self.value = value
        self.pointer = pointer

class LinkedList:
    def __init__(self, node: Node = None):
        self.head = node
        self.len = 1 if self.head else 0

    def print_linked_list(self) -> None:
        current = self.head
        while current:
            print(current.value)
            current = current.pointer
        print(None)

    def get_len(self) -> int:
        return self.len

    def add_node_to_first(self, node: Node):
        node.pointer = self.head
        self.head = node
        self.len += 1
        return self.head

    def add_node_to_last(self, new_node: Node) -> Node:
        if new_node is None:
            raise ValueError("new_node cannot be None")
        if new_node.pointer is not None:
            raise ValueError("new_node must be a detached node")

        if self.head is None:
            self.head = new_node
            self.len += 1
            return self.head
        last = self.head
        while last.pointer is not None:
            last = last.pointer
        last.pointer = new_node
        self.len += 1
        return self.head

    def remove_first(self) -> None:
        if self.head is None:
            return
        self.head = self.head.pointer
        self.len -= 1

    def remove_last(self) -> None:
        if self.head is None:
            return

        if self.head.pointer is None:
            self.head = None
            self.len -= 1
            return

        current = self.head
        while current.pointer.pointer is not None:
            current = current.pointer

        current.pointer = None
        self.len -= 1

    def search(self, value: any) -> bool:
        current = self.head
        while current:
            if current.value == value:
                return True
            current = current.pointer
        return False

    def reverse(self) -> None:
        if self.head is None:
            return

        prev = None
        current = self.head
        while current:
            next = current.pointer
            current.pointer = prev
            prev = current
            current = next
        self.head = prev
        return self.head

    def get_by_index(self, index) -> bool:
        if index > self.len -1 or index < 0:
            raise ValueError("index is out of range")
        current = self.head
        for i in range(index):
            current = current.pointer
        return current.value

def find_the_middle(linked_list):
    if linked_list.head is None:
        return None
    len = linked_list.get_len()
    middle = len // 2
    current = linked_list.head
    for i in range(middle):
        current = current.pointer
    return current


# ------

# import unittest

# class TestLinkedList(unittest.TestCase):
#     def test_init(self):
#         linked_list = LinkedList()
#         self.assertEqual(linked_list.head, None)

#     def test_add_to_first(self):
#         linked_list = LinkedList()
#         linked_list.add_node_to_first(Node(1))
#         self.assertEqual(linked_list.head.value, 1)
#         self.assertEqual(linked_list.head.pointer, None)
#         self.assertEqual(linked_list.get_len(), 1)

#     def test_add_to_last(self):
#         linked_list = LinkedList()
#         linked_list.add_node_to_last(Node(1))
#         linked_list.add_node_to_last(Node(1))
#         linked_list.print_linked_list()
#         self.assertEqual(linked_list.head.value, 1)


# unittest.main()


import pytest

@pytest.mark.parametrize(
    "values, expected",
    [
        ([10], 10),
        ([10, 20], 20),
        ([10, 20, 30], 20),
        ([10, 20, 30, 40], 30),
        ([10, 20, 30, 40, 50], 30),
        ([10, 20, 30, 40, 50, 60], 40),
    ],
)
def test_find_middle(values, expected):

    linked_list = LinkedList()

    for value in values:
        linked_list.add_node_to_last(Node(value))

    middle = find_the_middle(linked_list)

    assert middle is not None
    assert middle.value == expected