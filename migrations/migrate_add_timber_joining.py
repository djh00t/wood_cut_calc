#!/usr/bin/env python3
"""
Migration: Add timber_joining option to projects table
"""

import logging
import sqlite3

logger = logging.getLogger(__name__)


def migrate_database():
    """Add timber_joining column to projects table."""
    try:
        conn = sqlite3.connect('wood_cut_calc.db')
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(projects)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'allow_timber_joining' not in columns:
            logger.info("Adding allow_timber_joining column to projects table")
            cursor.execute('''
                ALTER TABLE projects 
                ADD COLUMN allow_timber_joining BOOLEAN DEFAULT 0
            ''')
            conn.commit()
            logger.info("Successfully added allow_timber_joining column")
        else:
            logger.info("allow_timber_joining column already exists")
            
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error adding allow_timber_joining column: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_database()
