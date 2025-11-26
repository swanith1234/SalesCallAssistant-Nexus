#!/bin/bash

echo "Starting main backend server..."
python main.py &

echo "Starting agent in dev mode..."
python agent.py dev &

# Keep the container running
wait
