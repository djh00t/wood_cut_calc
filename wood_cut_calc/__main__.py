"""Main entry point for the Wood Cut Calculator application.

This module configures and runs the Flask application.
"""

import os
import sys

# Add the parent directory to the Python path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """Run the application by importing and running the main app."""
    from app import app
    app.run(debug=True)


if __name__ == '__main__':
    main()
