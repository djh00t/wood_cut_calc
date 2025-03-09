#!/usr/bin/env python3
"""
Setup script for the Wood Cutting Calculator app
"""
import os
import sys
from flask import Flask
import subprocess

def setup_app():
    """Initialize the application and database"""
    print("Setting up Wood Cutting Calculator...")
    
    # Check if poetry is installed
    try:
        subprocess.run(["poetry", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Poetry is not installed. Please install it first:")
        print("curl -sSL https://install.python-poetry.org | python3 -")
        sys.exit(1)
    
    # Install dependencies
    print("\nInstalling dependencies...")
    subprocess.run(["poetry", "install"], check=True)
    
    # Initialize the database
    print("\nInitializing database...")
    if os.path.exists("wood_planner.db"):
        overwrite = input("Database already exists. Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            print("Setup aborted.")
            return
        os.remove("wood_planner.db")
    
    from app import app, init_db
    with app.app_context():
        init_db()
    
    print("\nSetup complete! Run the application with:")
    print("poetry run flask run")

if __name__ == "__main__":
    setup_app()