import os

IGNORE_DIRS = {'.venv', '__pycache__', '.git', '.idea'}
IGNORE_FILES = {'.DS_Store', '.env'}

def print_clean_tree(path, prefix=""):
    items = [
        f for f in os.listdir(path)
        if f not in IGNORE_DIRS and f not in IGNORE_FILES
    ]
    for i, name in enumerate(sorted(items)):
        full_path = os.path.join(path, name)
        connector = "└── " if i == len(items) - 1 else "├── "
        print(prefix + connector + name)
        if os.path.isdir(full_path):
            new_prefix = prefix + ("    " if i == len(items) - 1 else "│   ")
            print_clean_tree(full_path, new_prefix)

print_clean_tree(".")