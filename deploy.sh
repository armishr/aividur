#!/bin/bash
echo "Installing dependencies from requirements.txt"
pip install -r requirements.txt

echo "Starting the application"
gunicorn --bind 0.0.0.0:8000 app:app
