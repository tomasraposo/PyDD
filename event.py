from dataclasses import dataclass

@dataclass
class Event:
    timestamp: float
    event: str
    lineno: int 
    line: str
    locals: dict
    
    def __repr__(self):
        # return f"{self.event} {self.lineno} {self.line}"
        return f"{self.lineno} {self.line}"
    
    def locals_table(self, *args):
        table = {}
        if args:
            table = {arg : self.locals[arg] 
                     for arg in args if arg in self.locals}
        else:
            table = self.locals.copy()
        return table
    
    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.lineno == other.lineno and \
                self.line == other.line
    
    def __hash__(self):
        return hash((self.lineno, self.line))