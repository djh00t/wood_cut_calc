import os
import sqlite3

# Database configuration
DATABASE = os.environ.get('DATABASE', 'wood_cut_calc.db')

def init_db():
    # Check if database file exists and remove it
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        print(f"Removed existing database: {DATABASE}")
    
    # Create a new database
    conn = sqlite3.connect(DATABASE)
    
    # Read the schema file
    with open('schema.sql', 'r') as f:
        schema = f.read()
    
    # Execute the schema script
    conn.executescript(schema)
    
    # Add some default timber species
    default_species = [
        "Pine",
        "Oak",
        "Maple",
        "Walnut",
        "Cherry",
        "Birch",
        "Cedar",
        "Poplar"
    ]
    
    cursor = conn.cursor()
    for species in default_species:
        cursor.execute("INSERT INTO species (name) VALUES (?)", (species,))
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized: {DATABASE} with {len(default_species)} default timber species")

if __name__ == '__main__':
    init_db()