#!/usr/bin/env python3
import os
import subprocess
import sys

EXCLUDE_DIRS = {
    '.git',
    'node_modules',
    '.venv',
    '.agents',
    '.claude-plugin',
    '.codex-plugin',
    '.cursor-plugin',
    '.jetskicli',
}

def main():
    # Determine the directory paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    
    # Separate options (starting with '-') from positional arguments (files)
    options = []
    input_paths = []
    for arg in sys.argv[1:]:
        if arg.startswith('-'):
            options.append(arg)
        else:
            input_paths.append(arg)
            
    if input_paths:
        # User specified files/directories explicitly
        md_files = []
        for path in input_paths:
            abs_path = os.path.abspath(path)
            if not os.path.exists(abs_path):
                print(f"Error: Path '{path}' does not exist.", file=sys.stderr)
                sys.exit(1)
            elif os.path.isdir(abs_path):
                # Walk the directory
                for root, dirs, files in os.walk(abs_path):
                    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                    for file in files:
                        if file.endswith('.md'):
                            md_files.append(os.path.join(root, file))
            elif os.path.isfile(abs_path):
                if abs_path.endswith('.md'):
                    md_files.append(abs_path)
                else:
                    print(f"Error: File '{path}' is not a markdown file.", file=sys.stderr)
                    sys.exit(1)
    else:
        # Walk the entire repository
        md_files = []
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if file.endswith('.md'):
                    md_files.append(os.path.join(root, file))
                    
    if not md_files:
        print("No markdown files found to format.")
        return
        
    # Run mdformat
    cmd = [sys.executable, '-m', 'mdformat', '--wrap', '80'] + options + md_files
    
    # Run the command and propagate exit code
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == '__main__':
    main()
