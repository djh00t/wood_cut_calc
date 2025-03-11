import os
import sqlite3
import logging
import json
from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify
from datetime import datetime

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

# Register template filters
@app.template_filter('sum_previous_lengths')
def sum_previous_lengths(index, cuts, total_length):
    """
    Calculate the left position for each cut section in the cutting diagram.
    
    Args:
        index: Current index in the loop
        cuts: List of cuts
        total_length: Total length of the item
        
    Returns:
        Percentage position from the left
    """
    try:
        logger.debug(f"sum_previous_lengths called with index={index}, total_length={total_length}")
        logger.debug(f"cuts data: {cuts[:index] if index > 0 else []}")
        
        sum_length = 0
        for i in range(index):
            sum_length += cuts[i]['length']
        
        result = (sum_length / total_length) * 100
        logger.debug(f"sum_previous_lengths result: {result}%")
        return result
    except Exception as e:
        logger.error(f"Error in sum_previous_lengths: {str(e)}", exc_info=True)
        return 0  # Return a safe default value

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
        
        modify_db('INSERT INTO suppliers (name) VALUES (?)', [name])
        flash('Supplier added successfully!', 'success')
        return redirect(url_for('suppliers'))
    
    return render_template('supplier_form.html')

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
                        pass  # Already exists
                
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
        
        modify_db('INSERT INTO projects (name, description, created_at) VALUES (?, ?, ?)',
                 [name, description, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        
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
        
        modify_db('UPDATE projects SET name = ?, description = ? WHERE id = ?',
                 [name, description, project_id])
        
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
        
        # Check if quality_id column exists
        try:
            modify_db('''
                INSERT INTO cuts (project_id, species_id, label, length, width, depth, quantity, quality_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', [project_id, species_id, label, length, width, depth, quantity, quality_id])
        except sqlite3.OperationalError:
            # Fallback if quality_id doesn't exist
            modify_db('''
                INSERT INTO cuts (project_id, species_id, label, length, width, depth, quantity) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', [project_id, species_id, label, length, width, depth, quantity])
            flash('Database schema needs to be updated. Please run the migration script.', 'warning')
        
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
        
        # Check if quality_id column exists
        try:
            modify_db('''
                UPDATE cuts SET 
                project_id = ?, species_id = ?, label = ?, length = ?, width = ?, depth = ?, quantity = ?, quality_id = ? 
                WHERE id = ?
            ''', [project_id, species_id, label, length, width, depth, quantity, quality_id, cut_id])
        except sqlite3.OperationalError:
            # Fallback if quality_id doesn't exist
            modify_db('''
                UPDATE cuts SET 
                project_id = ?, species_id = ?, label = ?, length = ?, width = ?, depth = ?, quantity = ? 
                WHERE id = ?
            ''', [project_id, species_id, label, length, width, depth, quantity, cut_id])
            flash('Database schema needs to be updated. Please run the migration script.', 'warning')
        
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
    
    try:
        project = query_db('SELECT * FROM projects WHERE id = ?', [project_id], one=True)
        logger.debug(f"Project data: {dict(project) if project else None}")
        
        cuts = query_db('''
            SELECT c.*, s.name as species_name, q.name as quality_name
            FROM cuts c 
            LEFT JOIN species s ON c.species_id = s.id 
            LEFT JOIN qualities q ON c.quality_id = q.id
            WHERE c.project_id = ?
        ''', [project_id])
        logger.debug(f"Found {len(cuts) if cuts else 0} cuts for this project")
        
        # Check if we have cuts to work with
        if not cuts:
            logger.warning(f"No cuts found for project {project_id}")
            flash('Unable to generate cutting plan: No cuts defined for this project.', 'warning')
            return redirect(url_for('view_project', project_id=project_id))
        
        # Get all available inventory items with species and quality info
        inventory = query_db('''
            SELECT i.*, s.name as species_name, q.name as quality_name 
            FROM inventory i 
            JOIN species s ON i.species_id = s.id
            LEFT JOIN qualities q ON i.quality_id = q.id
        ''')
        logger.debug(f"Found {len(inventory) if inventory else 0} inventory items")
        
        # Check if we have inventory to work with
        if not inventory:
            logger.warning("No inventory items found in database")
            flash('Unable to generate cutting plan: No inventory items available. Please add inventory first.', 'warning')
            return redirect(url_for('view_project', project_id=project_id))
        
        # Log the cuts and inventory for debugging
        if debug_mode:
            logger.debug("Cuts data:")
            for i, cut in enumerate(cuts):
                logger.debug(f"  Cut {i+1}: {dict(cut)}")
            
            logger.debug("Inventory data:")
            for i, item in enumerate(inventory):
                logger.debug(f"  Item {i+1}: {dict(item)}")
        
        # Process the cuts and generate a plan
        logger.debug("Calling calculate_cutting_plan function")
        shopping_list, cutting_plan, unmatched_dimensions = calculate_cutting_plan(cuts, inventory)
        
        logger.debug(f"Shopping list has {len(shopping_list) if shopping_list else 0} items")
        logger.debug(f"Cutting plan has {len(cutting_plan) if cutting_plan else 0} dimensions")
        
        # Check if we got any results
        if not shopping_list and not cutting_plan:
            logger.warning(f"No cutting plan generated. Unmatched dimensions: {unmatched_dimensions}")
            
            if unmatched_dimensions:
                # Create a more informative error message
                dimension_list = ", ".join(f"{dim} ({len(details['cuts'])} cuts)" for dim, details in unmatched_dimensions.items())
                error_msg = f"Could not generate a cutting plan for dimensions: {dimension_list}. "
                error_msg += "The available inventory items may not be suitable for these cuts."
                flash(error_msg, 'warning')
            else:
                flash('No cutting plan could be generated. This may be because no inventory items match the dimensions needed for your cuts.', 'warning')
            
            return redirect(url_for('view_project', project_id=project_id))
        
        logger.debug("Successfully generated cutting plan, rendering template")
        
        # Create a serializable version of the plan data for potential saving
        serializable_plan = {
            'project_id': project_id,
            'shopping_list': {},
            'cutting_plan': {},
            'unmatched_dimensions': {}
        }
        
        # Convert shopping list to serializable format
        for key, item_data in shopping_list.items():
            serializable_plan['shopping_list'][key] = {
                'item': dict(item_data['item']),
                'quantity': item_data['quantity'],
                'total_price': item_data['total_price']
            }
        
        # Convert cutting plan to serializable format
        for dimension, plans in cutting_plan.items():
            serializable_plan['cutting_plan'][dimension] = []
            for plan in plans:
                serializable_cuts = []
                for cut in plan['cuts']:
                    serializable_cuts.append(dict(cut))
                
                serializable_plan['cutting_plan'][dimension].append({
                    'item': dict(plan['item']),
                    'cuts': serializable_cuts,
                    'waste': plan['waste'],
                    'waste_percent': plan.get('waste_percent', 0),
                    'is_cost_efficient': plan.get('is_cost_efficient', False),
                    'efficiency_note': plan.get('efficiency_note', '')
                })
        
        # Convert unmatched dimensions to serializable format
        for dim, details in unmatched_dimensions.items():
            serializable_cuts = []
            for cut in details['cuts']:
                serializable_cuts.append(dict(cut))
            
            serializable_plan['unmatched_dimensions'][dim] = {
                'cuts': serializable_cuts,
                'reason': details['reason']
            }
        
        # Store the serializable plan in the session for saving later
        serialized_data = json.dumps(serializable_plan)
        
        # Pass temp_plan_data to the template for saving functionality
        return render_template('cutting_plan.html', 
                            project=project, 
                            shopping_list=shopping_list, 
                            cutting_plan=cutting_plan,
                            unmatched_dimensions=unmatched_dimensions,
                            temp_plan_data=serialized_data)
                            
    except Exception as e:
        logger.error(f"Error generating cutting plan: {str(e)}", exc_info=True)
        flash(f"An error occurred when generating the cutting plan: {str(e)}", 'danger')
        return redirect(url_for('view_project', project_id=project_id))

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

def calculate_cutting_plan(cuts, inventory):
    """
    Calculates the optimal cutting plan based on the required cuts and available inventory.
    
    Returns:
    - shopping_list: List of inventory items to purchase with quantities
    - cutting_plan: How to cut each purchased item
    - unmatched_dimensions: Dictionary of dimensions that couldn't be matched with suitable inventory
    """
    logger.debug("Starting calculate_cutting_plan")
    
    # Group cuts by dimensions (width x depth) and species
    grouped_cuts = {}
    for cut in cuts:
        # Create a composite key including species and quality if available
        # SQLite Row objects don't support .get() method, use dictionary-like access with a fallback
        species_id = cut['species_id'] if 'species_id' in cut else None
        
        # Check if quality_id exists in the cut data
        try:
            quality_id = cut['quality_id'] if 'quality_id' in cut else None
        except:
            quality_id = None
            
        species_part = f"_{species_id}" if species_id else ""
        quality_part = f"_{quality_id}" if quality_id else ""
        key = f"{cut['width']}x{cut['depth']}{species_part}{quality_part}"
        
        if key not in grouped_cuts:
            grouped_cuts[key] = []
        
        # Add cut multiple times based on quantity
        for i in range(cut['quantity']):
            grouped_cuts[key].append({
                'label': cut['label'],
                'length': cut['length'],
                'width': cut['width'],
                'depth': cut['depth'],
                'species_id': species_id,
                'species_name': cut['species_name'] if 'species_name' in cut else None,
                'quality_id': quality_id,
                'quality_name': cut.get('quality_name') if hasattr(cut, 'get') else (cut['quality_name'] if 'quality_name' in cut else None)
            })
    
    logger.debug(f"Grouped cuts by dimensions: {list(grouped_cuts.keys())}")
    
    # Match inventory to dimensions
    matching_inventory = {}
    for key in grouped_cuts:
        try:
            # Parse the key to get dimensions, species and quality
            key_parts = key.split('_')
            dimensions = key_parts[0]
            species_id = int(key_parts[1]) if len(key_parts) > 1 and key_parts[1] else None
            quality_id = int(key_parts[2]) if len(key_parts) > 2 and key_parts[2] else None
            
            width, depth = map(int, dimensions.split('x'))
            matching_inventory[key] = []
            
            logger.debug(f"Looking for inventory matching width={width}, depth={depth}, species_id={species_id}")
            
            for item in inventory:
                # Match by dimensions (allow for rotation if width/depth are swapped)
                dimensions_match = (item['width'] == width and item['height'] == depth) or \
                                  (item['width'] == depth and item['height'] == width)
                
                # Match by species if a species was specified for the cut
                species_match = True
                if species_id is not None:
                    species_match = item['species_id'] == species_id
                
                # Match by quality if a quality was specified for the cut
                quality_match = True
                if quality_id is not None:
                    # Check if item has quality_id field (for backward compatibility)
                    item_quality_id = item.get('quality_id') if hasattr(item, 'get') else (item['quality_id'] if 'quality_id' in item else None)
                    quality_match = item_quality_id == quality_id
                
                if dimensions_match and species_match and quality_match:
                    matching_inventory[key].append(item)
                    # Get product name safely
                    product_name = None
                    if 'product_name' in item:
                        product_name = item['product_name']
                    elif 'task' in item:
                        product_name = item['task']
                    else:
                        product_name = f"Item #{item['id']}"
                    
                    logger.debug(f"  Match found: Item ID {item['id']} - {product_name} ({item['length']}x{item['width']}x{item['height']})")
            
            if not matching_inventory[key]:
                warning_msg = f"No matching inventory found for dimension {dimensions}"
                
                if species_id:
                    species_name = next((cut['species_name'] for cut in grouped_cuts[key] if cut.get('species_name')), "Unknown")
                    warning_msg += f" with species {species_name}"
                
                if quality_id:
                    quality_name = next((cut['quality_name'] for cut in grouped_cuts[key] if cut.get('quality_name')), "Unknown")
                    warning_msg += f" and quality {quality_name}"
                
                logger.warning(warning_msg)
        except Exception as e:
            logger.error(f"Error processing dimension key {key}: {str(e)}", exc_info=True)
    
    # Generate cutting plan using a cost-optimized algorithm
    shopping_list = {}
    cutting_plan = {}
    
    for dimension, cuts_list in grouped_cuts.items():
        logger.debug(f"Processing dimension {dimension} with {len(cuts_list)} cuts")
        
        # Sort cuts by length (descending)
        cuts_list.sort(key=lambda x: x['length'], reverse=True)
        
        # Get available inventory for this dimension
        available_items = matching_inventory[dimension]
        if not available_items:
            logger.warning(f"Skipping dimension {dimension}: No matching inventory available")
            continue
        
        # Try all inventory options and keep the most cost-effective solution
        best_solution = None
        best_total_cost = float('inf')
        best_item_count = 0
        best_cutting_plan = []
        
        for item_option in available_items:
            # Get product name safely
            product_name = None
            if 'product_name' in item_option:
                product_name = item_option['product_name']
            elif 'task' in item_option:
                product_name = item_option['task']
            else:
                product_name = f"Item #{item_option['id']}"
                
            logger.debug(f"Trying item {item_option['id']} - {product_name} ({item_option['length']}x{item_option['width']}x{item_option['height']})")
            
            # Check if any cuts are larger than the inventory item length
            too_large_cuts = [cut for cut in cuts_list if cut['length'] > item_option['length']]
            if too_large_cuts:
                logger.warning(f"Found {len(too_large_cuts)} cuts that are too large for inventory item length {item_option['length']}mm")
                # Skip this inventory item if there are cuts that will never fit
                continue
            
            # Try to fit cuts on this item type
            remaining_cuts = cuts_list.copy()
            item_count = 0
            current_cutting_plan = []
            max_iterations = 1000  # Safety limit to prevent infinite loops
            iterations = 0
            total_waste = 0
            
            # Track if we're making progress with this inventory option
            has_progress = True
            
            while remaining_cuts and has_progress and iterations < max_iterations:
                iterations += 1
                item_count += 1
                current_length = item_option['length']
                cuts_on_this_item = []
                
                i = 0
                while i < len(remaining_cuts):
                    cut = remaining_cuts[i]
                    # Check if this cut fits on the current item
                    if cut['length'] <= current_length:
                        cuts_on_this_item.append(cut)
                        current_length -= cut['length']
                        remaining_cuts.pop(i)
                    else:
                        i += 1
                
                # Check if we made any progress (used any cuts)
                if len(cuts_on_this_item) == 0:
                    logger.warning(f"No cuts could be placed on item {item_count} (length: {item_option['length']}mm)")
                    has_progress = False
                    item_count -= 1  # Rollback the increment as we're not using this item
                    break
                
                # Calculate waste for this item
                waste = current_length
                total_waste += waste
                
                # Record the cutting plan for this item
                current_cutting_plan.append({
                    'item': item_option,
                    'cuts': cuts_on_this_item,
                    'waste': waste,
                    'waste_percent': (waste / item_option['length']) * 100
                })
                
                logger.debug(f"Item {item_count}: Used {len(cuts_on_this_item)} cuts with {waste}mm waste")
            
            # Calculate total cost for this solution
            total_cost = item_count * item_option['price']
            
            # Only consider complete solutions (all cuts used)
            if item_count > 0 and not remaining_cuts:
                # Get product name safely
                product_name = None
                if 'product_name' in item_option:
                    product_name = item_option['product_name']
                elif 'task' in item_option:
                    product_name = item_option['task']
                else:
                    product_name = f"Item #{item_option['id']}"
                
                logger.debug(f"Complete solution found using {product_name} ({item_option['length']}mm): "
                           f"{item_count} items, total cost ${total_cost:.2f}, total waste {total_waste}mm")
                
                # Check if this is the cheapest solution so far
                if total_cost < best_total_cost:
                    best_solution = item_option
                    best_total_cost = total_cost
                    best_item_count = item_count
                    best_cutting_plan = current_cutting_plan
                    
                    # Add cost efficiency info to each cutting plan item
                    avg_waste_percent = total_waste / (item_count * item_option['length']) * 100
                    for plan in best_cutting_plan:
                        # Only mark as cost-efficient if it has significant waste (over 20%)
                        if plan['waste_percent'] > 20:
                            plan['is_cost_efficient'] = True
                            shorter_options = [i for i in available_items if i['length'] < item_option['length']]
                            if shorter_options:
                                shortest = min(shorter_options, key=lambda x: x['length'])
                                plan['efficiency_note'] = f"Using {item_option['length']}mm instead of {shortest['length']}mm is more cost-effective overall"
                            else:
                                plan['efficiency_note'] = f"This longer board is more cost-effective than using multiple shorter pieces"
                        else:
                            plan['is_cost_efficient'] = False
                        plan['avg_waste_percent'] = avg_waste_percent
            else:
                if remaining_cuts:
                    # Get product name safely
                    product_name = None
                    if 'product_name' in item_option:
                        product_name = item_option['product_name']
                    elif 'task' in item_option:
                        product_name = item_option['task']
                    else:
                        product_name = f"Item #{item_option['id']}"
                    
                    logger.warning(f"Incomplete solution with {product_name} - {len(remaining_cuts)} cuts couldn't be placed")
                else:
                    logger.warning(f"No viable cutting solution found with item {item_option['id']}")
        
        # Add best solution to shopping list and cutting plan
        if best_solution:
            item_key = f"{best_solution['id']}"
            if item_key in shopping_list:
                shopping_list[item_key]['quantity'] += best_item_count
                shopping_list[item_key]['total_price'] = shopping_list[item_key]['quantity'] * best_solution['price']
            else:
                shopping_list[item_key] = {
                    'item': best_solution,
                    'quantity': best_item_count,
                    'total_price': best_item_count * best_solution['price']
                }
            
            # Save cutting plan
            cutting_plan[dimension] = best_cutting_plan
            
            # Get product name safely
            product_name = None
            if 'product_name' in best_solution:
                product_name = best_solution['product_name']
            elif 'task' in best_solution:
                product_name = best_solution['task']
            else:
                product_name = f"Item #{best_solution['id']}"
                
            logger.debug(f"Best solution for dimension {dimension}: {best_item_count} items of {product_name}, "
                       f"total cost: ${best_total_cost:.2f}")
        else:
            logger.warning(f"No valid solution found for dimension {dimension}")
    
    # Find dimensions that couldn't be matched or had incomplete solutions
    unmatched_dimensions = {}
    for dimension, cuts_list in grouped_cuts.items():
        if dimension not in cutting_plan:
            # Extract dimension details for more user-friendly error message
            key_parts = dimension.split('_')
            dimensions = key_parts[0]
            species_id = int(key_parts[1]) if len(key_parts) > 1 and key_parts[1] else None
            quality_id = int(key_parts[2]) if len(key_parts) > 2 and key_parts[2] else None
            
            # Get readable names
            species_name = cuts_list[0].get('species_name') if species_id and cuts_list else None
            quality_name = cuts_list[0].get('quality_name') if quality_id and cuts_list else None
            
            # Build detailed reason
            reason = 'No matching inventory items found'
            if species_name:
                reason += f" with species '{species_name}'"
            if quality_name:
                reason += f" and quality '{quality_name}'"
                
            unmatched_dimensions[dimension] = {
                'cuts': cuts_list,
                'reason': reason,
                'dimensions': dimensions,
                'species_name': species_name,
                'quality_name': quality_name
            }
            logger.warning(f"Dimension {dimension} couldn't be matched to any inventory items")
    
    logger.debug(f"Calculation complete. Shopping list: {len(shopping_list)} items, Cutting plan: {len(cutting_plan)} dimension groups")
    logger.debug(f"Unmatched dimensions: {len(unmatched_dimensions)}")
    
    return shopping_list, cutting_plan, unmatched_dimensions

# Save cutting plan
@app.route('/project/<int:project_id>/plan/save', methods=['POST'])
def save_cutting_plan(project_id):
    try:
        plan_name = request.form.get('plan_name', f"Cutting Plan {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        plan_data = request.form.get('plan_data')
        
        if not plan_data:
            flash('Error: No plan data provided', 'danger')
            return redirect(url_for('view_project', project_id=project_id))
        
        # Save the plan to the database
        modify_db('INSERT INTO saved_plans (project_id, name, plan_data) VALUES (?, ?, ?)',
                [project_id, plan_name, plan_data])
        
        flash(f'Cutting plan "{plan_name}" saved successfully!', 'success')
        return redirect(url_for('view_project', project_id=project_id))
        
    except Exception as e:
        logger.error(f"Error saving cutting plan: {str(e)}", exc_info=True)
        flash(f"An error occurred when saving the cutting plan: {str(e)}", 'danger')
        return redirect(url_for('view_project', project_id=project_id))

# View saved cutting plan
@app.route('/project/<int:project_id>/plan/<int:plan_id>')
def view_saved_plan(project_id, plan_id):
    try:
        project = query_db('SELECT * FROM projects WHERE id = ?', [project_id], one=True)
        saved_plan = query_db('SELECT * FROM saved_plans WHERE id = ? AND project_id = ?', 
                           [plan_id, project_id], one=True)
        
        if not saved_plan:
            flash('Saved plan not found', 'danger')
            return redirect(url_for('view_project', project_id=project_id))
        
        # Parse the saved plan data
        plan_data = json.loads(saved_plan['plan_data'])
        
        # Reconstruct the plan components
        shopping_list = plan_data['shopping_list']
        cutting_plan = plan_data['cutting_plan']
        unmatched_dimensions = plan_data['unmatched_dimensions']
        
        return render_template('cutting_plan.html',
                            project=project,
                            shopping_list=shopping_list,
                            cutting_plan=cutting_plan,
                            unmatched_dimensions=unmatched_dimensions,
                            saved_plan=saved_plan)
                            
    except Exception as e:
        logger.error(f"Error viewing saved plan: {str(e)}", exc_info=True)
        flash(f"An error occurred when viewing the saved plan: {str(e)}", 'danger')
        return redirect(url_for('view_project', project_id=project_id))

# Delete saved cutting plan
@app.route('/project/<int:project_id>/plan/<int:plan_id>/delete', methods=['POST'])
def delete_saved_plan(project_id, plan_id):
    try:
        # Check if plan exists
        saved_plan = query_db('SELECT * FROM saved_plans WHERE id = ? AND project_id = ?', 
                           [plan_id, project_id], one=True)
        
        if not saved_plan:
            flash('Saved plan not found', 'danger')
            return redirect(url_for('view_project', project_id=project_id))
        
        # Delete the plan
        modify_db('DELETE FROM saved_plans WHERE id = ?', [plan_id])
        
        flash('Saved plan deleted successfully!', 'success')
        return redirect(url_for('view_project', project_id=project_id))
        
    except Exception as e:
        logger.error(f"Error deleting saved plan: {str(e)}", exc_info=True)
        flash(f"An error occurred when deleting the saved plan: {str(e)}", 'danger')
        return redirect(url_for('view_project', project_id=project_id))

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