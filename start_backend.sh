#!/bin/bash

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Start the Flask backend
echo "Starting Flask backend server..."
python chatbot_api.py