#!/bin/bash

# Install Redis server
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make

# Start Redis server in the background
cd src
./redis-server &

# Go back to project root
cd ../../

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python requirements
pip install -r requirements.txt

# Start Flask app
flask run