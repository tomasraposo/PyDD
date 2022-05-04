import cmd
import readline
from textwrap import dedent
import os

from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
import rich.box as box

from program_repairer import ProgramRepairer

history = os.path.expanduser('~/.pyddrepl_history')
history_length = 1000

class PyDDRepl(cmd.Cmd):
    prompt = "(PyDD) "   
    console = Console(log_time = False)
        
    def __init__(self, node, tracer, repair_strategy, cov):
        super().__init__()  
        self.node = node
        self.tracer = tracer
        self.breakpoints = []
        self.watchpoints = {}
        self.repair_strategy = repair_strategy
        self.cov = cov

    def preloop(self):
        if os.path.exists(history):
            readline.read_history_file(history)

    def postloop(self):
        readline.set_history_length(history_length)
        readline.write_history_file(history)

    def postcmd(self, stop, line):
        event = self.tracer.curr()
        if self.watchpoints:
            changed = self._has_changed(event.locals)
            if changed:
                self.console.print(f"Recorded change at [bold] {changed} [/bold]")
        return cmd.Cmd.postcmd(self, stop, line)
        
    def do_next(self, args):
        try:
            next_ = repr(self.tracer.next())
            next_ = Syntax(next_, "python", theme="ansi_light")
            self.console.log(next_)
        except StopIteration:
            self.console.print("[yellow]Reached end of function.[/yellow]")
              
    def do_prev(self, args):
        try:
            prev = repr(self.tracer.prev())
            prev = Syntax(prev, "python", theme="ansi_light")
            self.console.log(prev)
        except StopIteration:
            self.console.print("[yellow]Reached start of function.[/yellow]")
    
    def do_continue(self, args):
        line = self.tracer.curr().lineno
        breakpoints = sorted(filter(lambda b : int(b) >= line, self.breakpoints))
        if breakpoints:
            fst_breakpoint = breakpoints.pop(0)
            while line < int(fst_breakpoint):
                self.do_next(args)
                line = self.tracer.curr().lineno
            self.breakpoints.remove(fst_breakpoint)
        else:
            self.console.print("Nothing to stop at.")
                            
    def do_exit(self, args):
        return True
    
    def do_print(self, args):
        args = args.split()
        locals_table = self._get_locals_table(*args)
        if locals_table:
            if locals_table:
                table = Table(box=box.HORIZONTALS)
                columns = ["Line", "Name", "Value"]

                for column in columns:
                    table.add_column(column, justify = "left")

                for line in locals_table:
                    for name, value in locals_table[line].items():
                        table.add_row(*list(map(str, (line, name, value))))
                
                self.console.print(table)
    
    def do_list(self, args):
        source_str = ""
        source = self.node.source
        curr_line = self.tracer.curr().lineno
        for lineno in source:
            line = source[lineno].rstrip()
            if lineno == curr_line:
                source_str += "❱"
            source_str += f"\t{lineno} {line}\n"
        source_str = Syntax(source_str, "python", theme="ansi_light")
        self.console.log(source_str)
                
    
    def do_watch(self, args):
        cmd, args, line = self.parseline(args)
        args = line.split()
        self._set_watchpoints(*args)
        self.console.print(f"Watchpoints: {self.watchpoints}")
    
    def do_break(self, args):
        cmd, args, line = self.parseline(args)
        args = line.split()
        self._set_breakpoints(*args)
        self.console.print(f"Breakpoints: {self.breakpoints}")
    
    def do_remove(self, args):
        args = args.split()
        breakpoints = set(filter(str.isnumeric, args))
        watchpoints = set(args) - breakpoints
        if breakpoints:
            self._remove_breakpoints(*breakpoints)
            self.console.print(f"Breakpoints: {self.breakpoints}")
        if watchpoints:
            self._remove_watchpoints(*watchpoints)
            self.console.print(f"Watchpoints: {self.watchpoints}")
    
    def do_cov(self, args):
        self.cov.summary(self.node)
    
    def do_repair(self, args):
        args = args.split()
        if args:
            fault_lineno, *ret_val = args
            ret_val = " ".join(ret_val)
            source = [*self.node.source.values()]
            source = "".join(source)
            f_name = self.node.name
            self.console.print(dedent("""
                               Please provide the specification in the following format
                               [yellow]`arg0 = val0; arg1 = val1; return_value` [/yellow]
                               Press [bold]Ctrl-C[/bold] to exit the prompt.
                               """))
            
            sem_specs = []
            while True:
                try:
                    spec = input("> ")
                    spec = ProgramRepairer.parse_sem_specs(spec)
                    sem_specs.extend(spec)
                except:
                    break
 
            starting_lineno = list(self.node.source.keys())[0]
            fault_lineno = int(fault_lineno) - int(starting_lineno) + 1
            program_repairer = ProgramRepairer(f_name, source, fault_lineno, ret_val, sem_specs)
            program_repairer.repair(self.repair_strategy)
        else:
            self.help_repair()
        
    def _get_locals_table(self, *args):
        line_no = self.tracer.curr().lineno
        locals_table = {}
        for event_record in self.tracer.trace:
            if event_record.lineno > line_no: 
                break
            event_locals = event_record.locals_table(*args)
            lineno = event_record.lineno
            if event_locals:
                if lineno not in locals_table:
                    locals_table[lineno] = event_locals                
        return locals_table
    
    def _set_watchpoints(self, *args):
        print(*args)
        watched_vars = {param : None for param in args}
        if not self.watchpoints:
            self.watchpoints = watched_vars
        else:
            self.watchpoints.update(watched_vars)
        # self.console.print(f"Watchpoints: {self.watchpoints}")
    
    def _remove_watchpoints(self, *args):
        # print("Removing ", args)
        for var in args:
            if var in self.watchpoints:
                del self.watchpoints[var]
        # self.console.print(f"Watchpoints: {self.watchpoints}")
        
    def _set_breakpoints(self, *args):
        for lineno in args:
            if lineno.isnumeric() and \
                lineno not in self.breakpoints:
                self.breakpoints.append(lineno)
    
    def _remove_breakpoints(self, *args):
        for lineno in args:
            if lineno in self.breakpoints:
                self.breakpoints.remove(lineno)
        
    def _has_changed(self, *args):
        # add better formatting (e.g., lineno, etc)
        local_vars = args[0]
        changed = {}
        for var, value in local_vars.items():
            var = var.strip()
            if var in self.watchpoints:
                if self.watchpoints[var] != value:
                    changed[var] = value
        if changed:
            self.watchpoints.update(changed.copy())
        return changed
    
    def help_break(self):
        self.console.print(dedent("""
                                  Usage: [bold]break[/bold] ARGUMENT...
                                  Set line-based breakpoints.

                                  ARGUMENT:
                                      lineno
    
                                  Example:
                                    break 1
                                    break 2 3 5
                                  """))
    
    def help_continue(self):
        self.console.print(dedent("""
                                  Usage: [bold]continue[/bold]
                                  Continue execution until the next breakpoint.
                                  
                                  Example:
                                    continue
                                  """))
    
    def help_cov(self):
        self.console.print(dedent("""
                                  Usage: [bold]cov[/bold]
                                  Analyse code coverage of the current node.
                                  
                                  Example:
                                    cov
                                  """))
    
    def help_exit(self):
        self.console.print(dedent("""
                                  Usage: [bold]exit[/bold]
                                  Terminate the current interactive session.
                                  
                                  Example:
                                    exit
                                  """))
    
    def help_list(self):
        self.console.print(dedent("""
                                  Usage: [bold]list[/bold]
                                  Print the source code of the current node.

                                  Example:
                                    list
                                  """))
    
    def help_next(self):
        self.console.log(dedent("""
                                Usage: [bold]next[/bold]
                                Execute the next line.

                                Example:
                                    next
                                """))
    
    def help_prev(self):
        self.console.log(dedent("""
                                Usage: [bold]prev[/bold]
                                Execute the previous line.

                                Example:
                                    prev
                                """))
    
    def help_print(self):
        self.console.log(dedent("""
                                Usage: [bold]print[/bold] [ARGUMENT]... 
                                Print any variables in the local scope up to the currently executing line.

                                ARGUMENT:
                                    variable
    
                                Example:
                                    print foo bar
                                    print
                                """))
    
    def help_remove(self):
        self.console.log(dedent("""
                                Usage: [bold]remove[/bold] ARGUMENT...
                                Delete a breakpoint or watchpoint

                                ARGUMENT:
                                    lineno
                                    variable

                                Example:
                                    remove 4 bar
                                """))
    
    def help_repair(self):
        self.console.log(dedent("""
                                Usage: [bold]repair[/bold] LINENO RETVAL
                                Repair a given line of code
                                
                                Example:
                                    repair 1 foo
                                """))
        
    def help_watch(self):
        self.console.log(dedent("""
                                Usage: [bold]watch[/bold] [ARGUMENT]...
                                Register variables for watching.
                                
                                ARGUMENT:
                                    variable
                                
                                Example
                                    watch foo
                                    watch foo bar baz
                                """))
