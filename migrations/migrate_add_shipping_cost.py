#!/usr/bin/env python3
"""Migration to add shipping cost to suppliers table."""

import logging
import sqlite3
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the app
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_database():
    """Add shipping_cost column to suppliers table."""
    db_path = 'wood_cut_calc.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if shipping_cost column already exists
        cursor.execute("PRAGMA table_info(suppliers)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'shipping_cost' not in columns:
            logger.info("Adding shipping_cost column to suppliers table")
            cursor.execute('''
                ALTER TABLE suppliers
                ADD COLUMN shipping_cost REAL DEFAULT 0.0
            ''')
            conn.commit()
            logger.info("Successfully added shipping_cost column")
        else:
            logger.info("shipping_cost column already exists")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logger.error("Database error: %s", e)
        return False


if __name__ == '__main__':
    migrate_database()
