#!/usr/bin/env python3

from oracle import Terminal, Browser
from debugging_strategy import DebuggingStrategy
from tracer import Tracer
from coverage import Coverage
from program_repairer import ProgramRepairer
from pydd_repl import PyDDRepl
from execution_tree import ExecutionTree
from trace_iterator import TraceIterator
from dill import Pickler, Unpickler
import shelve
import os
import sys
import argparse

shelve.Pickler = Pickler
shelve.Unpickler = Unpickler

class PyDD:
    def __init__(self, source_file, interactive, web, debugging_strategy, program_repair_strategy, args):
        self.source_file = source_file
        self.interactive = True if interactive == "yes" else False
        self.web = True if web == "yes" else False
        self._args = args
        self.exec_tree = ExecutionTree()
        self.traceback = ""
        self.queries = []
        self.debugging_strategy = debugging_strategy
        self.program_repair_strategy = program_repair_strategy
        self.cov = Coverage()
    
    def __enter__(self):
        trace_file, cov_file = self._args
        sys_str = ""
        for path in self._args:
            _, name = os.path.split(path)
            if os.path.isfile(path):
                sys_str += name + ", "
        if sys_str:
            sys_str = sys_str[:-2]
            if len(sys_str.split(",")) == 2:
                sys_str += ": files exist."
            else:
                sys_str += ": file exists."
            sys.exit(sys_str)
                    
        self.trace_file = shelve.open(trace_file, writeback=True)
        self.cov_file = shelve.open(cov_file, writeback=True)
        setattr(self.cov, "cov_file", self.cov_file)
        return self
        
    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type:
            print(exc_type, exc_value, exc_traceback)
            return False
        self.trace_file.close()
        self.cov_file.close()
        return True
            
    def run(self):
        if not self.exists(self.source_file):
            sys.exit(f'{self.source_file}: not found.')
        self.exec_file()
            
    def exists(self, file):
        return os.path.isfile(file)

    def exec_file(self, globals = None, locals = None):
        with open(self.source_file, "rb") as f:
            src_code = compile(f.read(), self.source_file, "exec")
            with Tracer(self.exec_tree, self.trace_file, self.cov_file):
                if not globals:
                    globals = {
                        "__file__": self.source_file,
                        "__name__" : "__main__",
                        "__builtins__" :__builtins__
                        }
                if not locals:
                    locals = globals
                try:
                    exec(src_code, globals, locals)
                except Exception as e:
                    self.traceback = sys.exc_info()
                    # print(self.traceback)
                    
    def start_debugging(self):
        oracle = None
        tree_printer = None
        if self.web:
            oracle = Browser(self.queries)
            tree_printer = ExecutionTree.to_json
        else:
            oracle = Terminal(self.queries)
            tree_printer = ExecutionTree.to_ascii
        strategy = self.debugging_strategy.replace("-", "_")
        strategy_dispatcher = getattr(DebuggingStrategy(
                                        self.exec_tree,
                                        self.interactive, 
                                        self.start_repl,
                                        oracle,
                                        tree_printer), 
                                      strategy)
        if strategy_dispatcher:
            strategy_dispatcher()
    
    def start_repl(self, node):
        if node.id == 0:
            return # skip virtual root
        execution_trace = self.trace_file[str(node.id)]
        tracer = TraceIterator(execution_trace)
        pydd_repl = PyDDRepl(node, tracer, self.program_repair_strategy, self.cov)
        pydd_repl.cmdloop(intro = None)


if __name__ == "__main__":                                             
    if sys.argv:
        _, args = sys.argv
        args = args.split()
        args = list(filter(lambda arg: arg[0] % 2 != 0, enumerate(args)))
        args = list(map(lambda e: e[1], args))
        f, i, w, d, pr, t, c = args
        with PyDD(f, i, w, d, pr, (t, c)) as debugger:
            debugger.run()
            debugger.start_debugging()