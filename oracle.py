from abc import ABC, abstractclassmethod, abstractmethod
from query import Query
import json
from rich.prompt import Confirm
from rich import print
from rich.text import Text
from rich.panel import Panel

class Oracle(ABC):
    @abstractmethod
    def query(cls, ptr):
        pass
    
class Terminal(Oracle):
    def __init__(self, queries):
        self.queries = queries

    def query(self, ptr):
        question = f"Query: {str(ptr)}"
        question_marker = ["\n[", ("?", "yellow"), "] "]
        text = Text.assemble(*question_marker, (question, "gray"))
        print(text)       
        q_params = "Yes" if Confirm.ask("Inspect parameters and return value?") else "No"
        if q_params == "Yes":
            print(*(Panel.fit(str(ptr.params), title = "parameters"), 
                    Panel.fit(str(ptr.m_params), title = "modified parameters"),
                    Panel.fit(str(ptr.result), title = "return value")))
            # print(*ptr.params_panel())
        q_state = "Yes" if Confirm.ask("Is it correct?") else "No"
        query = Query(ptr, question, q_state) 
        self.queries.append(query)
        return q_state
    
    
class Browser(Oracle):
    def __init__(self, queries):
        self.queries = queries

    def query(self, ptr):
        question = f"Query: {str(ptr)}"
        print(json.dumps({"type" : "id", "id" : ptr.id}))
        answer = json.loads(input("").strip())
        query = Query(ptr, question, answer) 
        self.queries.append(query)
        return answer