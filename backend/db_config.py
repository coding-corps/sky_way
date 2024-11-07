from seed_data import seed_data  # Import seed data function to populate the database
from models import db  # Import the db object from your models
from flask import current_app


def init_db(flask_app):
    """
    Initialize the database for the Flask application.

    This function:
        - Configures the SQLAlchemy URI to use SQLite for the database.
        - Initializes the database with the Flask app.
        - Creates all tables defined in the models.
        - Calls a seed function to populate the database with initial data.

    Args:
        flask_app (Flask): The Flask application instance.

    Logs:
        - Any errors encountered during the database initialization.
    """
    try:
        # Set the URI for SQLite database
        flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skyway_airlines_systems.db'

        # Disable the modification tracking feature (to save resources)
        flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        # Initialize the database with the Flask app
        db.init_app(flask_app)

        # Create all tables defined by models
        with flask_app.app_context():
            # db.drop_all()  # Optional: Uncomment to drop all tables before creating them (use with caution)
            db.create_all()  # Create all tables defined by your models

            # Populate the database with seed data
            seed_data()

        current_app.logger.info("Database initialized and seeded successfully.")

    except Exception as e:
        current_app.logger.error(f"Error during database initialization: {str(e)}")
        raise e  # Re-raise the exception after logging it
