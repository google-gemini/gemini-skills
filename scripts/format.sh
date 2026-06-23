#!/bin/bash
set -e

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
  echo "Error: python3 is not installed. Please install Python 3 to run the formatter."
  exit 1
fi

VENV_DIR="$DIR/.venv"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating Python virtual environment in $VENV_DIR..."
  python3 -m venv "$VENV_DIR"
fi

# Install mdformat and plugins if not already installed, or ensure they are present
echo "Ensuring mdformat and plugins are installed..."
"$VENV_DIR/bin/pip" install -q mdformat mdformat-gfm mdformat-frontmatter

# Run the python formatter script, passing along all arguments
"$VENV_DIR/bin/python" "$DIR/format.py" "$@"
