from enum import Enum
from event import Event
from rich.panel import Panel
from rich import print

class ETNode:
    class State(Enum):
        UNKNOWN = 0
        VALID = 1
        INVALID = 2
        TRUSTED = 3
    
    def __init__(self, id, name, sig = "", params = {}, source = {}, result = None):
        self.id = id
        self.state = ETNode.State.UNKNOWN
        self.name = name
        self.sig = sig
        self.params = params
        self.m_params = params.copy()
        self.locals = {}
        self.source = source
        self.result = result
        self.parent = None
        self.left_child = None
        self.right_sibling = None
        
    def __eq__(self, other):
        if isinstance(other, ETNode):
            return self.id == other.id and \
                self.name == other.name and \
                    self.parent == other.parent
        return False
            
    def _get_children(self):
        children = []
        ptr = self.left_child
        if ptr:
            children.append(ptr)
            if ptr.right_sibling:
                ptr = ptr.right_sibling
                while ptr:
                    children.append(ptr)
                    ptr = ptr.right_sibling
        return children

    def __str__(self):
        return f"({self.id}) {self.name}{self.sig}"

    def update(self, updated_locals):
        if not self.locals:
            self.locals = updated_locals.copy()
        self.locals.update(updated_locals)
    
    def is_leaf(self):
        return not bool(self.left_child)
    
    def is_terminal(self):
        return not bool(self.right_sibling)
    
    def size(self):
        if not self.left_child:
            return 1
        ptr = self.left_child
        queue = [ptr]
        count = 1
        while queue:
            ptr = queue.pop(0)
            if ptr.left_child:
                queue.append(ptr.left_child)
                count += 1
            if ptr.right_sibling:
                queue.append(ptr.right_sibling)
                count += 1
        count += 1
        return count
         
    def fix_tree(self, node):
        if self.left_child == node:
            if node.right_sibling:
                self.left_child = node.right_sibling
            else:
                self.left_child = None
        else:
            ptr = self.left_child
            while ptr.right_sibling != node:
                ptr = ptr.right_sibling
            ptr.right_sibling = node.right_sibling # either None or the node's
        
        