FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get install weasyprint

# Install Poetry
RUN pip install poetry

# Copy poetry configuration files
COPY pyproject.toml ./

# Configure poetry to not use a virtual environment in Docker
RUN poetry config virtualenvs.create false

# Install project dependencies
RUN poetry install --no-dev

# Copy the rest of the application
COPY . .

# Initialize the database
RUN python -c "import os; from app import app, init_db; os.environ['FLASK_APP'] = 'app.py'; os.environ['FLASK_ENV'] = 'production'; with app.app_context(): init_db();"

# Expose the port the app will run on
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]