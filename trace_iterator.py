class TraceIterator:
    def __init__(self, code):
        self.trace = code
        self.index = 0

    def next(self):
        self.index += 1
        if self.index > len(self.trace) - 1:
            self.index = len(self.trace) - 1
            raise StopIteration
        return self.trace[self.index]
            
    def prev(self):
        self.index -= 1
        if self.index < 0:
            self.index = 0
            raise StopIteration
        return self.trace[self.index]

    def curr(self):
        try:
            result = self.trace[self.index]
        except IndexError:
            raise StopIteration
        return result
        
    def __iter__(self):
        return self
    