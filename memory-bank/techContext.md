# Technical Context: Wood Cutting Calculator

## Technologies Used

- **Backend**: Python 3.9+ with Flask framework
- **Database**: SQLite with Flask wrappers
- **Frontend**: Bootstrap, Jinja2 templates
- **Package Management**: Poetry

## Architecture Overview

The Wood Cutting Calculator has been refactored into a modular structure:

```
wood_cut_calc/
├── __init__.py           # Package initialization
├── __main__.py           # Application entry point
├── cutting_algorithms.py # Core algorithm implementation
├── svg_generator.py      # SVG diagram generation utilities
└── routes.py             # Flask route handlers
```

## Key Components

### 1. Cutting Algorithm Module

The `cutting_algorithms.py` module implements:

- Type definitions using TypedDict for strong typing
- Two-phase cutting plan algorithm:
  - Phase 1: Strict dimensions matching
  - Phase 2: Wildcard dimension handling
- Support for multiple solutions (up to 5 alternatives)
- Part rotation detection
- Waste calculation
- Proper part numbering using sheet_id.part_id format

### 2. SVG Generator

The `svg_generator.py` module provides:

- SVG diagram generation for cutting plans
- Functions to visualize cuts and waste
- Part labeling with dimensions and rotation information
- Support for multiple sheets per solution

### 3. Route Handlers

The `routes.py` module contains:

- Flask route handlers for generating cutting plans
- Logic for saving/loading cutting plans
- Integration between cutting algorithms and templates

## Data Structures

Key data structures include:

1. **CutDict**: 
   - Represents a single cut with dimensions and metadata
   - Includes wildcard dimension support (width=0 or depth=0)

2. **InventoryDict**:
   - Represents an inventory item with dimensions, price, source, etc.

3. **CuttingSolution**:
   - Combines shopping list, cutting plan, and assignments
   - Includes SVG diagrams and wildcard assignments

4. **CutAssignment**:
   - Maps cuts to specific positions on sheets
   - Includes positioning and rotation information

## Technical Constraints

1. **Database Compatibility**:
   - Must handle sqlite3.Row objects which don't have dict-like methods
   - Added conversion layer between database rows and TypedDict objects

2. **Jinja2 Template Requirements**:
   - Templates expect certain data structures
   - Need careful data structure transformation

3. **SVG Generation**:
   - Dynamically generated SVG code embedded in HTML
   - Requires proper escaping and safe rendering

## Integration Points

1. **app.py ↔ wood_cut_calc**:
   - Main application imports from the package
   - Replaces original calculate_cutting_plan function

2. **Routes ↔ Templates**:
   - Routes prepare data structures for templates
   - Templates render shopping lists, cutting diagrams, etc.

3. **Algorithms ↔ SVG Generator**:
   - Algorithms pass cut assignments to SVG generator
   - SVG generator creates diagrams based on assignments

## Current Technical Challenges

1. **Integration Issues**:
   - Proper passing of data between modules
   - Converting between different data structure formats

2. **Frontend Rendering**:
   - Ensuring SVG diagrams render properly
   - Displaying part numbering correctly

3. **No Matching Inventory**:
   - Addressing warnings about unmatched dimensions
   - Need better error handling in this case
