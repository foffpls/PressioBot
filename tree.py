import os

IGNORE_DIRS = {'.venv', '__pycache__', '.git', '.idea'}
IGNORE_FILES = {'.DS_Store'}

def print_tree(path, prefix=""):
    files = [f for f in os.listdir(path) if f not in IGNORE_DIRS and f not in IGNORE_FILES]
    for i, f in enumerate(files):
        full_path = os.path.join(path, f)
        connector = "└── " if i == len(files)-1 else "├── "
        print(prefix + connector + f)
        if os.path.isdir(full_path):
            print_tree(full_path, prefix + ("    " if i == len(files)-1 else "│   "))

print_tree(".")
