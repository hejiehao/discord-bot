import json

def open_json(path: str):
    """open a json file"""
    with open(path, 'r', encoding='utf-8') as f:
        tmp = json.load(f)
    return tmp