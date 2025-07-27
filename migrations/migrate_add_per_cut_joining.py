#!/usr/bin/env python3
"""Migration to add allow_joining column to cuts table."""

import logging
import sqlite3
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the app
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_database():
    """Add allow_joining column to cuts table."""
    db_path = 'wood_cut_calc.db'
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if the column already exists
            cursor.execute("PRAGMA table_info(cuts)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'allow_joining' not in columns:
                logger.info("Adding allow_joining column to cuts table")
                cursor.execute('''
                    ALTER TABLE cuts
                    ADD COLUMN allow_joining BOOLEAN DEFAULT 0
                ''')
                conn.commit()
                logger.info(
                    "Successfully added allow_joining column to cuts table"
                )
            else:
                logger.info(
                    "allow_joining column already exists in cuts table"
                )
            
            # Return True to indicate success
            # (whether column was added or already existed)
            return True
                
    except sqlite3.Error as e:
        logger.error("Failed to add allow_joining column: %s", e)
        return False


if __name__ == "__main__":
    migrate_database()
