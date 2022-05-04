from pygments.lexers import get_lexer_by_name
from pygments.formatters import Terminal256Formatter
from pygments import highlight
from pygments.style import Style
from pygments.token import Token

class Coverage:
    class ExecutedStyle(Style):
        default_style = ""
        styles = {
            Token : "ansiblue bg:ansigreen"
        }

    class SkippedStyle(Style):
        default_style = ""
        styles = {
            Token : "ansiblue bg:ansiyellow"
        }
                
    def __init__(self, cov_file = None):
        self.cov_file = cov_file
    
    def summary(self, node):
        if self.cov_file:
            source = node.source
            executed = self.cov_file[str(node.id)]
            executed = list(set(executed))
            skipped = []
            if executed:
                skipped = [line for line in list(set(source) - set(executed))]
            
            executed_pct = round((len(executed) / len(source)) * 100)
            skipped_pct = round((len(skipped) / len(source)) * 100)
                        
            header = f"Name\t\tTotal\t\tExecuted\tSkipped"
            values_row = f"{node.name}\t\t{len(source)}\t\t{len(executed)}({executed_pct}%)\t\t{len(skipped)}({skipped_pct}%)"
            
            lexer = get_lexer_by_name("python", stripnl=False)
        
            formatter = Terminal256Formatter(style = Coverage.ExecutedStyle, full = True)
            executed_lines = {line : highlight(source[line], lexer, formatter) 
                              for line in executed}

            formatter = Terminal256Formatter(style = Coverage.SkippedStyle, full = True)
            skipped_lines = {line : highlight(source[line], lexer, formatter)
                             for line in skipped}

            print(header, values_row, sep="\n")
            for line in source:
                if line in skipped_lines:
                    print(line, skipped_lines[line], end="")
                else:
                    print(line, executed_lines[line], end="")            