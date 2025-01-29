#!/bin/bash

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Installing..."
    # For Debian/Ubuntu
    apt-get update
    apt-get install -y python3 python3-pip python3-venv
fi


python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

python src/app.py