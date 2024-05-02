import ast

def extract_functions_from_file(file_path):
    with open(file_path, "r") as file:
        root = ast.parse(file.read(), filename=file_path)

    functions = []
    for node in ast.walk(root):
        if isinstance(node, ast.FunctionDef):
            # Capture function code using ast.unparse (available in Python 3.9+)
            func_code = ast.unparse(node)
            functions.append(func_code)

    return functions

functions = extract_functions_from_file(file_path="./test_file.py")
for i in functions:
    print(f"Function : \n {i}")