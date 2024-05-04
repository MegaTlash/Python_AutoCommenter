import argparse
import sys
import token
import os
import tokenize
import ast
from io import StringIO
import json


def parse_args():
    parser = argparse.ArgumentParser(description="Strip comments and docstrings from Python functions in a file.")
    parser.add_argument("--filename", default="test_file.py", help="Python file to process")
    parser.add_argument("--out_filename", default="datasets/dataset_strings.json", help="Json file output")
    parser.add_argument("--in-place", action="store_true", help="Modify the file in-place")
    return parser.parse_args()

def do_file(functions, fname, in_place=False):
    if in_place:
        nfname = fname
    else:
        nfname = fname[:-3] + '_modified.py'
    
    with open(nfname, "w", encoding='utf-8') as mod:
        last_lineno = -1
        last_col = 0
        for func in functions:
            source = StringIO("\n" + func)
            tokgen = tokenize.generate_tokens(source.readline)
            prev_toktype = tokenize.INDENT
            for toktype, ttext, (slineno, scol), (elineno, ecol), ltext in tokgen:
                if 0:   # Change to if 1 to see the tokens fly by.
                    print("%10s %-14s %-20r %r" % (
                        tokenize.tok_name.get(toktype, toktype),
                        "%d.%d-%d.%d" % (slineno, scol, elineno, ecol),
                        ttext, ltext
                        ))
                if slineno > last_lineno:
                    last_col = 0
                if scol > last_col:
                    mod.write(" " * (scol - last_col))
                if toktype == token.STRING and prev_toktype == token.INDENT:
                    # Docstring
                    mod.write("#--")
                elif toktype == tokenize.COMMENT:
                    # Comment
                    mod.write("##\n")
                else:
                    mod.write(ttext)
                prev_toktype = toktype
                last_col = ecol
                last_lineno = elineno

    return nfname


def transform_function(func_code):
    """ Simulate a transformation of function code, could be adding comments, etc. """
    # Example transformation: Just appending a comment about processing
    source = StringIO(func_code)
    tokgen = tokenize.generate_tokens(source.readline)
    prev_toktype = tokenize.INDENT  
    code_string = ""
    last_lineno = -1
    last_col = 0
    for toktype, ttext, (slineno, scol), (elineno, ecol), ltext in tokgen:
        if 0:   # Change to if 1 to see the tokens fly by.
            print("%10s %-14s %-20r %r" % (
                tokenize.tok_name.get(toktype, toktype),
                "%d.%d-%d.%d" % (slineno, scol, elineno, ecol),
                ttext, ltext
                ))
        if slineno > last_lineno:
            last_col = 0
        if scol > last_col:
           code_string += " " * (scol - last_col)
        if toktype == token.STRING and prev_toktype == token.INDENT:
            # Docstring
            code_string += "#--"
        elif toktype == tokenize.COMMENT:
            # Comment
            code_string += "##\n"
        else:
            code_string += ttext
        prev_toktype = toktype
        last_col = ecol
        last_lineno = elineno

    return code_string

def append_to_json(input_file, json_file):
    """ Append new functions extracted from input_file to json_file. """

    with open(input_file, 'r', encoding='utf-8') as file:
        source_code = file.read()

    functions, imports = extract_functions_from_file(source_code)
    existing_data, last_index = load_existing_data(json_file)
    new_data = []
    imports_string = "\n".join(imports)
    
    for idx, func in enumerate(functions, start=last_index + 1):
        item = {
            'id': idx,
            'input': func,
            'output': transform_function(func),
            'imports': imports_string
        }
        new_data.append(item)
    
    # Combine old and new data
    combined_data = existing_data + new_data

    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(combined_data, file, indent=4)

    print(f"Appended {len(functions)} functions to {json_file}")

def load_existing_data(file_path):
    """ Load existing data from a JSON file and find the highest index used. """
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        if data:  # Check if the data is not empty
            last_index = max(item['id'] for item in data)  # Find the maximum id used so far
            return data, last_index
    return [], 0  # Return empty list and start index 0 if file does not exist



def extract_functions_from_file(code):
    root = ast.parse(code)
    items = []
    imports = []
    for node in ast.walk(root):
        if isinstance(node, (ast.FunctionDef)):
            #print(ast.get_docstring(node))
            item_code = ast.unparse(node)
            items.append(item_code)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            import_code = ast.unparse(node)
            imports.append(import_code)
    return items, imports

if __name__ == '__main__':
    args = parse_args()
    try:

        append_to_json(args.filename, args.out_filename)
        print(f"Processed file saved as: {args.out_filename}")
    except Exception as e:
        print(f"Error processing the file: {e}")