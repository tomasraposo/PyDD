from etnode import ETNode
from query import Query
from rich import print
import json

class ExecutionTree:    
    def __init__(self, root = None):
        self.root = root
        self.size = 0
        
    def insert_at(self, parent, node):
        if not self.root:
            self.root = node
        else:
            ptr = parent.left_child
            if ptr:
                if ptr.right_sibling:
                    while ptr.right_sibling:
                        ptr = ptr.right_sibling
                    ptr.right_sibling = node
                node.parent = parent
                ptr.right_sibling = node
            else:
                node.parent = parent
                parent.left_child = node
        self.size += 1
    
    @classmethod
    def to_ascii(cls, node, curr_id, prefix = ""):
        def format_tree(node, curr_id, prefix = "", ls = []):
            connector = "└── " 
            if not node.is_terminal():
                connector = "├── "
            st = f"{prefix}{connector}"
            if node.state == ETNode.State.INVALID:
                st += f"[red]{str(node)}[/red]"
            else:
                st += f"[yellow]{str(node)}[/yellow]"
            if node.id == curr_id:
                st += f"\t[gray]<-[/gray]"
            ls.append(st + "\n")
            children = node._get_children()
            for child in children:
                new_prefix = prefix
                if node.is_terminal():
                    new_prefix += "    "
                else:
                    new_prefix += "│   "
                format_tree(child, curr_id, new_prefix, ls)
            return ls
        tree = format_tree(node, curr_id, "", [])
        return tree

    @classmethod
    def to_json(cls, node, curr_id):
        t_table = {
            "tree" : {
                "nodes" : [],
                "edges" : {},
            }
        }
        YELLOW = "#f7dc6f"
        BLUE = "#3498db"
        def populate_table(node, nodes, edges):
            if not node:
                return
            nodes.append({"id" : node.id,
                          "label" : str(node),
                          "title" : f"Arguments\n{str(node.params)}\n \
                                     Modified\n{str(node.m_params)}\n \
                                     Returned\n{str(node.result)}",
                         "color" : {
                             "background": YELLOW,
                             "border": YELLOW
                             }
                         })
            if node.id == curr_id:
                curr_node = nodes[-1]
                curr_node["color"] = {
                    "background": BLUE,
                    "border": BLUE
                }
            if node.left_child:
                edges.setdefault(node.id, []).append({"from" : node.id, "to" : node.left_child.id})
                populate_table(node.left_child, nodes, edges)
            if node.right_sibling:
                edges.setdefault(node.parent.id, []).append({"from" : node.parent.id, "to" : node.right_sibling.id})
                populate_table(node.right_sibling, nodes, edges)

        populate_table(node, **t_table["tree"])
        edge_list = []
        for ls in t_table["tree"]["edges"].values():
            edge_list.extend(ls)
        t_table["tree"]["edges"] = edge_list
        message = {"type" : "tree", "nID" : curr_id, **t_table}
        return [json.dumps(message)]
                    
    def height(self, root):
        if not root:
            return 0
        h = 0
        ptr = root.left_child
        while ptr:
            h = max(h, self.height(ptr))
            ptr = ptr.right_sibling
        return h + 1
                   
    def visit(self, node):
        print(str(node))
        