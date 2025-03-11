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

def execute_db(query, args=()):
    """Execute a query and commit changes"""
    conn = sqlite3.connect(DATABASE)
    conn.execute(query, args)
    conn.commit()
    conn.close()

def query_db(query, args=(), one=False):
    """Query the database and return results"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def backup_database():
    """Create a backup of the inventory table"""
    # Ensure backups directory exists
    os.makedirs('backups', exist_ok=True)
    
    try:
        # Export current inventory data
        logger.info("Exporting current inventory data...")
        inventory_items = query_db("SELECT * FROM inventory")
        inventory_data = []
        
        for item in inventory_items:
            item_dict = dict(item)
            inventory_data.append(item_dict)
        
        # Save a backup of the data
        backup_file = os.path.join('backups', f"inventory_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(backup_file, 'w') as f:
            json.dump(inventory_data, f, indent=2)
        logger.info(f"Backup saved to {backup_file}")
        
        return True
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        return False

def migrate_database():
    """Main migration function that's called by the migration manager"""
    return migrate_add_quality()

def migrate_add_quality():
    """
    Migration to add quality field to inventory items
    """
    logger.info("Starting migration: Adding quality field to inventory items")
    
    # Check if database exists
    if not os.path.exists(DATABASE):
        logger.error(f"Error: Database file {DATABASE} does not exist.")
        return False
    
    # Check if inventory table exists (this could be a new database with the correct schema)
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory'")
    if not cursor.fetchone():
        logger.info("Inventory table not found. Migration not needed (likely a new database).")
        conn.close()
        return True
    
    # For existing database, create a backup  
    if not backup_database():
        logger.error("Backup failed. Aborting migration.")
        return False
    
    try:
        # We already have a backup from the beginning of this function, so no need to create another
        logger.info("Proceeding with schema migration...")
        
        # 2. Create a temporary table with the new schema
        logger.info("Creating temporary table with new schema...")
        try:
            # First, clean up any leftover tables from previous migrations
            logger.info("Cleaning up any leftover temporary tables...")
            execute_db("DROP TABLE IF EXISTS inventory_new")
            execute_db("DROP TABLE IF EXISTS inventory_fk")
            
            # Check if quality column already exists
            col_info = query_db("PRAGMA table_info(inventory)")
            has_quality = any(col['name'] == 'quality' for col in col_info)
            has_product_name = any(col['name'] == 'product_name' for col in col_info)
            has_task = any(col['name'] == 'task' for col in col_info)
            
            if has_quality:
                logger.info("Quality column already exists. No migration needed.")
                return True
            
            # Build column names list
            if has_product_name:
                name_column = "product_name TEXT NOT NULL"
            elif has_task:
                name_column = "task TEXT NOT NULL"
            else:
                logger.error("Neither product_name nor task column found. Can't migrate.")
                return False
                
            execute_db(f"""
                CREATE TABLE inventory_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER NOT NULL,
                    species_id INTEGER NOT NULL,
                    {name_column},
                    length INTEGER NOT NULL,
                    height INTEGER NOT NULL,
                    width INTEGER NOT NULL,
                    price REAL NOT NULL,
                    link TEXT,
                    quality TEXT NOT NULL DEFAULT 'General Purpose',
                    FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
                    FOREIGN KEY (species_id) REFERENCES species (id)
                )
            """)
        except Exception as e:
            logger.error(f"Error creating new table: {str(e)}", exc_info=True)
            raise
        
        # 3. Copy data from old table to new one
        logger.info("Migrating data to new table structure...")
        
        # Choose the right SQL based on whether product_name or task exists
        if has_product_name:
            execute_db("""
                INSERT INTO inventory_new (id, supplier_id, species_id, product_name, length, height, width, price, link)
                SELECT id, supplier_id, species_id, product_name, length, height, width, price, link FROM inventory
            """)
        else:
            execute_db("""
                INSERT INTO inventory_new (id, supplier_id, species_id, task, length, height, width, price, link)
                SELECT id, supplier_id, species_id, task, length, height, width, price, link FROM inventory
            """)
        
        # 4. Drop old table and rename new one
        logger.info("Replacing old table with new table...")
        execute_db("DROP TABLE inventory")
        execute_db("ALTER TABLE inventory_new RENAME TO inventory")
        
        # 5. Update schema.sql file to include the new field
        logger.info("Migration completed successfully!")
        return True
    
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    result = migrate_add_quality()
    if result:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")