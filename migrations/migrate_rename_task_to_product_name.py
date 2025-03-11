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
        backup_file = os.path.join('backups', f"inventory_backup_rename_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(backup_file, 'w') as f:
            json.dump(inventory_data, f, indent=2)
        logger.info(f"Backup saved to {backup_file}")
        
        return True
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        return False

def migrate_database():
    """Main migration function that's called by the migration manager"""
    return migrate_rename_task_to_product_name()

def migrate_rename_task_to_product_name():
    """
    Migration to rename task field to product_name in inventory table
    """
    logger.info("Starting migration: Renaming task to product_name in inventory table")
    
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
        # Check if task column exists and product_name doesn't
        col_info = query_db("PRAGMA table_info(inventory)")
        has_task = any(col['name'] == 'task' for col in col_info)
        has_product_name = any(col['name'] == 'product_name' for col in col_info)
        
        if has_product_name and not has_task:
            logger.info("Migration already completed: product_name exists and task doesn't.")
            return True
        
        if has_product_name and has_task:
            logger.warning("Both columns exist. This is an unexpected state.")
            return False
        
        if not has_task:
            logger.warning("Task column doesn't exist. Cannot migrate.")
            return True  # Return true to mark as complete since we can't do anything
        
        # We already have a backup from the beginning of this function, so no need to create another
        logger.info("Proceeding with schema migration...")
        
        # 2. Create a temporary table with the new schema
        logger.info("Creating temporary table with new schema...")
        
        # Get the current table schema
        table_info = query_db("PRAGMA table_info(inventory)")
        column_defs = []
        
        for col in table_info:
            col_name = col['name']
            if col_name == 'task':
                col_name = 'product_name'  # Rename task to product_name
            
            # Build column definition
            col_def = f"{col_name} {col['type']}"
            if col['notnull']:
                col_def += " NOT NULL"
            if col['dflt_value'] is not None:
                col_def += f" DEFAULT {col['dflt_value']}"
            if col['pk']:
                col_def += " PRIMARY KEY"
            
            column_defs.append(col_def)
        
        # Create the new table
        create_table_sql = f"CREATE TABLE inventory_new ({', '.join(column_defs)})"
        execute_db(create_table_sql)
        
        # 3. Copy data from old table to new one
        logger.info("Migrating data to new table structure...")
        
        # Get column names except 'task'
        old_cols = [col['name'] for col in table_info]
        new_cols = [col if col != 'task' else 'product_name' for col in old_cols]
        
        # Build the insert statement
        insert_sql = f'''
            INSERT INTO inventory_new ({', '.join(new_cols)})
            SELECT {', '.join(old_cols)} FROM inventory
        '''
        execute_db(insert_sql)
        
        # 4. Drop old table and rename new one
        logger.info("Replacing old table with new table...")
        execute_db("DROP TABLE inventory")
        execute_db("ALTER TABLE inventory_new RENAME TO inventory")
        
        # 5. Re-create foreign key constraints
        logger.info("Re-creating foreign key constraints...")
        # Execute each statement separately
        execute_db("PRAGMA foreign_keys = OFF")
        
        execute_db('''
            CREATE TABLE IF NOT EXISTS inventory_fk (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL,
                species_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                length INTEGER NOT NULL,
                height INTEGER NOT NULL,
                width INTEGER NOT NULL,
                price REAL NOT NULL,
                link TEXT,
                quality TEXT NOT NULL DEFAULT 'General Purpose',
                FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
                FOREIGN KEY (species_id) REFERENCES species (id)
            )
        ''')
        
        execute_db("INSERT INTO inventory_fk SELECT * FROM inventory")
        execute_db("DROP TABLE inventory")
        execute_db("ALTER TABLE inventory_fk RENAME TO inventory")
        execute_db("PRAGMA foreign_keys = ON")
        
        logger.info("Migration completed successfully!")
        return True
    
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    result = migrate_rename_task_to_product_name()
    if result:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")