import sqlite3

# Database configuration
DATABASE = 'wood_planner.db'

def query_db(query, args=()):
    """Query the database and return results"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return rv

def execute_db(query, args=()):
    """Execute a query and commit changes"""
    conn = sqlite3.connect(DATABASE)
    conn.execute(query, args)
    conn.commit()
    conn.close()

def check_tables():
    """Check existing tables"""
    tables = query_db("SELECT name FROM sqlite_master WHERE type='table'")
    print("Tables in database:")
    for table in tables:
        print(f"- {table['name']}")
    
    if any(table['name'] == 'inventory_new' for table in tables):
        print("\nWARNING: inventory_new table exists - migration didn't complete")
    
    if any(table['name'] == 'inventory_fk' for table in tables):
        print("\nWARNING: inventory_fk table exists - migration didn't complete")

def check_inventory_schema():
    """Check inventory table schema"""
    columns = query_db("PRAGMA table_info(inventory)")
    print("\nInventory table columns:")
    for col in columns:
        print(f"- {col['name']} ({col['type']})")
    
    has_task = any(col['name'] == 'task' for col in columns)
    has_product_name = any(col['name'] == 'product_name' for col in columns)
    has_quality = any(col['name'] == 'quality' for col in columns)
    
    print(f"\nHas task column: {has_task}")
    print(f"Has product_name column: {has_product_name}")
    print(f"Has quality column: {has_quality}")

def cleanup_temp_tables():
    """Clean up temporary tables if they exist"""
    try:
        execute_db("DROP TABLE IF EXISTS inventory_new")
        execute_db("DROP TABLE IF EXISTS inventory_fk")
        print("\nTemporary tables cleaned up")
    except Exception as e:
        print(f"\nError cleaning up temporary tables: {str(e)}")

if __name__ == "__main__":
    check_tables()
    check_inventory_schema()
    cleanup_temp_tables()