# Wood Cutting Calculator

A web application for optimizing cutting plans for woodworking projects.

## Overview

The Wood Cutting Calculator helps woodworkers minimize waste and cost by efficiently allocating required parts to available inventory items. It supports wildcard dimensions (0 thickness) and generates optimized cutting plans with visual diagrams.

## Key Features

- Inventory management (suppliers, timber species, quality grades)
- Project and cuts management
- Multiple optimized cutting solutions
- Support for wildcard dimensions (flexible width or thickness)
- SVG-based cutting diagrams
- Proper part numbering (e.g., "1.01")
- Waste calculation and visualization
- Cost optimization

## Project Structure

The project has been restructured into a modular package:

```
wood_cut_calc/
├── __init__.py           # Package initialization
├── __main__.py           # Application entry point
├── cutting_algorithms.py # Cutting plan optimization algorithms  
├── svg_generator.py      # SVG diagram generation
└── routes.py             # Flask route handlers

templates/                # Jinja2 templates
static/                   # Static assets
```

## Running the Application

### Method 1: Original Method (app.py)

```bash
python app.py
```

### Method 2: Using the Package (Recommended)

```bash
python -m wood_cut_calc
```

## Development

This project uses Poetry for dependency management and packaging:

```bash
# Install dependencies
poetry install

# Run the application
poetry run python -m wood_cut_calc
```

## Implementation Details

### Cutting Plan Algorithm

The cutting plan algorithm follows a phased approach:

1. **Strict Matching Phase**:
   - Processes cuts with non-zero dimensions using strict matching
   - Groups cuts by dimensions, species, and quality
   - Matches with appropriate inventory items
   - Optimizes assignments to minimize waste

2. **Wildcard Matching Phase**:
   - Generates different possible assignments for wildcard dimensions
   - Creates up to 5 distinct solutions with different assignments
   - Combines with strict cut plans

### SVG Diagram Generation

The application now generates SVG-based cutting diagrams that:

- Scale properly regardless of dimensions
- Show cuts and waste in different colors
- Include labels with part numbers, dimensions, and rotation indicators
- Support downloading and printing

## Licensing

See LICENSE file for details.
