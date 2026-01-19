#!/usr/bin/env python
"""
Diagora - Oracle EBS AI Control System
Entry point for the Flask application
"""
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))

    print(f"""
    =========================================================
    |         Diagora - Oracle EBS AI Control System        |
    =========================================================
    |  Running on: http://{host}:{port}
    |  Debug mode: {debug}
    =========================================================
    """)

    app.run(host=host, port=port, debug=debug)
