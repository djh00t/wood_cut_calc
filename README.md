# Wood Cutting Calculator

An application that helps woodworkers optimize cutting plans by solving the bin packing problem. This tool allows you to manage timber suppliers, inventory, projects, and calculate the most efficient cutting plan for your woodworking projects.

## Features

- **Supplier Management**: Add and track timber suppliers
- **Inventory Management**: Record available timber products with dimensions and prices
- **Project Management**: Create woodworking projects with custom cut lists
- **Cutting Optimization**: Calculate optimal cutting plans to minimize waste
- **Visual Cutting Diagrams**: Visual representation of how to cut each piece of timber
- **Shopping List Generation**: Generate shopping lists with total costs
- **CSV Import**: Import project data via CSV file

## Installation

### Prerequisites
- Python 3.8+
- Poetry (Python package manager)
- Docker (optional, for containerized deployment)

### Setup with Poetry

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/wood_cut_calc.git
   cd wood_cut_calc
   ```

2. Install Poetry if you don't have it:
   ```
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. Install dependencies and set up the project:
   ```
   # Using the setup script
   python setup.py
   
   # Or using the Makefile
   make setup
   ```

4. Run the application:
   ```
   # Using poetry directly
   poetry run flask run
   
   # Or using the Makefile
   make run
   ```

5. Open your browser and navigate to `http://127.0.0.1:5000/`

### Setup with Docker

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/wood_cut_calc.git
   cd wood_cut_calc
   ```

2. Build and run the Docker container:
   ```
   # Using docker-compose directly
   docker-compose up -d
   
   # Or using the Makefile
   make docker-build
   make docker-run
   ```

3. Open your browser and navigate to `http://127.0.0.1:5000/`

## Usage Guide

### Setting Up Suppliers and Inventory

1. **Add Suppliers**: Navigate to the Suppliers page and click "Add Supplier" to create a new timber supplier.

2. **Add Inventory Items**: From a supplier's page, click "Add Inventory Item" to add timber products. Enter:
   - Task/Description (e.g., "Pine Beam", "Oak Board")
   - Dimensions (Length, Height, Width in mm)
   - Price
   - Optional link to the product

### Creating Projects and Cuts

1. **Create Project**: Go to the Projects page and click "Add Project" to create a new woodworking project.

2. **Add Cuts**: From a project page, click "Add Cut" to add required timber pieces. Enter:
   - Label (e.g., "Table Leg", "Shelf")
   - Dimensions (Length, Width, Depth in mm)
   - Quantity needed

### Generating Cutting Plans

1. From your project page, click the "Generate Cutting Plan" button.

2. The system will calculate the optimal way to cut your required pieces from standard timber sizes.

3. Review the generated:
   - Shopping list with materials to purchase and total cost
   - Cutting diagrams showing how to cut each piece of timber

### Importing from CSV

You can import data using a CSV file with the following format:

```
Inventory
Item,Length,Height,Width,Price,Link
Pine Plank,2400,25,100,$12.50,https://supplier.com/item1
Oak Board,1800,20,150,$18.75,https://supplier.com/item2
,,,,, 

Cuts
Label,Length,Width,Depth,Quantity
Table Leg,400,50,50,4
Shelf,1200,200,20,3
```

## Development

This application is built with:
- Flask (Python web framework)
- SQLite (Database)
- Bootstrap 5 (Frontend)
- JavaScript (Client-side interactions)

### Available Make Commands

The project includes a Makefile with useful commands:

```
make setup         # Set up the project (install dependencies, initialize database)
make run           # Run the Flask application
make initdb        # Initialize or reset the database
make clean         # Remove database and cache files
make docker-build  # Build the Docker container
make docker-run    # Run the application in Docker
make docker-stop   # Stop the Docker container
make lint          # Run code linter
make format        # Format code using Black and isort
make help          # Show available commands
```

## License

MIT License
