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
    """Create a backup of the inventory and qualities tables"""
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
        
        # Save a backup of the inventory data
        backup_file = os.path.join('backups', f"inventory_backup_qualities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(backup_file, 'w') as f:
            json.dump(inventory_data, f, indent=2)
        logger.info(f"Inventory backup saved to {backup_file}")
        
        return True
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        return False

def migrate_database():
    """Main migration function that's called by the migration manager"""
    return migrate_quality_to_relation()

def migrate_quality_to_relation():
    """
    Migration to convert quality text field to a relation with qualities table
    """
    logger.info("Starting migration: Converting quality text field to relation")
    
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
        
    # Check if qualities table already exists (new schema might have it)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='qualities'")
    if cursor.fetchone():
        # Check if quality_id foreign key exists in inventory
        cursor.execute("PRAGMA table_info(inventory)")
        columns = cursor.fetchall()
        if any(col[1] == 'quality_id' for col in columns):
            logger.info("Qualities table and quality_id foreign key already exist. Migration not needed.")
            conn.close()
            return True
    
    conn.close()
    
    # For existing database, create a backup
    if not backup_database():
        logger.error("Backup failed. Aborting migration.")
        return False
    
    try:
        # Clean up leftover temporary tables first
        execute_db("DROP TABLE IF EXISTS inventory_new")
        execute_db("DROP TABLE IF EXISTS inventory_fk")
        
        # Check if qualities table exists
        tables = query_db("SELECT name FROM sqlite_master WHERE type='table' AND name='qualities'")
        if not tables:
            logger.info("Creating qualities table...")
            execute_db('''
                CREATE TABLE qualities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # We already have created a backup at the beginning of this function
        # Now get the inventory data for processing
        inventory_items = query_db("SELECT * FROM inventory")
        
        # 2. Extract unique quality values from inventory
        unique_qualities = set()
        has_quality_field = False
        
        # Check if quality field exists in inventory
        columns = query_db("PRAGMA table_info(inventory)")
        for col in columns:
            if col['name'] == 'quality':
                has_quality_field = True
                break
        
        if has_quality_field:
            logger.info("Extracting unique quality values...")
            for item in inventory_items:
                if 'quality' in item and item['quality']:
                    unique_qualities.add(item['quality'])
                    
            # Insert default quality values if they're not in the unique_qualities set
            default_qualities = ['Premium', 'General Purpose', 'Framing', 'Framing (Non-Structural)']
            for quality in default_qualities:
                unique_qualities.add(quality)
        else:
            logger.info("No quality field found. Using default values.")
            unique_qualities = {'Premium', 'General Purpose', 'Framing', 'Framing (Non-Structural)'}
        
        # 3. Insert qualities into qualities table
        logger.info(f"Inserting {len(unique_qualities)} unique qualities...")
        for quality in unique_qualities:
            try:
                execute_db("INSERT INTO qualities (name) VALUES (?)", [quality])
                logger.info(f"  - Added: {quality}")
            except sqlite3.IntegrityError:
                logger.info(f"  - Already exists: {quality}")
        
        # 4. Check if quality_id field exists in inventory
        has_quality_id_field = False
        for col in columns:
            if col['name'] == 'quality_id':
                has_quality_id_field = True
                break
                
        if not has_quality_id_field:
            logger.info("Adding quality_id field to inventory table...")
            try:
                # SQLite doesn't support ADD COLUMN with foreign key, so we need to recreate the table
                execute_db("ALTER TABLE inventory ADD COLUMN quality_id INTEGER")
            except sqlite3.OperationalError:
                logger.info("Could not add quality_id field directly. Creating new table structure...")
                
                # Create new table with right structure
                col_info = query_db("PRAGMA table_info(inventory)")
                column_defs = []
                column_names = []
                
                for col in col_info:
                    if col['name'] != 'quality_id':  # Skip quality_id, we'll add it separately
                        column_defs.append(f"{col['name']} {col['type']}")
                        column_names.append(col['name'])
                
                # Add quality_id with foreign key
                column_defs.append("quality_id INTEGER")
                column_defs.append("FOREIGN KEY (quality_id) REFERENCES qualities (id)")
                column_defs.append("FOREIGN KEY (supplier_id) REFERENCES suppliers (id)")
                column_defs.append("FOREIGN KEY (species_id) REFERENCES species (id)")
                
                # Create the new table
                execute_db(f"DROP TABLE IF EXISTS inventory_new")
                execute_db(f"CREATE TABLE inventory_new (id INTEGER PRIMARY KEY AUTOINCREMENT, {', '.join(column_defs)})")
                
                # Copy data
                execute_db(f"INSERT INTO inventory_new ({', '.join(column_names)}) SELECT {', '.join(column_names)} FROM inventory")
                
                # Replace tables
                execute_db("DROP TABLE inventory")
                execute_db("ALTER TABLE inventory_new RENAME TO inventory")
        
        # 5. Update inventory items with quality_id foreign keys
        if has_quality_field:
            logger.info("Updating inventory items with quality_id values...")
            qualities = query_db("SELECT id, name FROM qualities")
            quality_map = {q['name']: q['id'] for q in qualities}
            
            for item in inventory_items:
                if 'quality' in item and item['quality'] and item['quality'] in quality_map:
                    quality_id = quality_map[item['quality']]
                    try:
                        execute_db("UPDATE inventory SET quality_id = ? WHERE id = ?", 
                                [quality_id, item['id']])
                    except Exception as e:
                        logger.error(f"Error updating item {item['id']}: {str(e)}")
        
        # 6. Optionally drop the quality column if it exists
        if has_quality_field:
            logger.info("Keeping quality column for backward compatibility.")
            # We're keeping it for now to avoid breaking existing code
            # execute_db("ALTER TABLE inventory DROP COLUMN quality")
        
        logger.info("Migration completed successfully!")
        return True
    
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    result = migrate_quality_to_relation()
    if result:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")