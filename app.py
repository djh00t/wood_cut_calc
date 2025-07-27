from typing import Any, Dict, List, Optional, TypedDict


class CutDict(TypedDict):
    """Dictionary type for a cut item.

    Attributes:
        id: Unique identifier for the cut.
        project_id: Associated project ID.
        species_id: Species ID (optional).
        quality_id: Quality ID (optional).
        label: Label for the cut.
        length: Length in mm.
        width: Width in mm.
        depth: Depth in mm.
        quantity: Quantity required.
        species_name: Name of the species (optional).
        quality_name: Name of the quality (optional).
    """
    id: int
    project_id: int
    species_id: Optional[int]
    quality_id: Optional[int]
    label: str
    length: int
    width: int
    depth: int
    quantity: int
    species_name: Optional[str]
    quality_name: Optional[str]

class InventoryDict(TypedDict):
    """Dictionary type for an inventory item.

    Attributes:
        id: Unique identifier for the inventory item.
        supplier_id: Supplier ID.
        species_id: Species ID.
        quality_id: Optional quality ID.
        product_name: Name of the product.
        length: Length in mm.
        height: Height in mm.
        width: Width in mm.
        price: Price of the item.
        link: Optional link to the product.
        species_name: Name of the species (optional).
        quality_name: Name of the quality (optional).
    """
    id: int
    supplier_id: int
    species_id: int
    quality_id: Optional[int]
    product_name: str
    length: int
    height: int
    width: int
    price: float
    link: str
    species_name: Optional[str]
    quality_name: Optional[str]

class PlanItem(TypedDict):
    """Dictionary type for a cutting plan item.

    Attributes:
        item: The inventory item used.
        cuts: List of cuts assigned to this item.
        waste: Waste length in mm.
        waste_percent: Waste as a percentage.
        is_cost_efficient: Whether this plan is cost efficient.
        efficiency_note: Optional note about efficiency.
    """
    item: InventoryDict
    cuts: List[CutDict]
    waste: int
    waste_percent: float
    is_cost_efficient: bool
    efficiency_note: str


import itertools
import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, cast

from flask import Flask, flash, g, jsonify, redirect, render_template, request, url_for

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'wood_planner_secret_key'

# Constants
DEFAULT_QUALITY = 'General Purpose'

# Configure logging based on DEBUG environment variable
debug_mode = os.environ.get('DEBUG', '').lower() in ('1', 'true')
log_level = logging.DEBUG if debug_mode else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if debug_mode:
    logger.debug("Debug mode activated")

# Database configuration
DATABASE = os.environ.get('DATABASE', 'wood_cut_calc.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def modify_db(query, args=()):
    db = get_db()
    db.execute(query, args)
    db.commit()

# Register custom template filters
from custom_filters import bp as filters_bp

app.register_blueprint(filters_bp)

# Make helpful functions available in templates
app.jinja_env.globals['enumerate'] = enumerate
app.jinja_env.globals['now'] = datetime.now

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/run_migrations', methods=['POST'])
def run_migrations():
    """Run all database migrations"""
    try:
        # Add migrations directory to path if it's not already there
        import sys
        if not 'migrations' in sys.path:
            sys.path.append('migrations')
        
        # Import and run the migration manager
        from migrations.migration_manager import run_all_migrations
        if run_all_migrations():
            flash('All migrations completed successfully!', 'success')
        else:
            flash('Some migrations failed. Check the console for errors.', 'danger')
    except Exception as e:
        flash(f'Migration failed: {str(e)}', 'danger')
        logger.error(f"Migration error: {str(e)}", exc_info=True)
    
    return redirect(url_for('index'))

# Species routes
@app.route('/species')
def species():
    species_list = query_db('SELECT * FROM species')
    return render_template('species.html', species_list=species_list)

@app.route('/species/add', methods=['GET', 'POST'])
def add_species():
    if request.method == 'POST':
        name = request.form['name']
        
        # Check if species already exists
        existing = query_db('SELECT * FROM species WHERE name = ?', [name], one=True)
        if existing:
            flash(f'Species "{name}" already exists!', 'warning')
            return redirect(url_for('species'))
        
        modify_db('INSERT INTO species (name) VALUES (?)', [name])
        flash('Species added successfully!', 'success')
        return redirect(url_for('species'))
    
    return render_template('species_form.html')

@app.route('/species/<int:species_id>/edit', methods=['GET', 'POST'])
def edit_species(species_id):
    species_item = query_db('SELECT * FROM species WHERE id = ?', [species_id], one=True)
    
    if not species_item:
        flash('Species not found', 'danger')
        return redirect(url_for('species'))
    
    if request.method == 'POST':
        name = request.form['name']
        
        # Check if species already exists with this name (and it's not this one)
        existing = query_db('SELECT * FROM species WHERE name = ? AND id != ?', [name, species_id], one=True)
        if existing:
            flash(f'Species "{name}" already exists!', 'warning')
            return render_template('species_form.html', species=species_item, edit_mode=True)
        
        modify_db('UPDATE species SET name = ? WHERE id = ?', [name, species_id])
        
        flash('Species updated successfully!', 'success')
        return redirect(url_for('species'))
    
    return render_template('species_form.html', species=species_item, edit_mode=True)

@app.route('/species/<int:species_id>/delete', methods=['POST'])
def delete_species(species_id):
    # Check if species is used in inventory or cuts
    inventory_count = query_db('SELECT COUNT(*) FROM inventory WHERE species_id = ?', [species_id], one=True)[0]
    cuts_count = query_db('SELECT COUNT(*) FROM cuts WHERE species_id = ?', [species_id], one=True)[0]
    
    if inventory_count > 0 or cuts_count > 0:
        flash('Cannot delete species that is in use by inventory items or cuts', 'danger')
        return redirect(url_for('species'))
    
    # Delete the species
    modify_db('DELETE FROM species WHERE id = ?', [species_id])
    
    flash('Species deleted successfully!', 'success')
    return redirect(url_for('species'))

# Quality routes
@app.route('/qualities')
def qualities():
    qualities_list = query_db('SELECT * FROM qualities')
    return render_template('qualities.html', qualities_list=qualities_list)

@app.route('/qualities/add', methods=['GET', 'POST'])
def add_quality():
    if request.method == 'POST':
        name = request.form['name']
        
        # Check if quality already exists
        existing = query_db('SELECT * FROM qualities WHERE name = ?', [name], one=True)
        if existing:
            flash(f'Quality "{name}" already exists!', 'warning')
            return redirect(url_for('qualities'))
        
        modify_db('INSERT INTO qualities (name) VALUES (?)', [name])
        flash('Quality added successfully!', 'success')
        return redirect(url_for('qualities'))
    
    return render_template('quality_form.html')

@app.route('/qualities/<int:quality_id>/edit', methods=['GET', 'POST'])
def edit_quality(quality_id):
    quality_item = query_db('SELECT * FROM qualities WHERE id = ?', [quality_id], one=True)
    
    if not quality_item:
        flash('Quality not found', 'danger')
        return redirect(url_for('qualities'))
    
    if request.method == 'POST':
        name = request.form['name']
        
        # Check if quality already exists with this name (and it's not this one)
        existing = query_db('SELECT * FROM qualities WHERE name = ? AND id != ?', [name, quality_id], one=True)
        if existing:
            flash(f'Quality "{name}" already exists!', 'warning')
            return render_template('quality_form.html', quality=quality_item, edit_mode=True)
        
        modify_db('UPDATE qualities SET name = ? WHERE id = ?', [name, quality_id])
        
        flash('Quality updated successfully!', 'success')
        return redirect(url_for('qualities'))
    
    return render_template('quality_form.html', quality=quality_item, edit_mode=True)

@app.route('/qualities/<int:quality_id>/delete', methods=['POST'])
def delete_quality(quality_id):
    # Check if quality is used in inventory
    inventory_count = query_db('SELECT COUNT(*) FROM inventory WHERE quality_id = ?', [quality_id], one=True)[0]
    
    if inventory_count > 0:
        flash('Cannot delete quality that is in use by inventory items', 'danger')
        return redirect(url_for('qualities'))
    
    # Delete the quality
    modify_db('DELETE FROM qualities WHERE id = ?', [quality_id])
    
    flash('Quality deleted successfully!', 'success')
    return redirect(url_for('qualities'))

# Supplier routes
@app.route('/suppliers')
def suppliers():
    suppliers = query_db('SELECT * FROM suppliers')
    return render_template('suppliers.html', suppliers=suppliers)

@app.route('/supplier/add', methods=['GET', 'POST'])
def add_supplier():
    if request.method == 'POST':
        name = request.form['name']
        shipping_cost = float(request.form.get('shipping_cost', 0.0))
        
        # Check if shipping_cost column exists
        col_info = query_db("PRAGMA table_info(suppliers)")
        has_shipping_cost = any(col['name'] == 'shipping_cost' for col in col_info)
        
        try:
            if has_shipping_cost:
                modify_db('INSERT INTO suppliers (name, shipping_cost) VALUES (?, ?)', 
                         [name, shipping_cost])
            else:
                modify_db('INSERT INTO suppliers (name) VALUES (?)', [name])
                flash('Note: Shipping cost not saved. Please run migrations to add shipping support.', 'warning')
        except Exception as e:
            logger.error("Error adding supplier: %s", e)
            flash('Error adding supplier. Please try again.', 'danger')
            return render_template('supplier_form.html')
            
        flash('Supplier added successfully!', 'success')
        return redirect(url_for('suppliers'))
    
    return render_template('supplier_form.html')

@app.route('/supplier/<int:supplier_id>/edit', methods=['GET', 'POST'])
def edit_supplier(supplier_id):
    supplier = query_db('SELECT * FROM suppliers WHERE id = ?', [supplier_id], one=True)
    
    if not supplier:
        flash('Supplier not found', 'danger')
        return redirect(url_for('suppliers'))
    
    if request.method == 'POST':
        name = request.form['name']
        shipping_cost = float(request.form.get('shipping_cost', 0.0))
        
        # Check if shipping_cost column exists
        col_info = query_db("PRAGMA table_info(suppliers)")
        has_shipping_cost = any(col['name'] == 'shipping_cost' for col in col_info)
        
        try:
            if has_shipping_cost:
                modify_db('UPDATE suppliers SET name = ?, shipping_cost = ? WHERE id = ?', 
                         [name, shipping_cost, supplier_id])
            else:
                modify_db('UPDATE suppliers SET name = ? WHERE id = ?', [name, supplier_id])
                flash('Note: Shipping cost not saved. Please run migrations to add shipping support.', 'warning')
        except Exception as e:
            logger.error("Error updating supplier: %s", e)
            flash('Error updating supplier. Please try again.', 'danger')
            return render_template('supplier_form.html', supplier=supplier, edit_mode=True)
            
        flash('Supplier updated successfully!', 'success')
        return redirect(url_for('suppliers'))
    
    return render_template('supplier_form.html', supplier=supplier, edit_mode=True)

@app.route('/supplier/<int:supplier_id>/delete', methods=['POST'])
def delete_supplier(supplier_id):
    # Check if supplier is used in inventory
    inventory_count = query_db('SELECT COUNT(*) FROM inventory WHERE supplier_id = ?', [supplier_id], one=True)[0]
    
    if inventory_count > 0:
        flash('Cannot delete supplier that has inventory items', 'danger')
        return redirect(url_for('suppliers'))
    
    # Delete the supplier
    modify_db('DELETE FROM suppliers WHERE id = ?', [supplier_id])
    
    flash('Supplier deleted successfully!', 'success')
    return redirect(url_for('suppliers'))

@app.route('/supplier/<int:supplier_id>')
def view_supplier(supplier_id):
    supplier = query_db('SELECT * FROM suppliers WHERE id = ?', [supplier_id], one=True)
    
    # Check which columns exist
    col_info = query_db("PRAGMA table_info(inventory)")
    has_product_name = any(col['name'] == 'product_name' for col in col_info)
    has_task = any(col['name'] == 'task' for col in col_info)
    has_quality_id = any(col['name'] == 'quality_id' for col in col_info)
    
    # Check if qualities table exists
    tables = query_db("SELECT name FROM sqlite_master WHERE type='table' AND name='qualities'")
    has_qualities_table = len(tables) > 0
    
    try:
        # Base query parts
        base_select = "SELECT i.*, s.name as species_name"
        base_from = "FROM inventory i JOIN species s ON i.species_id = s.id"
        
        # Add quality join if available
        if has_quality_id and has_qualities_table:
            base_select += ", q.name as quality_name"
            base_from += " LEFT JOIN qualities q ON i.quality_id = q.id"
        
        # Build and execute the query
        query = f"{base_select} {base_from} WHERE i.supplier_id = ?"
        inventory = query_db(query, [supplier_id])
        
        # Process items for consistency
        processed_inventory = []
        for item in inventory:
            item_dict = dict(item)
            
            # Map task to product_name for template consistency
            if not has_product_name and 'task' in item_dict:
                item_dict['product_name'] = item_dict['task']
                # Show message about running migration (once)
                if not has_product_name and len(processed_inventory) == 0:
                    flash('Database needs product_name migration. Please run: python migrate_rename_task_to_product_name.py', 'warning')
            
            # Add quality_name if not present but quality_id exists
            if 'quality_id' in item_dict and item_dict['quality_id'] and 'quality_name' not in item_dict:
                # Look up quality name from id
                quality = query_db('SELECT name FROM qualities WHERE id = ?', [item_dict['quality_id']], one=True)
                if quality:
                    item_dict['quality_name'] = quality['name']
                else:
                    item_dict['quality_name'] = DEFAULT_QUALITY
            
            # Ensure quality_name exists
            if 'quality_name' not in item_dict or not item_dict['quality_name']:
                item_dict['quality_name'] = DEFAULT_QUALITY
                
            processed_inventory.append(item_dict)
        
        inventory = processed_inventory
        
        # Check for quality migration
        if not has_quality_id or not has_qualities_table:
            flash('Database needs quality relation migration. Please run: python migrate_quality_to_relation.py', 'warning')
    
    except sqlite3.OperationalError as e:
        logger.error(f"Database error: {str(e)}")
        flash(f"Database error: {str(e)}. Please run the migration scripts.", "danger")
        inventory = []
    
    return render_template('supplier_view.html', supplier=supplier, inventory=inventory)

# Inventory routes
@app.route('/inventory/add', methods=['GET', 'POST'])
def add_inventory():
    if request.method == 'POST':
        supplier_id = request.form['supplier_id']
        species_id = request.form['species_id']
        # Handle both task and product_name for backward compatibility
        product_name = request.form.get('product_name', '') or request.form.get('task', '')
        length = int(request.form['length'])
        height = int(request.form['height'])
        width = int(request.form['width'])
        price = float(request.form['price'])
        link = request.form['link']
        quality_id = request.form.get('quality_id')
        
        # Check if quality_id is a valid integer
        if quality_id:
            try:
                quality_id = int(quality_id)
            except ValueError:
                quality_id = None
        
        # Check if columns exist by querying table structure
        col_info = query_db("PRAGMA table_info(inventory)")
        has_product_name = any(col['name'] == 'product_name' for col in col_info)
        has_quality_id = any(col['name'] == 'quality_id' for col in col_info)
        
        try:
            # Get the default SQL fields
            sql_fields = ['supplier_id', 'species_id', 'product_name', 'length', 'height', 'width', 'price', 'link']
            sql_values = [supplier_id, species_id, product_name, length, height, width, price, link]
            
            # Add quality_id if the field exists
            if has_quality_id and quality_id:
                sql_fields.append('quality_id')
                sql_values.append(quality_id)
            
            # Build the SQL statement
            field_str = ", ".join(sql_fields)
            placeholders = ", ".join(['?'] * len(sql_fields))
            
            # Execute the insert
            modify_db(f"INSERT INTO inventory ({field_str}) VALUES ({placeholders})", sql_values)
            
        except sqlite3.OperationalError as e:
            logger.error(f"Database error: {str(e)}")
            flash(f"Database error: {str(e)}. Please run the migration scripts.", "danger")
            return redirect(url_for('suppliers'))
        
        flash('Inventory item added successfully!', 'success')
        return redirect(url_for('view_supplier', supplier_id=supplier_id))
    
    suppliers = query_db('SELECT * FROM suppliers')
    species_list = query_db('SELECT * FROM species')
    quality_list = query_db('SELECT * FROM qualities')
    
    # If no qualities exist, run the migration or populate defaults
    if not quality_list:
        try:
            # Check if qualities table exists
            tables = query_db("SELECT name FROM sqlite_master WHERE type='table' AND name='qualities'")
            if not tables:
                flash("The qualities table doesn't exist. Please run the migration script.", 'warning')
            else:
                # Add default qualities
                default_qualities = ['Premium', 'General Purpose', 'Framing', 'Framing (Non-Structural)']
                for quality in default_qualities:
                    try:
                        modify_db("INSERT INTO qualities (name) VALUES (?)", [quality])
                        logger.info(f"Added default quality: {quality}")
                    except sqlite3.IntegrityError:
                        pass  # Already exists
                
                # Fetch the qualities again
                quality_list = query_db('SELECT * FROM qualities')
                if quality_list:
                    flash("Default quality grades have been added.", 'info')
        except Exception as e:
            logger.error(f"Error adding default qualities: {str(e)}")
            flash("Error initializing quality grades. Please run the migration script.", 'warning')
    
    return render_template('inventory_form.html', suppliers=suppliers, species_list=species_list, quality_list=quality_list)

@app.route('/inventory/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_inventory(item_id):
    item = query_db('SELECT * FROM inventory WHERE id = ?', [item_id], one=True)
    
    if not item:
        flash('Inventory item not found', 'danger')
        return redirect(url_for('suppliers'))
    
    # Convert item to dictionary for easier handling
    item_dict = dict(item)
    
    # Map task to product_name for UI consistency
    if 'product_name' not in item_dict and 'task' in item_dict:
        item_dict['product_name'] = item_dict['task']
    
    if request.method == 'POST':
        supplier_id = request.form['supplier_id']
        species_id = request.form['species_id']
        # Handle both task and product_name for backward compatibility
        product_name = request.form.get('product_name', '') or request.form.get('task', '')
        length = int(request.form['length'])
        height = int(request.form['height'])
        width = int(request.form['width'])
        price = float(request.form['price'])
        link = request.form['link']
        quality_id = request.form.get('quality_id')
        
        # Check if quality_id is a valid integer
        if quality_id:
            try:
                quality_id = int(quality_id)
            except ValueError:
                quality_id = None
        
        # Check if columns exist by querying table structure
        col_info = query_db("PRAGMA table_info(inventory)")
        has_product_name = any(col['name'] == 'product_name' for col in col_info)
        has_quality_id = any(col['name'] == 'quality_id' for col in col_info)
        
        try:
            # Start with base fields that are always present
            field_updates = [
                "supplier_id = ?",
                "species_id = ?",
                "length = ?",
                "height = ?",
                "width = ?",
                "price = ?",
                "link = ?"
            ]
            params = [
                supplier_id, 
                species_id, 
                length, 
                height, 
                width, 
                price, 
                link
            ]
            
            # Add product_name field
            if has_product_name:
                field_updates.append("product_name = ?")
                params.append(product_name)
            else:
                field_updates.append("task = ?")
                params.append(product_name)
                
            # Add quality_id field if it exists and was provided
            if has_quality_id and quality_id:
                field_updates.append("quality_id = ?")
                params.append(quality_id)
                
            # Add item_id for WHERE clause
            params.append(item_id)
                
            # Build and execute SQL
            sql = f"UPDATE inventory SET {', '.join(field_updates)} WHERE id = ?"
            modify_db(sql, params)
            
        except sqlite3.OperationalError as e:
            logger.error(f"Database error: {str(e)}")
            flash(f"Database error: {str(e)}. Please run the migration scripts.", "danger")
            return redirect(url_for('suppliers'))
        
        flash('Inventory item updated successfully!', 'success')
        return redirect(url_for('view_supplier', supplier_id=supplier_id))
    
    suppliers = query_db('SELECT * FROM suppliers')
    species_list = query_db('SELECT * FROM species')
    quality_list = query_db('SELECT * FROM qualities')
    
    # If no qualities exist, run the migration or populate defaults
    if not quality_list:
        try:
            # Check if qualities table exists
            tables = query_db("SELECT name FROM sqlite_master WHERE type='table' AND name='qualities'")
            if not tables:
                flash("The qualities table doesn't exist. Please run the migration script.", 'warning')
            else:
                # Add default qualities
                default_qualities = ['Premium', 'General Purpose', 'Framing', 'Framing (Non-Structural)']
                for quality in default_qualities:
                    try:
                        modify_db("INSERT INTO qualities (name) VALUES (?)", [quality])
                        logger.info(f"Added default quality: {quality}")
                    except sqlite3.IntegrityError:
                        pass  #
                
                # Fetch the qualities again
                quality_list = query_db('SELECT * FROM qualities')
                if quality_list:
                    flash("Default quality grades have been added.", 'info')
        except Exception as e:
            logger.error(f"Error adding default qualities: {str(e)}")
            flash("Error initializing quality grades. Please run the migration script.", 'warning')
    
    return render_template('inventory_form.html', suppliers=suppliers, species_list=species_list, quality_list=quality_list, item=item_dict, edit_mode=True)

@app.route('/inventory/<int:item_id>/copy')
def copy_inventory(item_id):
    try:
        # Get the original inventory item
        item = query_db('SELECT * FROM inventory WHERE id = ?', [item_id], one=True)
        
        if not item:
            flash('Inventory item not found', 'danger')
            return redirect(url_for('suppliers'))
        
        # Convert item to a dictionary
        item = dict(item)
        
        # Get the name field (task or product_name)
        product_name = ""
        if 'product_name' in item:
            product_name = f"{item['product_name']} (Copy)"
        elif 'task' in item:
            product_name = f"{item['task']} (Copy)"
        else:
            product_name = "New Item (Copy)"
        
        # Check if columns exist by querying table structure
        col_info = query_db("PRAGMA table_info(inventory)")
        has_product_name = any(col['name'] == 'product_name' for col in col_info)
        has_quality_id = any(col['name'] == 'quality_id' for col in col_info)
        
        try:
            # Start with base fields
            fields = ["supplier_id", "species_id", "length", "height", "width", "price", "link"]
            values = [
                item['supplier_id'], 
                item['species_id'],
                item['length'], 
                item['height'], 
                item['width'], 
                item['price'], 
                item['link']
            ]
            
            # Add the correct name field
            if has_product_name:
                fields.append("product_name")
            else:
                fields.append("task")
            values.append(product_name)
            
            # Add quality_id if available
            if has_quality_id and 'quality_id' in item and item['quality_id']:
                fields.append("quality_id")
                values.append(item['quality_id'])
            
            # Build and execute SQL
            field_str = ", ".join(fields)
            placeholders = ", ".join(['?'] * len(fields))
            modify_db(f"INSERT INTO inventory ({field_str}) VALUES ({placeholders})", values)
            
        except sqlite3.OperationalError as e:
            logger.error(f"Database error: {str(e)}")
            flash(f"Database error: {str(e)}. Please run the migration scripts.", "danger")
            return redirect(url_for('suppliers'))
        
        flash('Inventory item copied successfully!', 'success')
        return redirect(url_for('view_supplier', supplier_id=item['supplier_id']))
        
    except Exception as e:
        logger.error(f"Error copying inventory item: {str(e)}", exc_info=True)
        flash(f"An error occurred when copying the inventory item: {str(e)}", 'danger')
        return redirect(url_for('suppliers'))

@app.route('/inventory/<int:item_id>/delete', methods=['POST'])
def delete_inventory(item_id):
    # Get the supplier ID before deleting the item
    item = query_db('SELECT supplier_id FROM inventory WHERE id = ?', [item_id], one=True)
    
    if not item:
        flash('Inventory item not found', 'danger')
        return redirect(url_for('suppliers'))
    
    supplier_id = item['supplier_id']
    
    # Delete the inventory item
    modify_db('DELETE FROM inventory WHERE id = ?', [item_id])
    
    flash('Inventory item deleted successfully!', 'success')
    return redirect(url_for('view_supplier', supplier_id=supplier_id))

# Project routes
@app.route('/projects')
def projects():
    projects = query_db('SELECT * FROM projects')
    return render_template('projects.html', projects=projects)

@app.route('/project/add', methods=['GET', 'POST'])
def add_project():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        allow_timber_joining = 'allow_timber_joining' in request.form
        
        modify_db(
            'INSERT INTO projects (name, description, allow_timber_joining, created_at) '
            'VALUES (?, ?, ?, ?)',
            [name, description, allow_timber_joining, 
             datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        )
        
        flash('Project added successfully!', 'success')
        return redirect(url_for('projects'))
    
    return render_template('project_form.html')

@app.route('/project/<int:project_id>')
def view_project(project_id):
    project = query_db('SELECT * FROM projects WHERE id = ?', [project_id], one=True)
    
    # First check if quality_id column exists in cuts table
    try:
        cuts = query_db('''
            SELECT c.*, s.name as species_name, q.name as quality_name
            FROM cuts c 
            LEFT JOIN species s ON c.species_id = s.id 
            LEFT JOIN qualities q ON c.quality_id = q.id
            WHERE c.project_id = ?
        ''', [project_id])
    except sqlite3.OperationalError:
        # Fallback if quality_id doesn't exist yet
        cuts = query_db('''
            SELECT c.*, s.name as species_name, NULL as quality_name
            FROM cuts c 
            LEFT JOIN species s ON c.species_id = s.id 
            WHERE c.project_id = ?
        ''', [project_id])
        flash('Database schema needs to be updated. Please run the migration script.', 'warning')
        
    saved_plans = query_db('SELECT * FROM saved_plans WHERE project_id = ? ORDER BY created_at DESC', [project_id])
    return render_template('project_view.html', project=project, cuts=cuts, saved_plans=saved_plans)

@app.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
    project = query_db('SELECT * FROM projects WHERE id = ?', [project_id], one=True)
    
    if not project:
        flash('Project not found', 'danger')
        return redirect(url_for('projects'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        allow_timber_joining = 'allow_timber_joining' in request.form
        
        modify_db(
            'UPDATE projects SET name = ?, description = ?, allow_timber_joining = ? WHERE id = ?',
            [name, description, allow_timber_joining, project_id]
        )
        
        flash('Project updated successfully!', 'success')
        return redirect(url_for('view_project', project_id=project_id))
    
    return render_template('project_form.html', project=project, edit_mode=True)

@app.route('/project/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id):
    project = query_db('SELECT * FROM projects WHERE id = ?', [project_id], one=True)
    
    if not project:
        flash('Project not found', 'danger')
        return redirect(url_for('projects'))
    
    # Delete all cuts associated with this project
    modify_db('DELETE FROM cuts WHERE project_id = ?', [project_id])
    
    # Delete the project
    modify_db('DELETE FROM projects WHERE id = ?', [project_id])
    
    flash('Project and all associated cuts deleted successfully!', 'success')
    return redirect(url_for('projects'))

@app.route('/project/<int:project_id>/copy')
def copy_project(project_id):
    try:
        # Get the original project
        project = query_db('SELECT * FROM projects WHERE id = ?', [project_id], one=True)
        
        if not project:
            flash('Project not found', 'danger')
            return redirect(url_for('projects'))
        
        # Create a new project with a copy name
        new_name = f"{project['name']} (Copy)"
        modify_db('INSERT INTO projects (name, description, created_at) VALUES (?, ?, ?)',
                 [new_name, project['description'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        
        # Get the new project ID
        new_project_id = query_db('SELECT last_insert_rowid()', one=True)[0]
        
        # Get all cuts from the original project
        cuts = query_db('SELECT * FROM cuts WHERE project_id = ?', [project_id])
        
        # Copy all cuts to the new project
        for cut in cuts:
            modify_db('''
                INSERT INTO cuts (project_id, species_id, label, length, width, depth, quantity) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', [new_project_id, cut['species_id'], cut['label'], cut['length'], 
                  cut['width'], cut['depth'], cut['quantity']])
        
        # Get all saved plans from the original project
        saved_plans = query_db('SELECT * FROM saved_plans WHERE project_id = ?', [project_id])
        
        # Copy all saved plans to the new project
        plans_count = 0
        for plan in saved_plans:
            # Load the plan data to update the project_id inside
            plan_data = json.loads(plan['plan_data'])
            plan_data['project_id'] = new_project_id
            updated_plan_data = json.dumps(plan_data)
            
            # Save plan with new project ID
            new_plan_name = f"{plan['name']} (Copied)"
            modify_db(
                'INSERT INTO saved_plans (project_id, name, plan_data, created_at) VALUES (?, ?, ?, ?)',
                [new_project_id, new_plan_name, updated_plan_data, datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            )
            plans_count += 1
        
        # Create success message
        success_msg = f'Project copied successfully! Created "{new_name}" with {len(cuts)} cuts'
        if plans_count > 0:
            success_msg += f' and {plans_count} saved plan{"s" if plans_count > 1 else ""}'
        success_msg += '.'
        flash(success_msg, 'success')
        
        return redirect(url_for('view_project', project_id=new_project_id))
        
    except Exception as e:
        logger.error(f"Error copying project: {str(e)}", exc_info=True)
        flash(f"An error occurred when copying the project: {str(e)}", 'danger')
        return redirect(url_for('view_project', project_id=project_id))

# Cut routes
@app.route('/cut/add', methods=['GET', 'POST'])
def add_cut():
    if request.method == 'POST':
        project_id = request.form['project_id']
        species_id = request.form.get('species_id', None)  # Optional
        if species_id == '':
            species_id = None
        quality_id = request.form.get('quality_id', None)  # Optional
        if quality_id == '':
            quality_id = None
        label = request.form['label']
        length = int(request.form['length'])
        width = int(request.form['width'])
        depth = int(request.form['depth'])
        quantity = int(request.form['quantity'])
        allow_joining = 1 if request.form.get('allow_joining') else 0
        
        # Check if allow_joining column exists and insert accordingly
        try:
            modify_db('''
                INSERT INTO cuts (
                    project_id, species_id, label, length, width, depth, 
                    quantity, quality_id, allow_joining
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                project_id, species_id, label, length, width, depth, 
                quantity, quality_id, allow_joining
            ])
        except sqlite3.OperationalError:
            # Fallback if allow_joining doesn't exist yet
            try:
                modify_db('''
                    INSERT INTO cuts (
                        project_id, species_id, label, length, width, depth, 
                        quantity, quality_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', [
                    project_id, species_id, label, length, width, depth, 
                    quantity, quality_id
                ])
            except sqlite3.OperationalError:
                # Fallback if quality_id doesn't exist
                modify_db('''
                    INSERT INTO cuts (
                        project_id, species_id, label, length, width, depth, 
                        quantity
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', [
                    project_id, species_id, label, length, width, depth, 
                    quantity
                ])
                flash(
                    'Database schema needs updating. Run migration script.', 
                    'warning'
                )
        
        flash('Cut added successfully!', 'success')
        return redirect(url_for('view_project', project_id=project_id))
    
    projects = query_db('SELECT * FROM projects')
    species_list = query_db('SELECT * FROM species')
    
    # Try to get quality list
    try:
        quality_list = query_db('SELECT * FROM qualities')
    except sqlite3.OperationalError:
        quality_list = []
        flash('Database schema needs to be updated. Please run the migration script.', 'warning')
    
    return render_template('cut_form.html', projects=projects, species_list=species_list, quality_list=quality_list)

@app.route('/cut/<int:cut_id>/edit', methods=['GET', 'POST'])
def edit_cut(cut_id):
    cut = query_db('SELECT * FROM cuts WHERE id = ?', [cut_id], one=True)
    
    if not cut:
        flash('Cut not found', 'danger')
        return redirect(url_for('projects'))
    
    if request.method == 'POST':
        project_id = request.form['project_id']
        species_id = request.form.get('species_id', None)
        if species_id == '':
            species_id = None
        quality_id = request.form.get('quality_id', None)
        if quality_id == '':
            quality_id = None
        label = request.form['label']
        length = int(request.form['length'])
        width = int(request.form['width'])
        depth = int(request.form['depth'])
        quantity = int(request.form['quantity'])
        allow_joining = 1 if request.form.get('allow_joining') else 0
        
        # Check if allow_joining column exists and update accordingly
        try:
            modify_db('''
                UPDATE cuts SET 
                    project_id = ?, species_id = ?, label = ?, length = ?, 
                    width = ?, depth = ?, quantity = ?, quality_id = ?, 
                    allow_joining = ?
                WHERE id = ?
            ''', [
                project_id, species_id, label, length, width, depth, 
                quantity, quality_id, allow_joining, cut_id
            ])
        except sqlite3.OperationalError:
            # Fallback if allow_joining doesn't exist yet
            try:
                modify_db('''
                    UPDATE cuts SET 
                        project_id = ?, species_id = ?, label = ?, length = ?, 
                        width = ?, depth = ?, quantity = ?, quality_id = ?
                    WHERE id = ?
                ''', [
                    project_id, species_id, label, length, width, depth, 
                    quantity, quality_id, cut_id
                ])
            except sqlite3.OperationalError:
                # Fallback if quality_id doesn't exist
                modify_db('''
                    UPDATE cuts SET 
                        project_id = ?, species_id = ?, label = ?, length = ?, 
                        width = ?, depth = ?, quantity = ?
                    WHERE id = ?
                ''', [
                    project_id, species_id, label, length, width, depth, 
                    quantity, cut_id
                ])
                flash(
                    'Database schema needs updating. Run migration script.', 
                    'warning'
                )
        
        flash('Cut updated successfully!', 'success')
        return redirect(url_for('view_project', project_id=project_id))
    
    projects = query_db('SELECT * FROM projects')
    species_list = query_db('SELECT * FROM species')
    
    # Try to get quality list
    try:
        quality_list = query_db('SELECT * FROM qualities')
    except sqlite3.OperationalError:
        quality_list = []
        flash('Database schema needs to be updated. Please run the migration script.', 'warning')
    
    return render_template('cut_form.html', projects=projects, species_list=species_list, quality_list=quality_list, cut=cut, edit_mode=True)

@app.route('/cut/<int:cut_id>/delete', methods=['POST'])
def delete_cut(cut_id):
    cut = query_db('SELECT * FROM cuts WHERE id = ?', [cut_id], one=True)
    
    if not cut:
        flash('Cut not found', 'danger')
        return redirect(url_for('projects'))
    
    project_id = cut['project_id']
    
    # Delete the cut
    modify_db('DELETE FROM cuts WHERE id = ?', [cut_id])
    
    flash('Cut deleted successfully!', 'success')
    return redirect(url_for('view_project', project_id=project_id))

# Calculate and generate cutting plan
@app.route('/project/<int:project_id>/plan')
def generate_plan(project_id):
    logger.debug(f"Starting generate_plan for project_id={project_id}")

    # fetch project details
    project = query_db('SELECT * FROM projects WHERE id = ?',
                       [project_id], one=True)
    if not project:
        flash('Project not found!', 'error')
        return redirect(url_for('projects'))

    # fetch cuts & inventory
    cuts = query_db('SELECT * FROM cuts WHERE project_id = ?', [project_id])
    inventory = query_db('SELECT * FROM inventory', [])

    # call optimized algorithm
    from wood_cut_calc.cutting_algorithms import generate_basic_plan

    # Check if any cuts have joining enabled
    cuts_with_joining = any(
        cut['allow_joining'] if 'allow_joining' in cut.keys() else False
        for cut in cuts
    )
    
    logger.info(f"Generating cutting plan for {len(cuts)} cuts "
                f"using {len(inventory)} inventory items "
                f"(joining {'enabled' if cuts_with_joining else 'disabled'})")
    plan = generate_basic_plan(cuts, inventory,
                               allow_joining=cuts_with_joining)
    
    # The new algorithm returns solutions directly in the expected format
    solutions = plan.get('solutions', [])
    
    # Add some additional metrics if solutions exist
    if solutions:
        logger.info(f"Generated {len(solutions)} optimized solutions")
        for i, solution in enumerate(solutions):
            strategy = solution.get('efficiency_metrics', {}).get(
                'strategy', f'Solution {i+1}'
            )
            cost = solution.get('total_cost', 0)
            waste = solution.get('waste_percentage', 0)
            logger.debug(f"{strategy}: ${cost:.2f}, {waste:.1f}% waste")
    else:
        logger.warning("No solutions generated - check inventory")
        flash('No cutting solutions could be generated. Please check that '
              'your inventory items can accommodate the required cuts.',
              'warning')

    return render_template('cutting_plan.html', project=project,
                           plan=plan, solutions=solutions)


# API endpoint to import data from CSV
@app.route('/api/import_csv', methods=['POST'])
def import_csv():
    data = request.json
    
    # Create supplier
    supplier_name = data.get('supplier_name', 'Default Supplier')
    
    modify_db('INSERT INTO suppliers (name) VALUES (?)', [supplier_name])
    supplier_id = query_db('SELECT last_insert_rowid()', one=True)[0]
    
    # Add inventory items
    for item in data.get('inventory', []):
        modify_db('INSERT INTO inventory (supplier_id, task, length, height, width, price, link) VALUES (?, ?, ?, ?, ?, ?, ?)',
                 [supplier_id, item['task'], item['length'], item['height'], item['width'], item['price'], item.get('link', '')])
    
    # Create project
    project_name = data.get('project_name', 'Imported Project')
    
    modify_db('INSERT INTO projects (name, description, created_at) VALUES (?, ?, ?)',
             [project_name, 'Imported from CSV', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    project_id = query_db('SELECT last_insert_rowid()', one=True)[0]
    
    # Add cuts
    for cut in data.get('cuts', []):
        modify_db('INSERT INTO cuts (project_id, label, length, width, depth, quantity) VALUES (?, ?, ?, ?, ?, ?)',
                 [project_id, cut['label'], cut['length'], cut['width'], cut['depth'], cut['quantity']])
    
    return jsonify({'success': True, 'supplier_id': supplier_id, 'project_id': project_id})

# Save cutting plan
@app.route('/project/<int:project_id>/plan/save', methods=['POST'])
def save_cutting_plan(project_id):
    # Import our route handler
    from wood_cut_calc.routes import save_cutting_plan as save_cutting_plan_handler

    # Call the handler with our database function
    return save_cutting_plan_handler(project_id, modify_db)

# View saved cutting plan
@app.route('/project/<int:project_id>/plan/<int:plan_id>')
def view_saved_plan(project_id, plan_id):
    # Import our route handler
    from wood_cut_calc.routes import view_saved_plan as view_saved_plan_handler

    # Call the handler with our database function
    return view_saved_plan_handler(project_id, plan_id, query_db)

# Delete saved cutting plan
@app.route('/project/<int:project_id>/plan/<int:plan_id>/delete', methods=['POST'])
def delete_saved_plan(project_id, plan_id):
    # Import our route handler
    from wood_cut_calc.routes import delete_saved_plan as delete_saved_plan_handler

    # Call the handler with our database functions
    return delete_saved_plan_handler(project_id, plan_id, query_db, modify_db)

# PDF feature has been removed as requested

# Initialize the database if it doesn't exist
@app.cli.command('initdb')
def initdb_command():
    init_db()
    print('Initialized the database.')

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        with app.app_context():
            init_db()
    app.run(debug=True)
