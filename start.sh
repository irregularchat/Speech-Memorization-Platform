#!/bin/bash
# Start Xvfb
Xvfb :99 -screen 0 1024x768x16 &
# Set display to use Xvfb
export DISPLAY=:99

# Wait for Xvfb to be ready
sleep 1

# Run the application
python app.py
