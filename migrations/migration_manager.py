#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration Manager - Runs all migrations in the correct order
"""

import importlib
import logging
import os
import sqlite3
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE = os.environ.get('DATABASE', 'wood_cut_calc.db')

# List of migrations in order they should be applied
MIGRATIONS = [
    'migrate_rename_task_to_product_name',
    'migrate_add_quality',
    'migrate_quality_to_relation',
    'migrate_add_quality_to_cuts',
    'migrate_add_timber_joining',
    'migrate_add_shipping_cost',
    'migrate_add_per_cut_joining'
]

def ensure_migration_tracking():
    """Create a migration tracking table if it doesn't exist"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Check if migrations table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='migrations'
        """)
        if not cursor.fetchone():
            # Create migrations table
            cursor.execute("""
                CREATE TABLE migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logger.info("Created migrations tracking table")
        
        return True
    except Exception as e:
        logger.error(f"Failed to create migrations table: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def get_applied_migrations():
    """Get a list of migrations that have already been applied"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM migrations ORDER BY id")
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Failed to get applied migrations: {str(e)}")
        return []
    finally:
        if conn:
            conn.close()

def mark_migration_applied(name):
    """Mark a migration as applied in the database"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO migrations (name, applied_at) VALUES (?, ?)",
            (name, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to mark migration as applied: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def run_migration(name):
    """Run a specific migration"""
    try:
        logger.info(f"Running migration: {name}")
        
        # Import the migration module
        migration = importlib.import_module(name)
        
        # Check if it has a migrate_database function
        if hasattr(migration, 'migrate_database'):
            if migration.migrate_database():
                mark_migration_applied(name)
                logger.info(f"Migration {name} completed successfully")
                return True
            else:
                logger.error(f"Migration {name} failed")
                return False
        else:
            logger.error(f"Migration {name} does not have a migrate_database function")
            return False
    except Exception as e:
        logger.error(f"Failed to run migration {name}: {str(e)}")
        return False

def run_all_migrations():
    """Run all pending migrations in the correct order"""
    if not ensure_migration_tracking():
        return False
    
    applied = get_applied_migrations()
    pending = [m for m in MIGRATIONS if m not in applied]
    
    if not pending:
        logger.info("No pending migrations")
        return True
    
    logger.info(f"Found {len(pending)} pending migrations")
    success = True
    
    for migration in pending:
        if not run_migration(migration):
            success = False
            break
    
    if success:
        logger.info("All migrations applied successfully")
    else:
        logger.error("Migration process failed")
    
    return success

if __name__ == "__main__":
    logger.info("Starting migration manager")
    
    # Make sure we can import from the current directory
    sys.path.append('.')
    
    if run_all_migrations():
        logger.info("Migration manager completed successfully")
        sys.exit(0)
    else:
        logger.error("Migration manager failed")
        sys.exit(1)