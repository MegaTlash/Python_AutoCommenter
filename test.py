import argparse
import sys
import token
import os
import tokenize
import ast
from io import StringIO
import json


def parse_args():
    parser = argparse.ArgumentParser(description=
        'Strip comments and docstrings from Python functions in a file.')
    parser.add_argument('--filename', default='test_file.py', help=
        'Python file to process')
    parser.add_argument('--out_filename', default=
        'datasets/dataset_strings.json', help='Json file output')
    parser.add_argument('--in-place', action='store_true', help=
        'Modify the file in-place')
    return parser.parse_args()


def do_file(functions, fname, in_place=False):
    """
    Write the modified functions to a file.

    Parameters
    ----------
    functions : list of str
        The modified functions.
    fname : str
        The name of the file to write to.
    in_place : bool, optional
        If True, write to the same file.  Otherwise, write to a new file
        with the same name but with a ``_modified`` suffix.

    Returns
    -------
    fname : str
        The name of the file written to.

    """
    if in_place:
        nfname = fname
    else:
        nfname = fname[:-3] + '_modified.py'
    with open(nfname, 'w', encoding='utf-8') as mod:
        last_lineno = -1
        last_col = 0
        for func in functions:
            source = StringIO('\n' + func)
            tokgen = tokenize.generate_tokens(source.readline)
            prev_toktype = tokenize.INDENT
            for toktype, ttext, (slineno, scol), (elineno, ecol
                ), ltext in tokgen:
                if 0:
                    print('%10s %-14s %-20r %r' % (tokenize.tok_name.get(
                        toktype, toktype), '%d.%d-%d.%d' % (slineno, scol,
                        elineno, ecol), ttext, ltext))
                if slineno > last_lineno:
                    last_col = 0
                if scol > last_col:
                    mod.write('' * (scol - last_col))
                if toktype == token.STRING and prev_toktype == token.INDENT:
                    mod.write('#--')
                elif toktype == tokenize.COMMENT:
                    mod.write('##\n')
                else:
                    mod.write(ttext)
                prev_toktype = toktype
                last_col = ecol
                last_lineno = elineno
    return nfname


def transform_function(func_code):
    """
    Transform a Python function into a string that can be used to create a
    new function with the same code.

    :param func_code:
        A string containing the Python function code.
    :type func_code: str
    :return:
        A string containing the Python function code.
    :rtype: str
    """
    source = StringIO(func_code)
    tokgen = tokenize.generate_tokens(source.readline)
    prev_toktype = tokenize.INDENT
    code_string = ''
    last_lineno = -1
    last_col = 0
    for toktype, ttext, (slineno, scol), (elineno, ecol), ltext in tokgen:
        if 0:
            print('%10s %-14s %-20r %r' % (tokenize.tok_name.get(toktype,
                toktype), '%d.%d-%d.%d' % (slineno, scol, elineno, ecol),
                ttext, ltext))
        if slineno > last_lineno:
            last_col = 0
        if scol > last_col:
            code_string += '' * (scol - last_col)
        if toktype == token.STRING and prev_toktype == token.INDENT:
            code_string += '#--'
        elif toktype == tokenize.COMMENT:
            code_string += '##\n'
        else:
            code_string += ttext
        prev_toktype = toktype
        last_col = ecol
        last_lineno = elineno
    return code_string


def append_to_json(input_file, json_file):
    """
    Append function docstrings to an existing JSON file.

    :param input_file:
        The Python source file to extract function docstrings from.
    :type input_file: str
    :param json_file:
        The JSON file to append the function docstrings to.
    :type json_file: str
    """
    with open(input_file, 'r', encoding='utf-8') as file:
        source_code = file.read()
    functions, imports, doc_strings = extract_functions_from_file(source_code)
    existing_data, index = load_existing_data(json_file)
    new_data = []
    for i in range(len(functions)):
        item = {'instruction':
            "Write detailed and informative comments for the Python function provided. The comments should include a high-level overview of the function's purpose, detailed descriptions of each parameter and what they represent, an explanation of the function's return values, and a line-by-line breakdown of what each part of the code does. The goal is to make the function's operation clear and understandable for someone who may be unfamiliar with the code."
            , 'input': transform_function(functions[i]), 'output':
            doc_strings[i]}
        new_data.append(item)
    combined_data = existing_data + new_data
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(combined_data, file, indent=4)
    print(f'Appended {len(functions)} functions to {json_file}')


def load_existing_data(file_path):
    """ Load existing data from a JSON file and find the highest index used. """
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data, 0
    return [], 0


def extract_functions_from_file(code):
    """
    Extract function definitions from a Python source file.

    :param code:
        Python source code.
    :type code: str
    :return:
        A tuple of (function definitions, import statements, docstrings).
    :rtype: tuple
    """
    root = ast.parse(code)
    items = []
    imports = []
    doc_strings = []
    for node in ast.walk(root):
        if isinstance(node, ast.FunctionDef):
            if ast.get_docstring(node):
                item_code = ast.unparse(node)
                items.append(item_code)
                doc_strings.append(ast.get_docstring(node))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            import_code = ast.unparse(node)
            imports.append(import_code)
    return items, imports, doc_strings


if __name__ == '__main__':
    args = parse_args()
    try:
        append_to_json(args.filename, args.out_filename)
        print(f'Processed file saved as: {args.out_filename}')
    except Exception as e:
        print(f'Error processing the file: {e}')
