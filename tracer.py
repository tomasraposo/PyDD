from etnode import ETNode
from event import Event
from datetime import datetime
import sys
import os
import inspect
import gc

  
class Tracer:
    def __init__(self, exec_tree, trace_file, cov_file):
        self.exec_tree = exec_tree
        self.default_tracer = sys.gettrace()
        self.current_node = None
        self.source = []
        self.stack_level = 0
        self.last_vars = {}
        self.trace_file = trace_file
        self.cov_file = cov_file
                               
    def excepthook(self, exc_type, exc_value, exc_tb):
        exc_type_name = exc_type.__name__
        exc_line = exc_tb.tb_lineno
        exc_file = exc_tb.tb_frame.f_code.co_filename
        print(f'Exception "{exc_type_name}" in file "{exc_file}" at line {exc_line}')
        sys.__excepthook__(exc_type, exc_value, exc_tb)
    
    def track_event(self, node_id, event_record):
        self.trace_file.setdefault(node_id, []).append(event_record)    
    
    def track_cov(self, node_id, lineno):
        self.cov_file.setdefault(node_id, []).append(lineno)
    
    def __call__(self, frame, event, arg):
        package_name = frame.f_globals["__name__"].split('.')[0]        

        co = frame.f_code 
        f_name = co.co_name 
        f_params = frame.f_locals
        line_no = frame.f_lineno
        file_name = co.co_filename
        f_globals = frame.f_globals
        co_names = co.co_names
        co_freevars = co.co_freevars

        if f_name == "<module>":
            self.source = inspect.getsource(frame).split("\n")
        
        if "self" in frame.f_locals:
            obj = frame.f_locals["self"]
            class_name = obj.__class__.__name__
            f_name = class_name + '.' + frame.f_code.co_name
            if class_name == self.__class__.__name__:
                return
                                                           
        sanitised_params = self.sanitise_params(f_name, f_params,f_globals, co_names, co_freevars)
                       
        parent_frame = frame.f_back
        parent_name = parent_frame.f_code.co_name if parent_frame else ""
        
        updated_locals = self.track_locals(event, line_no, sanitised_params)        
        self.last_vars = sanitised_params.copy()

        if event == "line":
            current_line = self.source[line_no - 1]
            if updated_locals[line_no]:
                self.current_node.update(updated_locals)

            now = datetime.now()
            timestamp = datetime.timestamp(now)
            updated_locals = updated_locals[line_no] if updated_locals else {}
            event_record = Event(timestamp, event, line_no, current_line, updated_locals)
            
            if self.current_node:
                self.track_event(str(self.current_node.id), event_record)
                self.track_cov(str(self.current_node.id), line_no)
                # updated m_params
                for var, value in self.last_vars.items():
                    if var in self.current_node.params:
                        self.current_node.m_params[var] = value
            
        if event == "call":
            source_lines, starting_lineno = inspect.getsourcelines(frame)
            source = {starting_lineno + i: line for i, line in enumerate(source_lines)} 
            params = sanitised_params.copy()
            f_sig = self.get_signature(co)
            next_node = ETNode(self.stack_level, f_name, f_sig or "", params, source)
            self.exec_tree.insert_at(self.current_node, next_node)            
            self.current_node = next_node
            self.stack_level += 1
            
            self.track_cov(str(self.current_node.id), line_no)
        
        elif event == "return" or event == "exception":
            if self.current_node:
                if event == "exception":
                    arg = f"{str(arg[0].__name__)} : {arg[1]}"
                self.current_node.result = arg
                self.current_node = self.current_node.parent
            return
        return self
    
    def __enter__(self):
        sys.excepthook = self.excepthook
        sys.settrace(self)
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type:
            print(exc_type, exc_value, exc_traceback)
            return False       
        self.current_node = None
        sys.settrace(self.default_tracer)
        sys.excepthook = sys.__excepthook__
        return True
    
    def get_signature(self, co):
        obj = self.get_object(co)
        if obj:
            f_sig = inspect.signature(obj)
            return str(f_sig)
                    
    def check_str(self, str, start_char, end_char):
        return str.startswith(start_char) and \
               str.endswith(end_char)
    
    def is_class_decl(self, f_locals, f_name):
        if "__qualname__" in f_locals and \
            f_locals["__qualname__"] == f_name:
            return True
        return False
            
    def get_object(self, co):
        for obj in gc.get_referrers(co):
            if hasattr(obj, "__code__") and obj.__code__ is co:
                return obj
        
    def get_globals(self, f_globals, co_names):
        global_vars = {}
        for name in co_names:
            if name in f_globals:
                if not callable(f_globals[name]) and not self.check_str(name, "__", "__"):
                    global_vars["global " + name] = f_globals[name]
        return global_vars
    
    def sanitise_params(self, f_name, f_locals, f_globals, co_names, co_freevars):
        f_params = {}
        if self.is_class_decl(f_locals, f_name) or f_name == "<module>":
            return f_params
        for k, v in list(f_locals.items()):
            if self.check_str(k, "__", "__"):
                f_locals.pop(k)
            elif hasattr(v, "__dict__"):
                d = dict(vars(v))
                for key, val in list(d.items()):
                    if hasattr(val, "__dict__"):
                        nested_dict = dict(vars(val))
                        d[key] = self.sanitise_params(key, nested_dict, f_globals, co_names, co_freevars)
                    else:
                        d[key] = val
                f_params[k] = d
            elif k in co_freevars:
                f_params["freevar " + k] = f_locals[k]
            elif hasattr(v, "copy"):
                f_params[k] = v.copy()
            else:
                f_params[k] = v
        global_vars = self.get_globals(f_globals, co_names)
        f_params.update(global_vars)
        return f_params 

    def track_locals(self, event, f_lineno, f_locals):
        if self.current_node:
            update = {f_lineno : {}}
            ptr = update[f_lineno]
            last_locals = {}
            last_locals.update(self.current_node.params)
            for d in self.current_node.locals.values():
                last_locals.update(d)
            for k, v in f_locals.items():
                if k not in last_locals or last_locals[k] != v:
                    ptr[k] = v
            return update