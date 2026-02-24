import ast
import os

directories = ['handlers', 'services', 'scheduler']
output_lines = []
counter = 1

class MessageVisitor(ast.NodeVisitor):
    def __init__(self, filepath):
        self.filepath = filepath
        self.current_function = None

    def visit_FunctionDef(self, node):
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = None
        
    def visit_AsyncFunctionDef(self, node):
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = None

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            if func_name in ['answer', 'reply', 'send_message'] or (isinstance(node.func, ast.Name) and node.func.id == 'safe_send_message'):
                
                # Try to extract text from args or kwargs
                text_val = None
                
                # Check args
                if node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.Constant):
                        text_val = arg.value
                    elif isinstance(arg, ast.JoinedStr):
                        # reconstruct f-string loosely
                        parts = []
                        for val in arg.values:
                            if isinstance(val, ast.Constant):
                                parts.append(str(val.value))
                            elif isinstance(val, ast.FormattedValue):
                                parts.append("{...}")
                        text_val = "".join(parts)
                        
                # Check kwargs 
                for kw in node.keywords:
                    if kw.arg == 'text':
                        if isinstance(kw.value, ast.Constant):
                            text_val = kw.value
                        elif isinstance(kw.value, ast.JoinedStr):
                            parts = []
                            for val in kw.value.values:
                                if isinstance(val, ast.Constant):
                                    parts.append(str(val.value))
                                elif isinstance(val, ast.FormattedValue):
                                    parts.append("{...}")
                            text_val = "".join(parts)
                            
                if text_val:
                    global counter
                    clean_text = text_val.replace('\n', ' \\n ')
                    desc = f"Сообщение в файле {os.path.basename(self.filepath)}, функция {self.current_function}"
                    output_lines.append(f"{counter} - {desc} - \"{clean_text}\"\n")
                    counter += 1
                    
        self.generic_visit(node)

for d in directories:
    for root, _, files in os.walk(d):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    try:
                        tree = ast.parse(f.read(), filename=path)
                        visitor = MessageVisitor(path)
                        visitor.visit(tree)
                    except Exception as e:
                        pass

with open('ALL_MSGS_CLEAN.txt', 'w', encoding='utf-8') as out:
    out.write("\n".join(output_lines))
