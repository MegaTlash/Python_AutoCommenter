import argparse
import sys
import token
import os
import tokenize
import ast
from io import StringIO, BytesIO
import json
from unsloth import FastLanguageModel
import torch
import astor
max_seq_length = 2048 # Choose any! We auto support RoPE Scaling internally!
dtype = None # None for auto detection. Float16 for Tesla T4, V100, Bfloat16 for Ampere+
load_in_4bit = True # Use 4bit quantization to reduce memory usage. Can be False.
instruction_prompt = "Write detailed and informative comments for the Python function provided. The comments should include a high-level overview of the function's purpose, detailed descriptions of each parameter and what they represent, an explanation of the function's return values, and a line-by-line breakdown of what each part of the code does. The goal is to make the function's operation clear and understandable for someone who may be unfamiliar with the code."

alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.
### Instruction:
{}

### Input:
{}

### Response:
{}"""




def parse_args():
    parser = argparse.ArgumentParser(description="Add Comments to a Python File")
    parser.add_argument("filename", type = str, help="Python file to process")
    parser.add_argument("--num_tokens", type= int, default=2048, help="Number of tokens from LLM")
    return parser.parse_args()




### Loading up model and getting response from model 
def load_finedtuned_model():
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = "lora_model",
        max_seq_length = max_seq_length,
        dtype = dtype,
        load_in_4bit = load_in_4bit,
    )
    FastLanguageModel.for_inference(model) # Enable native 2x faster inference

    return model, tokenizer

def output_from_model(model, tokenizer, input):
    FastLanguageModel.for_inference(model) # Enable native 2x faster inference
    inputs = tokenizer(
    [
        alpaca_prompt.format(
            "Write detailed and informative comments for the Python function provided. The comments should include a high-level overview of the function's purpose, detailed descriptions of each parameter and what they represent, an explanation of the function's return values, and a line-by-line breakdown of what each part of the code does. The goal is to make the function's operation clear and understandable for someone who may be unfamiliar with the code.", # instruction
            input,
            "", # output - leave this blank for generation!
        )
    ], return_tensors = "pt").to("cuda")
    
    outputs = model.generate(**inputs, max_new_tokens = 1024, use_cache = True)
    m_out = tokenizer.batch_decode(outputs)
    res = m_out[0].split("### Response:\n", 1)
    
    return res[1][0:-15]

class ReplaceFunctionTransformer(ast.NodeTransformer):
    def __init__(self, comments, new_functions):
        """
        Initialize the transformer.
        :param comments: Dictionary of line numbers to comments.
        :param new_functions: List of strings, each containing a new function code.
        """
        self.comments = comments
        self.new_functions = iter(new_functions)  # Create an iterator from the list

    def visit_FunctionDef(self, node):
        """
        Visit a function definition and replace it if there is a #-- comment directly after.
        """
        if "#--" in self.comments.get(node.lineno + 1, ''):
            try:
                new_function_code = next(self.new_functions)  # Get the next function code
                new_function_node = ast.parse(new_function_code).body[0]  # Parse it into an AST node
                return new_function_node  # Replace the current node with the new one
            except StopIteration:
                pass  # No more new functions available
        return self.generic_visit(node)  # Continue visiting other nodes

def find_functions_with_comments(source_code, comments):
    """Parse source code and extract entire functions as strings, adding #-- right after the function declaration."""
    tree = ast.parse(source_code)
    functions_with_comments = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check for a #-- comment on the line immediately after the function definition
            if "#--" in comments.get(node.lineno + 1, ''):
                # Convert the AST node back to source code
                function_source = astor.to_source(node)
                # Insert #-- right after the function declaration line
                lines = function_source.splitlines()
                if len(lines) > 1:
                    lines.insert(1, "    #--")
                function_source_with_comment = "\n".join(lines)
                functions_with_comments.append(function_source_with_comment)

    return functions_with_comments


def capture_comments(source_code):
    tokens = tokenize.tokenize(BytesIO(source_code.encode('utf-8')).readline)
    comments = {}
    for toktype, tokval, (srow, _), _, _ in tokens:
        if toktype == tokenize.COMMENT:
            if tokval == "#--":    
                comments[srow] = tokval  # Store line number and comment
    return comments



if __name__ == '__main__':
    args = parse_args()
    try:
        with open(args.filename, 'r', encoding='utf-8') as file:
            source_code = file.read()
        
        dic_comments = capture_comments(source_code)
        functions = find_functions_with_comments(source_code, dic_comments)
        ast_tree = ast.parse(source_code)
        
        #for i in functions:
        #    print(i)
        
        #Loading model up
        
        model, tokenizer = load_finedtuned_model()
        
        modified_funcs = []
        for func in functions:
            mod_func = output_from_model(model, tokenizer, func)
            modified_funcs.append(mod_func)
            print(mod_func)
        
        transformer = ReplaceFunctionTransformer(dic_comments, modified_funcs)
        modified_ast = transformer.visit(ast_tree)
        
        modified_code = astor.to_source(modified_ast)
        
        with open(args.filename, 'w') as file:
            file.write(modified_code)
        
    except Exception as e:
        print(f"Error processing the file: {e}")