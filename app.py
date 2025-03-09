import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'wood_planner_secret_key'

# Database configuration
DATABASE = 'wood_planner.db'

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
    sum_length = 0
    for i in range(index):
        sum_length += cuts[i]['length']
    
    return (sum_length / total_length) * 100

@app.template_filter('enumerate')
def _enumerate(iterable):
    """
    Enumerate filter for Jinja templates
    """
    return enumerate(iterable)

@app.route('/')
def index():
    return render_template('index.html')

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
        flash('Supplier added successfully!')
        return redirect(url_for('suppliers'))
    
    return render_template('supplier_form.html')

@app.route('/supplier/<int:supplier_id>')
def view_supplier(supplier_id):
    supplier = query_db('SELECT * FROM suppliers WHERE id = ?', [supplier_id], one=True)
    inventory = query_db('SELECT * FROM inventory WHERE supplier_id = ?', [supplier_id])
    return render_template('supplier_view.html', supplier=supplier, inventory=inventory)

# Inventory routes
@app.route('/inventory/add', methods=['GET', 'POST'])
def add_inventory():
    if request.method == 'POST':
        supplier_id = request.form['supplier_id']
        task = request.form['task']
        length = int(request.form['length'])
        height = int(request.form['height'])
        width = int(request.form['width'])
        price = float(request.form['price'])
        link = request.form['link']
        
        modify_db('INSERT INTO inventory (supplier_id, task, length, height, width, price, link) VALUES (?, ?, ?, ?, ?, ?, ?)',
                 [supplier_id, task, length, height, width, price, link])
        
        flash('Inventory item added successfully!')
        return redirect(url_for('view_supplier', supplier_id=supplier_id))
    
    suppliers = query_db('SELECT * FROM suppliers')
    return render_template('inventory_form.html', suppliers=suppliers)

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
        
        flash('Project added successfully!')
        return redirect(url_for('projects'))
    
    return render_template('project_form.html')

@app.route('/project/<int:project_id>')
def view_project(project_id):
    project = query_db('SELECT * FROM projects WHERE id = ?', [project_id], one=True)
    cuts = query_db('SELECT * FROM cuts WHERE project_id = ?', [project_id])
    return render_template('project_view.html', project=project, cuts=cuts)

# Cut routes
@app.route('/cut/add', methods=['GET', 'POST'])
def add_cut():
    if request.method == 'POST':
        project_id = request.form['project_id']
        label = request.form['label']
        length = int(request.form['length'])
        width = int(request.form['width'])
        depth = int(request.form['depth'])
        quantity = int(request.form['quantity'])
        
        modify_db('INSERT INTO cuts (project_id, label, length, width, depth, quantity) VALUES (?, ?, ?, ?, ?, ?)',
                 [project_id, label, length, width, depth, quantity])
        
        flash('Cut added successfully!')
        return redirect(url_for('view_project', project_id=project_id))
    
    projects = query_db('SELECT * FROM projects')
    return render_template('cut_form.html', projects=projects)

# Calculate and generate cutting plan
@app.route('/project/<int:project_id>/plan')
def generate_plan(project_id):
    project = query_db('SELECT * FROM projects WHERE id = ?', [project_id], one=True)
    cuts = query_db('SELECT * FROM cuts WHERE project_id = ?', [project_id])
    
    # Get all available inventory items
    inventory = query_db('SELECT * FROM inventory')
    
    # Process the cuts and generate a plan
    shopping_list, cutting_plan = calculate_cutting_plan(cuts, inventory)
    
    return render_template('cutting_plan.html', 
                          project=project, 
                          shopping_list=shopping_list, 
                          cutting_plan=cutting_plan)

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
    """
    # Group cuts by dimensions (width x depth)
    grouped_cuts = {}
    for cut in cuts:
        key = f"{cut['width']}x{cut['depth']}"
        if key not in grouped_cuts:
            grouped_cuts[key] = []
        
        # Add cut multiple times based on quantity
        for i in range(cut['quantity']):
            grouped_cuts[key].append({
                'label': cut['label'],
                'length': cut['length'],
                'width': cut['width'],
                'depth': cut['depth']
            })
    
    # Match inventory to dimensions
    matching_inventory = {}
    for key in grouped_cuts:
        width, depth = map(int, key.split('x'))
        matching_inventory[key] = []
        
        for item in inventory:
            # Match by dimensions (allow for rotation if width/depth are swapped)
            if (item['width'] == width and item['height'] == depth) or \
               (item['width'] == depth and item['height'] == width):
                matching_inventory[key].append(item)
    
    # Generate cutting plan using first-fit decreasing algorithm
    shopping_list = {}
    cutting_plan = {}
    
    for dimension, cuts_list in grouped_cuts.items():
        # Sort cuts by length (descending)
        cuts_list.sort(key=lambda x: x['length'], reverse=True)
        
        # Get available inventory for this dimension
        available_items = matching_inventory[dimension]
        if not available_items:
            continue
            
        # Sort available items by price per mm
        available_items.sort(key=lambda x: x['price'] / x['length'])
        
        # For each dimension, find the most cost-effective option
        for item_option in available_items:
            # Try to fit cuts on this item type
            remaining_cuts = cuts_list.copy()
            item_count = 0
            current_cutting_plan = []
            
            while remaining_cuts:
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
                
                # Record the cutting plan for this item
                current_cutting_plan.append({
                    'item': item_option,
                    'cuts': cuts_on_this_item,
                    'waste': current_length
                })
            
            # Add to shopping list
            item_key = f"{item_option['id']}"
            if item_key in shopping_list:
                shopping_list[item_key]['quantity'] += item_count
                shopping_list[item_key]['total_price'] = shopping_list[item_key]['quantity'] * item_option['price']
            else:
                shopping_list[item_key] = {
                    'item': item_option,
                    'quantity': item_count,
                    'total_price': item_count * item_option['price']
                }
            
            # Save cutting plan
            cutting_plan[dimension] = current_cutting_plan
            
            # We found a solution for this dimension, so break
            break
    
    return shopping_list, cutting_plan

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