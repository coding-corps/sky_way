from flask import Flask, send_from_directory, jsonify, abort  # Import necessary modules from Flask
from flask_cors import CORS  # Import CORS to handle Cross-Origin Resource Sharing
from routes import bp  # Import blueprint for routing (assumed to be defined in 'routes.py')
from flask_sqlalchemy import SQLAlchemy  # Import SQLAlchemy for database integration
from db_config import init_db  # Import the function to initialize the database (assumed to be in 'db_config.py')
from flask_jwt_extended import JWTManager  # Import JWTManager for handling JWT authentication

# Initialize the Flask app
app = Flask(__name__, static_folder='static/skyway_frontend/browser', static_url_path='/static')

# Initialize the database with the app configuration
init_db(app)

# Enable Cross-Origin Resource Sharing (CORS) for the app
CORS(app)

# Set up the JWT Manager for handling JWT-based authentication
jwt = JWTManager(app)

# Set up the secret keys for JWT and Flask (use environment variables for production)
app.config['JWT_SECRET_KEY'] = 'your-jwt-secret-key'  # Secret key for JWT token signing
app.config['SECRET_KEY'] = 'your-flask-secret-key'  # Secret key for Flask session management

# Register the blueprint for API routes (grouping routes into a separate file for better organization)
app.register_blueprint(bp, url_prefix='/api')  # Prefix all routes defined in 'bp' with '/api'


# Define the base route to serve the Angular app's 'index.csr.html'
@app.route('/')
def serve_index():
    """
    Serve the Angular app's index page for the base route.
    """
    return send_from_directory(app.static_folder, 'index.csr.html')


# Catch all non-API routes and redirect them to Angular's 'index.csr.html'
@app.route('/<path:path>')  # Catch all routes except API ones
def serve_path(path=None):
    """
    Serve the Angular index page for any path that doesn't match API routes.
    Excludes API paths and serves 'index.csr.html' for others like '/sw/*'.
    """
    if path and path.startswith('api/'):  # Exclude API paths from being handled here
        return "Not found", 404  # Return 404 for API routes
    if path and path.startswith('sw/'):  # Handle special path pattern like '/sw/*'
        return send_from_directory(app.static_folder, 'index.csr.html')
    return send_from_directory(app.static_folder, path)  # Serve static files for other paths


# Serve static files from the 'static' folder, excluding API paths
@app.route('/static/<path:path>')
def serve_static(path):
    """
    Serve static files (images, JS, CSS, etc.) from the 'static' folder.
    """
    return send_from_directory(app.static_folder, path)  # Returns requested file from static folder


# Run the Flask app in debug mode for development purposes
if __name__ == '__main__':
    app.run(debug=True)
