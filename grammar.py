import re
import copy
from astor import to_source
from ast_transformer import ASTTransformer
import ast
import astunparse
from rich import print
from rich.syntax import Syntax

class Grammar:
    def __init__(self, terminals = (), start_symbol = None):
        self.terminals = {*terminals}
        self.nonterminals = {start_symbol}
        self.start_symbol = start_symbol
        self.rules = {}
        self.program = []
        self.test_results = {}
        self.best_match = None
        self.sem_specs = None
        
    def add_rule(self, symbol, rule):
        if rule and isinstance(rule, tuple):
            try:
                self.rules[symbol].update(rule)
            except KeyError:
                self.rules[symbol] = {*rule}
        self.nonterminals.add(symbol)
    
    def tokenize(self, word):
        tokens = re.split("[\s]+", word)
        return tokens
    
    def _len(self, word):
        _, terminals = zip(*self.terminals)
        terminals = list(terminals)
        terminals.remove("+")
        terminals.append("\+")
        terminal_tokens = re.findall(f"({'|'.join(terminals)})", word)
        return len(terminal_tokens)

    def is_nonterminal(self, symbol):
        return symbol in self.nonterminals
            
    def is_terminal(self, symbol):
        return not self.is_nonterminal(symbol)

    def is_valid(self, word):
        return all([self.is_terminal(token) for token in self.tokenize(word)])
    
    def remove_equiv(self, programs):
        equiv = []
        results = []
        for program in programs:
            p_type, p = program
            outputs = []
            for inputs, _ in self.sem_specs:
                try:
                    outputs.append(eval(program[1], inputs.copy()))
                except Exception:
                    pass
            builtins = self.rules["BuiltinId"]
            if any(builtin in p for builtin in builtins) \
                or outputs not in results:
                results.append(outputs)
                equiv.append(program)
        return equiv
            
    def is_match(self, args, p):
        f_name, tree, faulty_node, ret_val = args
        tree = copy.deepcopy(tree)
        to_source(tree)
        tests = {}
        match = False
        if isinstance(p, tuple):
            p = p[1]
        mutated_tree = ASTTransformer(p, faulty_node).visit(tree)
        mutated_tree = ast.fix_missing_locations(mutated_tree) # fix up line numbers
        
        mutated_source = astunparse.unparse(mutated_tree.body[0])
        mutated_source = compile(mutated_source, filename = "<string>", mode = "exec")

        for inputs, outputs in self.sem_specs:
            _locals = copy.deepcopy(inputs)
            if isinstance(outputs, str):
                outputs = _locals[outputs]
            try:
                exec(mutated_source, globals())
                temp = globals()[f_name](**_locals)
                try:
                    res = _locals[ret_val]
                except KeyError:
                    res = temp
                if outputs == res:
                    match = True
                else:
                    match = False
            except Exception as e:
                match = False
            finally:
                tests.setdefault(p, []).append((inputs, match))
        if p and p not in self.test_results:
            self.test_results[p] = (tests[p], self.score(tests))
        del globals()[f_name]
        match = all(match for _, match in tests[p])
        return match
    
    def score(self, tests):
        score = 0
        p = list(tests)[0]
        cases, results = zip(*tests[p])
        total_tests = len(cases)
        total_passed = results.count(True)
        score = float(total_passed / total_tests)
        
        if self.best_match:
            bm_p, bm_score = self.best_match   
            if score > bm_score:
                self.best_match = (p, score)
        else:
            self.best_match = (p, score)
        return score
    
    def bus(self, args):
        f_name, tree, faulty_node, ret_val = args
        bank = [*self.terminals]
        size = 1
        bound = 10
        while size <= bound:
            print(f"Running iteration of size {size}...")
            for p in bank:
                if self.is_match(args, p):
                    p = Syntax(p[1], "python", theme="ansi_light")
                    print("\nGenerated matching expression: ", p)
                    return p
            bank += self.grow(bank, size)
            size += 1
    
    def grow(self, bank, size):
        temp_bank = []
        rhs = []
        for nonterminal, rules in self.rules.items():
            for rule in rules:
                def expand(prod_rule):
                    program = " ".join(prod_rule)
                    if program not in bank:
                        for i, token in enumerate(prod_rule):
                            for j, p in enumerate(bank):
                                p_type, p = p
                                if self.is_nonterminal(token):
                                    if p_type == token or \
                                        p_type in self.rules[token]:
                                        temp = prod_rule.copy()
                                        temp[i] = p
                                        expand(temp)
                        if self.is_valid(program) and \
                            self._len(program) == size:
                            node = (nonterminal, program)
                            if node not in temp_bank:
                                temp_bank.append(node)
                expand(self.tokenize(rule))        
        temp_bank = self.remove_equiv(temp_bank)
        return temp_bank

    def iddfs(self, args):
        f_name, tree, faulty_node, ret_val = args
        d = 1
        while not self.dfs(args, self.start_symbol, d):
            print(f"Running iteration of depth {d}...")
            d += 1
    
    def dfs(self, args, p, depth):
        if self.is_valid(p):
            if self.is_match(args, p):
                p = Syntax(p, "python", theme="ansi_light")
                print("\nGenerated matching expression: ", p)
                return True
        children = self.children(p)
        if not children or depth == 0:
            return False
        for c in children:
            result = self.dfs(args, c, depth - 1)
            if result:
                return True
        return False

    def bfs(self, args):
        f_name, tree, faulty_node, ret_val = args
        queue = [self.start_symbol]
        it = 0
        while queue:
            p = queue.pop(0)
            children = self.children(p)
            if children:
                for c in children:
                    if self.is_valid(c):
                        if self.is_match(args, c):
                            c = Syntax(c, "python", theme="ansi_light")
                            print("\nGenerated matching expression: ", c)
                            return c
                    queue.append(c)
            queue = sorted(queue, key=len)
            it += 1
        
    def children(self, p):        
        nt = None
        p_tokens = self.tokenize(p)
        for i, p_token in enumerate(p_tokens):
            if self.is_nonterminal(p_token):
                nt = (i, p_token)
                break
        if nt:
            nt_i, nt_token = nt
            children_ = []
            for rule in self.rules[nt_token]:
                temp = p_tokens.copy()
                temp[nt_i] = rule 
                temp = " ".join(temp)
                children_.append(temp)
            return children_
        