from code import interact
# from sre_parse import State
from oracle import Terminal, Browser
from query import Query
from rich import print
from etnode import ETNode
import json
 
class DebuggingStrategy:
    def __init__(self, exec_tree, interactive, pydd_repl, oracle, tree_formatter):
        self.exec_tree = exec_tree
        self.interactive = interactive
        self.pydd_repl = pydd_repl
        self.oracle = oracle
        self.tree_formatter = tree_formatter
    
    def single_stepping(self):
        if not self.exec_tree.root:
            return
        queries = []        
        stack = []
        visited = []
        root = self.exec_tree.root
        stack.append(root)
        while stack:
            ptr = stack.pop()
            visited.append(ptr)
            if ptr.left_child:
                stack.append(ptr.left_child)
            if ptr.right_sibling:
                stack.append(ptr.right_sibling)
        while visited:
            ptr = visited.pop()
            
            print(*self.tree_formatter(self.exec_tree.root, ptr.id))
 
            answer = self.oracle.query(ptr)
        
            if self.interactive and answer == "No":
                self.pydd_repl(ptr)

            if answer == "No":
                ptr.state = ETNode.State.INVALID
                print(f"[bold red]Buggy node found at {ptr}[/bold red]")
                return
            ptr.state = ETNode.State.VALID
                                            
    def top_down(self):
        if not self.exec_tree.root:
            return
        queries = []
        queue = []
        ptr = self.exec_tree.root
        while ptr:
            queue.append(ptr)
            ptr = ptr.right_sibling
        while queue:
            ptr = queue[0]
            queue.pop(0)

            print(*self.tree_formatter(self.exec_tree.root, ptr.id))
 
            answer = self.oracle.query(ptr)

            if self.interactive and answer == "No":
                self.pydd_repl(ptr)
            
            if answer == "Yes":
                ptr.state = ETNode.State.VALID
                if ptr.is_terminal():
                    print(f"[bold red]Buggy node found at {ptr.parent}[/bold red]")
                    return
                pptr = ptr.parent
                pptr.left_child = ptr.right_sibling
                ptr = ptr.right_sibling
            elif answer == "No":
                ptr.state = ETNode.State.INVALID
                ptr.right_sibling = None
                if ptr.is_leaf():
                    print(f"[bold red]Buggy node found at {ptr}[/bold red]")
                    return
                else:
                    self.exec_tree.root = ptr
                    ptr = ptr.left_child
                    queue = []
            while ptr:
                queue.append(ptr)
                ptr = ptr.right_sibling

                                
    def heaviest_first(self):
        if not self.exec_tree.root:
            return
        queries = []
        queue = []
        ptr = self.exec_tree.root
        weights = {}
        while ptr:
            queue.append(ptr)
            ptr = ptr.right_sibling

        while queue:
            for node in queue:
                weights[str(node.id)] = (node, node.size())
            
            queue = []
            if weights:
                heaviest = max(weights, key = lambda x : weights[x][1])
                
            ptr, _ = weights[heaviest]
            del weights[heaviest] # pop from dictionary
            
            print(*self.tree_formatter(self.exec_tree.root, ptr.id))
 
            answer = self.oracle.query(ptr)
            
            if self.interactive and answer == "No":
                self.pydd_repl(ptr)
                            
            if answer == "Yes":
                ptr.state = ETNode.State.VALID
                if ptr.is_terminal():
                    print(f"[bold red] Buggy node found at {ptr.parent} [/bold red]")
                    return
                pptr = ptr.parent
                pptr.fix_tree(ptr)
                ptr = ptr.right_sibling
            elif answer == "No":
                ptr.state = ETNode.State.INVALID
                ptr.right_sibling = None
                if ptr.is_leaf():
                    print(f"[bold red] Buggy node found at {ptr} [/bold red]")
                    return
                else:
                    self.exec_tree.root = ptr
                    ptr = ptr.left_child
                    queue = []
                    weights = {}
            while ptr:
                queue.append(ptr)
                ptr = ptr.right_sibling


                      
    def _cleanup(self, weights, node, node_weight):
        root = self.exec_tree.root        
        ptr = node
        while ptr != root:
            # subtract the node weight from the parent trees (recompute their weights)
            weights[ptr.parent.id][1] -= node_weight 
            ptr = ptr.parent

        if not node:
            return
        stack = []
        if node.left_child:
            stack = [node.left_child]
            while stack:
                ptr = stack.pop()
                if ptr:
                    del weights[ptr.id]
                if ptr.right_sibling:
                    stack.append(ptr.right_sibling)
                if ptr.left_child:
                    stack.append(ptr.left_child)
    
    def divide_and_query(self):
        if not self.exec_tree.root:
            return
        queries = []
        ptr = self.exec_tree.root
        root_id = ptr.id
        
        def get_weights(root, weights):
            if not root:
                return
            weights[root.id] = [root, 1]
            lst = get_weights(root.left_child, weights)
            rst = get_weights(root.right_sibling, weights)
            if lst:
                weights[root.id][1] += weights[lst.id][1]
            if rst:
                weights[root.parent.id][1] += weights[rst.id][1]
            return root
        
        weights = {}
        get_weights(ptr, weights)
        
        _, total_weight = weights[0]
        best_weight = total_weight // 2
               
        # find the nearest value to best_weight by abs of the 
        # difference between the target value and the node size
        best_guess = lambda e: abs(e[1][1] - best_weight) 
        while True:
            if not weights:
                return
            best = min(weights.items(), key = best_guess) # get best guess

            node_id, (node, node_weight) = best
            del weights[node_id] # remove from dict not to check it again

            print(*self.tree_formatter(self.exec_tree.root, node_id))
 
            answer = self.oracle.query(node)
            
            if self.interactive and answer == "No":
                self.pydd_repl(node)
            
            if answer == "Yes":
                node.state = ETNode.State.VALID
                if node.is_terminal() and node.parent.state == ETNode.State.INVALID:
                    print(f"[bold red] Buggy node found at {node.parent}[/bold red]")
                    return

                pptr = node.parent
                pptr.fix_tree(node)  # perform tree adjustment

                self._cleanup(weights, node, node_weight)
                
            elif answer == "No":
                node.state = ETNode.State.INVALID
                node.right_sibling = None
                if node.is_leaf():
                    print(f"[bold red] Buggy node found at {node} [/bold red]")
                    return
                else:
                    root_id = node.id # set the node to be the new tree root
                    self.exec_tree.root = node
                    weights = {}
                    get_weights(node, weights)

            _, total_weight = weights[root_id]
            best_weight = total_weight // 2
            