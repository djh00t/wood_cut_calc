# System Patterns: Wood Cutting Calculator

## Architecture Overview

The Wood Cutting Calculator is built on a **Flask-based web application** with a **SQLite database backend**. The architecture follows a simplified MVC (Model-View-Controller) pattern:

- **Models**: Represented through database tables (suppliers, inventory, species, qualities, projects, cuts, saved_plans)
- **Views**: Jinja2 HTML templates for rendering UI
- **Controllers**: Flask routes in app.py that handle business logic

## Key Design Patterns

### 1. Data Access Layer

The application uses a simple data access layer with utility functions:
- `get_db()`: Establishes database connections
- `query_db()`: Executes SELECT queries and returns results
- `modify_db()`: Executes INSERT/UPDATE/DELETE operations with automatic commit

```python
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def modify_db(query, args=()):
    db = get_db()
    db.execute(query, args)
    db.commit()
```

### 2. Bin Packing Algorithm

The heart of the application is its bin packing algorithm (calculate_cutting_plan function) that:
1. Groups cuts by dimensions, species, and quality
2. Matches inventory items to dimension groups
3. Generates optimal assignments using a partition-based approach
4. Calculates waste and cost efficiency

The algorithm handles special cases:
- Standard cuts with exact dimensions
- Flexible/wildcard dimensions (width=0 or height=0)
- Species and quality matching

```python
def _all_cut_partitions(cuts, inventory, fits_fn):
    """Generate all valid assignments of cuts to inventory pieces."""
    # Recursive algorithm for finding optimal partitions
    # ...
```

### 3. Migration System

The application uses a simple migration system to handle schema changes:
- Individual migration scripts in the `/migrations` folder
- A migration manager that tracks and runs migrations
- Database schema can evolve without losing data

```python
def migrate_quality_to_relation():
    """Migration to convert quality text field to a relation with qualities table"""
    # ...
```

### 4. Template Extension Pattern

UI components follow a template inheritance pattern:
- `base.html` provides the common layout, navigation, and styling
- Feature-specific templates extend the base template
- Reusable UI components (cards, forms, etc.) follow consistent patterns

```html
{% extends 'base.html' %}
{% block content %}
  <!-- Page-specific content -->
{% endblock %}
```

## Data Model Relationships

```
suppliers (1) --- (*) inventory --- (*) cuts --- (*) projects
                      |                |
                      v                v
                    species          saved_plans
                      |
                      v
                    qualities
```

Key relationships:
- An inventory item belongs to one supplier and one species
- A cut belongs to one project and can specify species and quality
- A project can have multiple cuts and saved plans
- Inventory and cuts can specify timber quality

## Critical Implementation Paths

### 1. Cut Planning Process

1. `generate_plan(project_id)`: Entry point for plan generation
2. `calculate_cutting_plan(cuts, inventory)`: Core algorithm that:
   - Groups cuts by dimensions, species, and quality
   - Matches with available inventory
   - Generates optimal assignments
   - Calculates waste and cost metrics
3. Template rendering: Displays the plan with visual diagrams

### 2. Dimension Matching Logic

The dimension matching is particularly important:
```python
# Handle flexible dimension matching (when width or depth is 0)
if width == 0 and depth == 0:
    # If both dimensions are 0, any item will match (just considering length)
    dimensions_match = True
elif width == 0:
    # If width is 0, only match on depth (any width is acceptable)
    dimensions_match = item['height'] >= depth or item['width'] >= depth
elif depth == 0:
    # If depth is 0, only match on width (any depth is acceptable)
    dimensions_match = item['width'] >= width or item['height'] >= width
else:
    # Original matching logic for exact dimensions (allowing rotation)
    dimensions_match = (item['width'] == width and item['height'] == depth) or \
                      (item['width'] == depth and item['height'] == width)
```

### 3. Data Validation Flow

1. Form submission in route handler
2. Validation of form data (types, required fields)
3. Database consistency checks (foreign keys, uniqueness)
4. Flash messages for user feedback

## Error Handling Patterns

1. Database errors are caught and displayed as flash messages
2. Migration failures include rollback mechanisms
3. Missing inventory or dimension mismatches generate helpful user messages
4. Database existence checks prevent runtime errors
