import ast
import tokenize
from io import BytesIO
import astor

def capture_comments(source_code):
    tokens = tokenize.tokenize(BytesIO(source_code.encode('utf-8')).readline)
    comments = {}
    for toktype, tokval, (srow, _), _, _ in tokens:
        if toktype == tokenize.COMMENT:
            comments[srow] = tokval  # Store line number and comment
    return comments

def parse_code_to_ast(source_code):
    return ast.parse(source_code)

class FunctionModifier(ast.NodeTransformer):
    def __init__(self, comments):
        self.comments = comments

    def visit_FunctionDef(self, node):
        # Check if there's a comment on the line immediately after the function signature
        if self.comments.get(node.lineno + 1) == "#--":
            # Example modification: add a print statement to the function body
            new_stmt = ast.parse("print('This function was modified.')")
            node.body.insert(0, new_stmt)
        return node

def modify_and_rewrite_functions(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
            source_code = file.read() 
            
    comments = capture_comments(source_code)
    ast_tree = parse_code_to_ast(source_code)
    print(comments)
    # Create a transformer and apply it
    transformer = FunctionModifier(comments)
    modified_tree = transformer.visit(ast_tree)

    # Convert the modified AST back to source code using astor
    modified_code = astor.to_source(modified_tree)

    # Write the modified code back to the file
    with open(filepath, 'w') as file:
        file.write(modified_code)



# Save the modified source code back to a Python script file
file_path = "test.py"
modify_and_rewrite_functions(file_path)
