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
    parser.add_argument("--filename", type = str, default= "test.py", help="Python file to process")
    parser.add_argument("--num_tokens", type= int, default=1024, help="Number of tokens from LLM")
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
    
    return res[1]


def parse_code_to_ast(source_code):
    return ast.parse(source_code)

def correlate_comments_with_ast_nodes(comments, ast_tree):
    func_comments = []
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.FunctionDef):
            # Get the line number of the function signature
            signature_end_line = node.lineno
            # Check if there's a comment on the line immediately after the function signature
            following_comment = comments.get(signature_end_line + 1)
            if following_comment:
                func_comments.append(ast.unparse(node))
    return func_comments

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
        ast_tree = parse_code_to_ast(source_code)
        func_comments = correlate_comments_with_ast_nodes(dic_comments, ast_tree)
        
        print(func_comments)
        
        #Loading model up
        '''
        model, tokenizer = load_finedtuned_model()
        
        modified_funcs = []
        for func in func_comments:
            mod_func = output_from_model(model, tokenizer, func)
            modified_funcs.append(mod_func)
        '''
        
    except Exception as e:
        print(f"Error processing the file: {e}")