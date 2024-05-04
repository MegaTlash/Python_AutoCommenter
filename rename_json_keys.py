import json

def rename_keys_in_json(file_path):
    """
    Rename 'prompt' to 'input' and 'completion' to 'output' in a JSON file.
    
    Parameters:
    - file_path: str, the path to the JSON file.
    """
    # Read the existing data
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Rename the keys
    updated_data = []
    for item in data:
        print(item['output'])
        break
        ''' 
        new_item = {
            'instruction': "Write detailed and informative comments for the Python function provided. The comments should include a high-level overview of the function's purpose, detailed descriptions of each parameter and what they represent, an explanation of the function's return values, and a line-by-line breakdown of what each part of the code does. The goal is to make the function's operation clear and understandable for someone who may be unfamiliar with the code.",
            'input': item['output'],
            'output': item['input'],
            'imports': item['imports']
        }
        updated_data.append(new_item)

    # Write the modified data back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(updated_data, file, indent=4)
    
    print("File has been updated with new key names.")
    '''
# Usage
if __name__ == '__main__':
    path_to_json = 'datasets/dataset_strings.json'  # Specify the JSON file path
    rename_keys_in_json(path_to_json)