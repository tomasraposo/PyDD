from grammar import Grammar
import ast
import astunparse
from astor import to_source
from textwrap import dedent
import re
import copy
import builtins
import time

class ProgramRepairer:
    def __init__(self, f_name, source, lineno, ret_val, sem_specs = None):
        self.f_name = f_name
        self.source = dedent(source)
        self.tree = ast.parse(dedent(source))
        self.faulty_node = (None, int(lineno))
        self.ret_val = ret_val
        self.sem_specs = sem_specs
        self.grammar = None
        self.accepted_types = [ast.Compare, ast.Assign]

    @classmethod
    def parse_expr(cls, expr):
        try:
            parsed = ast.literal_eval(expr)
        except Exception:
            pass
        else:
            return parsed

    @classmethod
    def parse_sem_specs(cls, spec):
        sem_specs = []
        inputs = {}
        ret_val = None
        for val in spec.split(";"):
            val = val.strip()
            if "=" in val:
                arg, arg_val = map(str.strip, val.split("="))
                arg_val = ProgramRepairer.parse_expr(arg_val)
                if arg_val:
                    inputs[arg] = arg_val
            else:
                ret_val = ProgramRepairer.parse_expr(val)
        if inputs and ret_val:
            sem_specs.append((inputs, ret_val))
        return sem_specs
    
    def repair(self, repair_strategy):
        self.make_grammar()
        start_time = time.time()
        print("\nSynthesizing... ")
        faulty_node, _ = self.faulty_node
        tree = copy.deepcopy(self.tree)
        args = (self.f_name, tree, faulty_node, self.ret_val)
        strategy = getattr(self.grammar, repair_strategy)
        if strategy:
            strategy(args)
        print(f"\nFinished in {round(time.time() - start_time, 6)}") 
        
    def walk_tree(self):
        ids = []
        builtin_ids = []
        _, lineno = self.faulty_node
        for node in ast.walk(self.tree):
            if hasattr(node, "lineno"):
                if node.lineno == lineno and \
                    type(node) in self.accepted_types:
                        self.faulty_node = (node, node.lineno)  
            if isinstance(node, ast.Name):
                if node.id in vars(builtins):
                    if node.id not in builtin_ids:
                        builtin_ids.append(node.id)
                else:
                    if node.id not in ids:
                        ids.append(node.id)
            # elif isinstance(node, ast.Compare):
                # print(node.__dict__)
                # pass
                        
        return ids, builtin_ids
        
    def make_grammar(self):
        ids, builtin_ids = self.walk_tree()
        start_symbol = "Expr"
        # digits = ["0", "1"]
        # binops = ["+", "-", "*", "/", "==", "<", ">", "!=", ">=", "<="]
        binops = ["+", "==", "<", ">", "!="]
        terminals = []
        # terminals += [("Num", digits[0]), ("Num", digits[1])]
		
        for name in ids:
            terminals.append(("Id", name))        
        for op in binops:
            terminals.append(("BinOp", op))
        
        for name in builtin_ids:
            terminals.append(("BuiltinId", name))
            
        self.grammar = Grammar(terminals = terminals, start_symbol= start_symbol)
        self.grammar.add_rule("Expr", ("Id", "FnCall", "Expr BinOp Expr"))
        self.grammar.add_rule("FnCall", ("BuiltinId ( ArgsList )",))
        self.grammar.add_rule("BuiltinId", (*builtin_ids,))
        self.grammar.add_rule("ArgsList", ("Id", ))
        self.grammar.add_rule("BinOp", (*binops,))
        self.grammar.add_rule("Id", (*ids,))
        # self.grammar.add_rule("Num", (*digits,))
        if self.sem_specs:
            self.grammar.sem_specs = self.sem_specs


