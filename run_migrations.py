#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convenience script to run all database migrations
"""

import os
import sys
import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add the migrations directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'migrations'))

# Import the migration manager
from migrations.migration_manager import run_all_migrations, DATABASE

def check_database_exists():
    """Check if the database file exists and has required tables"""
    if not os.path.exists(DATABASE):
        return False
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Check if core tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('suppliers', 'inventory', 'projects', 'cuts')")
        tables = cursor.fetchall()
        
        conn.close()
        return len(tables) >= 4
    except:
        return False

def initialize_database():
    """Initialize a new database if it doesn't exist"""
    logger.info(f"Database {DATABASE} not found or incomplete. Initializing...")
    try:
        # Create a new database
        conn = sqlite3.connect(DATABASE)
        
        # Read the schema file
        with open('schema.sql', 'r') as f:
            schema = f.read()
        
        # Execute the schema script
        conn.executescript(schema)
        
        # Add some default timber species
        default_species = [
            "Pine", "Oak", "Maple", "Walnut", 
            "Cherry", "Birch", "Cedar", "Poplar"
        ]
        
        cursor = conn.cursor()
        for species in default_species:
            cursor.execute("INSERT INTO species (name) VALUES (?)", (species,))
        
        # Add some default quality grades
        default_qualities = [
            "Premium", "General Purpose", "Framing", "Framing (Non-Structural)"
        ]
        
        for quality in default_qualities:
            cursor.execute("INSERT INTO qualities (name) VALUES (?)", (quality,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Database initialized with basic tables and default values")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return False

if __name__ == "__main__":
    print("Running database migrations...")
    
    # Check if database exists and initialize if needed
    if not check_database_exists():
        if not initialize_database():
            print("Failed to initialize database. Cannot continue with migrations.")
            sys.exit(1)
        logger.info("Database initialized successfully")
    
    # Run all migrations
    if run_all_migrations():
        print("All migrations applied successfully!")
        sys.exit(0)
    else:
        print("Migration process failed. Check the logs for details.")
        sys.exit(1)