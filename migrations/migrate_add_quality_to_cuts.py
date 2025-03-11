#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration script to add quality_id column to cuts table.
This script should be run when upgrading from an older database version.
"""

import os
import sqlite3
import json
import logging
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

def backup_database():
    """Create a backup of the database before migration."""
    # Ensure backups directory exists
    os.makedirs('backups', exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = os.path.join('backups', f'cuts_backup_{timestamp}.json')
    
    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        
        # Export cuts table
        cuts = []
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cuts')
        for row in cursor.fetchall():
            cuts.append(dict(row))
        
        # Save backup
        with open(backup_filename, 'w') as f:
            json.dump(cuts, f, indent=2)
        
        logger.info(f"Database backup created: {backup_filename}")
        return True
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def migrate_database():
    """Add quality_id column to cuts table."""
    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Check if cuts table exists (this could be a new database with the correct schema)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cuts'")
        if not cursor.fetchone():
            logger.info("Cuts table not found. Migration not needed (likely a new database).")
            conn.close()
            return True
        
        # Check if qualities table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='qualities'")
        if not cursor.fetchone():
            logger.info("Qualities table not found. Creating it now.")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS qualities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Add default quality values
            default_qualities = ['Premium', 'General Purpose', 'Framing', 'Framing (Non-Structural)']
            for quality in default_qualities:
                try:
                    cursor.execute("INSERT INTO qualities (name) VALUES (?)", (quality,))
                    logger.info(f"Added default quality: {quality}")
                except sqlite3.IntegrityError:
                    logger.info(f"Quality already exists: {quality}")
            
            conn.commit()
        
        # Check if quality_id column already exists
        cursor.execute("PRAGMA table_info(cuts)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'quality_id' not in columns:
            # Add quality_id column
            cursor.execute('''
                ALTER TABLE cuts
                ADD COLUMN quality_id INTEGER
            ''')
            
            # Add foreign key constraint
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS fk_cuts_quality_id
                BEFORE INSERT ON cuts
                FOR EACH ROW BEGIN
                    SELECT RAISE(ROLLBACK, 'insert on table "cuts" violates foreign key constraint "fk_cuts_quality_id"')
                    WHERE NEW.quality_id IS NOT NULL AND (SELECT id FROM qualities WHERE id = NEW.quality_id) IS NULL;
                END;
            ''')
            
            conn.commit()
            logger.info("Migration completed successfully: Added quality_id column to cuts table")
        else:
            logger.info("quality_id column already exists in cuts table. No migration needed.")
        
        return True
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Starting migration to add quality_id to cuts table")
    
    # Backup first
    if backup_database():
        # Then migrate
        if migrate_database():
            logger.info("Migration completed successfully")
        else:
            logger.error("Migration failed")
    else:
        logger.error("Migration aborted due to backup failure")