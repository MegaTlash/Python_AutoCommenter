# AutoCommenter

AutoCommenter is a Python library for dealing with automatically generating docstrings in Python files.

## Installation

Clone the repo

```bash
git clone https://github.com/MegaTlash/Python_AutoCommenter.git
```

## Running File
```bash
python python_autocommenter.py <file_to_comment>
```

## Example
### Before running code
```python

def append_to_json(input_file, json_file):
    #--
    with open(input_file, 'r', encoding='utf-8') as file:
        source_code = file.read()
    functions, _, doc_strings = extract_functions_from_file(source_code)
    existing_data, _ = load_existing_data(json_file)
    new_data = []
    for i in range(len(functions)):
        item = {'instruction': "Write detailed and informative comments for the Python function provided. The comments should include a high-level overview of the function's purpose, detailed descriptions of each parameter and what they represent, an explanation of the function's return values, and a line-by-line breakdown of what each part of the code does. The goal is to make the function's operation clear and understandable for someone who may be unfamiliar with the code.", 
                'input': transform_function(functions[i]), 
                'output': doc_strings[i]}
        new_data.append(item)
    combined_data = existing_data + new_data
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(combined_data, file)

```
### After running code
```python

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
    functions, _, doc_strings = extract_functions_from_file(source_code)
    existing_data, _ = load_existing_data(json_file)
    new_data = []
    for i in range(len(functions)):
        item = {'instruction': "Write detailed and informative comments for the Python function provided. The comments should include a high-level overview of the function's purpose, detailed descriptions of each parameter and what they represent, an explanation of the function's return values, and a line-by-line breakdown of what each part of the code does. The goal is to make the function's operation clear and understandable for someone who may be unfamiliar with the code.", 
                'input': transform_function(functions[i]), 
                'output': doc_strings[i]}
        new_data.append(item)
    combined_data = existing_data + new_data
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(combined_data, file)

```

### TODO: MAKE AN INSTALLIATION FILE!!!!
### TODO: Set global variable for users to use everywhere 

## Contributing

If you would love to contribute, go for it! Any improvments are greatly apperciated.


## License

[MIT](https://choosealicense.com/licenses/mit/)
