from dataclasses import dataclass
from etnode import ETNode

@dataclass
class Query:
    node: ETNode
    question: str
    answer: str