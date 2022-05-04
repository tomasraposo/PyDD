import ast
from astor import to_source

class UnsupportedNode(Exception):
    """ Unsupported ast node """
    pass

class ASTTransformer(ast.NodeTransformer):
    def __init__(self, expr, node):
        self.accepted_nodes = {ast.Compare}
        self.expr = expr
        self.fault = (node.lineno, to_source(node).strip()[1:-1]) # [1:-1] remove lr parens
    
    def visit_Compare(self, node):
        source = (node.lineno, to_source(node).strip())
        if source == self.fault:
            try:
                transf_node = ast.parse(self.expr, mode = "eval")
                transf_node = transf_node.__dict__["body"]
                ast.copy_location(transf_node, node)
                ast.NodeVisitor.generic_visit(self, transf_node)
                return transf_node
            except SyntaxError:
                return node
        return node
    