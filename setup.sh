#!/usr/bin/env bash
# setup.sh - Script to set up the development environment

# Step 1: Create a virtual environment
# This creates a Python virtual environment in the `.venv` directory.
python3 -m venv .venv

# Step 2: Activate the virtual environment
# For Windows, use the PowerShell activation script.
# For Linux/MacOS, use the standard `source` command.
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    .\.venv\Scripts\Activate.ps1  # Windows activation
else
    source .venv/bin/activate  # Linux/MacOS activation
fi

# Step 3: Upgrade pip
# Ensure that pip, the Python package manager, is up-to-date.
pip install --upgrade pip

# Step 4: Install dependencies
# Install all required Python packages listed in the `requirements.txt` file.
pip install -r requirements.txt

# Final message
# Notify the user that the setup process is complete.
echo "*** Environment setup complete ***"