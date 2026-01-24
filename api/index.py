from fastapi import FastAPI
import sys
import os

# Add the parent directory to sys.path to allow imports from 'app'
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Now we can import from the app directory
# We assume 'app' is a directory in the root
from app.main import app

# Vercel expects a variable named 'app'
