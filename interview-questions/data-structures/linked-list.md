# Linked List Implementation

## Problem Statement
Implement a singly linked list with the following operations:
- Insert at head
- Insert at tail
- Delete by value
- Search for a value
- Print the list

## Linked List Basics

A linked list is a linear data structure where elements are stored in nodes. Each node contains:
- Data (the value)
- Next pointer (reference to next node)

### Advantages
- Dynamic size
- Easy insertion/deletion at beginning (O(1))
- No memory waste

### Disadvantages
- No random access (must traverse from head)
- Extra memory for pointers
- Not cache-friendly

## Time Complexities
- Insert at head: O(1)
- Insert at tail: O(n) without tail pointer, O(1) with tail pointer
- Delete: O(n) 
- Search: O(n)
- Access by index: O(n)

## Space Complexity: O(n)

## Solution (Python)

```python
class Node:
    """Node in a singly linked list."""
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    """Singly linked list implementation."""
    
    def __init__(self):
        self.head = None
    
    def insert_at_head(self, data):
        """Insert new node at the beginning."""
        new_node = Node(data)
        new_node.next = self.head
        self.head = new_node
    
    def insert_at_tail(self, data):
        """Insert new node at the end."""
        new_node = Node(data)
        
        if not self.head:
            self.head = new_node
            return
        
        current = self.head
        while current.next:
            current = current.next
        current.next = new_node
    
    def delete(self, data):
        """Delete first node with given data."""
        if not self.head:
            return
        
        # If head needs to be deleted
        if self.head.data == data:
            self.head = self.head.next
            return
        
        # Find the node to delete
        current = self.head
        while current.next:
            if current.next.data == data:
                current.next = current.next.next
                return
            current = current.next
    
    def search(self, data):
        """Search for a value in the list."""
        current = self.head
        while current:
            if current.data == data:
                return True
            current = current.next
        return False
    
    def print_list(self):
        """Print all elements in the list."""
        elements = []
        current = self.head
        while current:
            elements.append(str(current.data))
            current = current.next
        print(" -> ".join(elements))
    
    def length(self):
        """Return the length of the list."""
        count = 0
        current = self.head
        while current:
            count += 1
            current = current.next
        return count

# Test the linked list
if __name__ == "__main__":
    ll = LinkedList()
    
    # Insert elements
    ll.insert_at_head(1)
    ll.insert_at_head(2)
    ll.insert_at_tail(3)
    ll.insert_at_tail(4)
    
    print("Linked List:")
    ll.print_list()  # 2 -> 1 -> 3 -> 4
    
    print(f"Length: {ll.length()}")  # 4
    print(f"Search 3: {ll.search(3)}")  # True
    print(f"Search 5: {ll.search(5)}")  # False
    
    ll.delete(1)
    print("After deleting 1:")
    ll.print_list()  # 2 -> 3 -> 4
```

## Common Linked List Problems
1. Reverse a linked list
2. Detect cycle in linked list
3. Find middle element
4. Merge two sorted lists
5. Remove nth node from end
6. Check if palindrome

## Notes
- Always check for null/None pointers
- Draw diagrams when solving linked list problems
- Consider edge cases: empty list, single node, two nodes
- Be careful when modifying pointers - easy to lose references
