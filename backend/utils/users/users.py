from datetime import datetime
from flask import current_app, jsonify
from your_app.models import User  # Replace 'your_app' with the actual name of your app module
from sqlalchemy.exc import SQLAlchemyError  # For database-related exceptions
from sqlalchemy.orm.exc import NoResultFound  # Specific exception for no results
from models import db


def get_user_by_id(user_id):
    """
    Retrieve a user by their ID from the database.

    Args:
        user_id (int): The ID of the user to retrieve.

    Returns:
        User or None:
            - A `User` object if found.
            - `None` if the user does not exist or an error occurs.

    Logs:
        - Error messages if the user is not found or if an exception is raised.

    Raises:
        SQLAlchemyError: For database-related errors.
        Exception: For unexpected errors.
    """
    try:
        # Attempt to retrieve the user by ID
        user = User.query.get(user_id)

        # If no user is found, log an error and return None
        if not user:
            current_app.logger.error(f"User with ID {user_id} not found")
            return None

        # Return the user object if found
        return user

    except SQLAlchemyError as e:
        # Log database-specific errors
        current_app.logger.error(f"Database error fetching user by ID {user_id}: {str(e)}")
        return None

    except Exception as e:
        # Log any unexpected errors
        current_app.logger.error(f"Unexpected error fetching user by ID {user_id}: {str(e)}")
        return None


def get_user_by_email(email):
    """
    Retrieve a user by their email address from the database.

    Args:
        email (str): The email address of the user to retrieve.

    Returns:
        User or None:
            - A `User` object if found.
            - `None` if the user does not exist or an error occurs.

    Logs:
        - Error messages if no user is found or an exception is raised.

    Raises:
        SQLAlchemyError: For database-related errors.
        NoResultFound: When no user matches the given email.
    """
    try:
        # Attempt to retrieve the user by email
        user = User.query.filter_by(email=email).first()

        # If no user is found, log an error and return None
        if user is None:
            current_app.logger.error(f"User with email {email} not found")
            return None

        # Return the user object if found
        return user

    except NoResultFound:
        # Log the case where no user matches the query
        current_app.logger.error(f"No result found for email {email}")
        return None

    except SQLAlchemyError as e:
        # Log any database-related errors
        current_app.logger.error(f"Database error fetching user by email {email}: {str(e)}")
        return None

    except Exception as e:
        # Log any unexpected errors
        current_app.logger.error(f"Unexpected error fetching user by email {email}: {str(e)}")
        return None


def create_user(first_name, last_name, gender, email, password):
    """
    Create a new user in the system.

    Args:
        first_name (str): The first name of the user.
        last_name (str): The last name of the user.
        gender (str): The gender of the user (e.g., 'Male', 'Female', 'Other').
        email (str): The email address of the user.
        password (str): The plain-text password of the user.

    Returns:
        User or None:
            - A `User` object if creation is successful.
            - `None` if an error occurs or the email is already in use.

    Logs:
        - Error messages if user creation fails or an exception is raised.

    Raises:
        SQLAlchemyError: For database-related errors.
        Exception: For unexpected errors.
    """
    try:
        # Check if email is already in use
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            current_app.logger.error(f"Email {email} is already in use.")
            return None  # Return None or raise an exception for existing email

        # Create a new user instance
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            email=email
        )

        # Set the user's password using a hashing method
        new_user.set_password(password)

        # Add the new user to the database session
        db.session.add(new_user)
        db.session.commit()  # Commit the transaction to save the new user

        current_app.logger.info(f"User {email} created successfully.")
        return new_user  # Return the created user object

    except SQLAlchemyError as e:
        # Rollback the session if a database error occurs
        db.session.rollback()
        current_app.logger.error(f"Database error during user creation: {str(e)}")
        return None

    except Exception as e:
        # Rollback the session and log any unexpected errors
        db.session.rollback()
        current_app.logger.error(f"Unexpected error during user creation: {str(e)}")
        return None


def delete_user(user_id):
    """
    Soft delete a user by setting the 'deleted_at' field to the current time.

    Args:
        user_id (int): The ID of the user to delete.

    Returns:
        User or None:
            - The updated `User` object if the deletion is successful.
            - `None` if the user does not exist or an error occurs.

    Logs:
        - Error messages if the user is not found or if an exception is raised.

    Raises:
        SQLAlchemyError: For database-related errors.
        Exception: For unexpected errors.
    """
    try:
        # Attempt to find the user with the given ID and ensure they aren't already deleted
        user = User.query.filter_by(id=user_id, deleted_at=None).first()

        if user is None:
            current_app.logger.error(f"User with ID {user_id} not found or already deleted.")
            return None  # Return None or raise an exception if preferred

        # Mark the user as deleted by setting the 'deleted_at' field to the current time
        user.deleted_at = datetime.utcnow()

        # Commit the change to the database
        db.session.commit()
        current_app.logger.info(f"User with ID {user_id} successfully soft-deleted.")

        return user  # Return the updated user object

    except SQLAlchemyError as e:
        # Rollback the session in case of a database error
        db.session.rollback()
        current_app.logger.error(f"Database error during soft deletion of user ID {user_id}: {str(e)}")
        return None

    except Exception as e:
        # Rollback the session and log any unexpected errors
        db.session.rollback()
        current_app.logger.error(f"Unexpected error during soft deletion of user ID {user_id}: {str(e)}")
        return None


def update_user(user_id, first_name=None, last_name=None, gender=None, email=None, password=None):
    """
    Update a user's information in the database.

    Args:
        user_id (int): The ID of the user to update.
        first_name (str, optional): New first name for the user.
        last_name (str, optional): New last name for the user.
        gender (str, optional): New gender for the user (e.g., 'Male', 'Female', 'Other').
        email (str, optional): New email address for the user.
        password (str, optional): New plain-text password for the user.

    Returns:
        User or None:
            - The updated `User` object if the update is successful.
            - `None` if the user does not exist or an error occurs.

    Logs:
        - Error messages if the user is not found or if an exception is raised.

    Raises:
        SQLAlchemyError: For database-related errors.
        Exception: For unexpected errors.
    """
    try:
        # Find the user by ID, ensuring the user is not soft-deleted
        user = User.query.filter_by(id=user_id, deleted_at=None).first()

        if user is None:
            current_app.logger.error(f"User with ID {user_id} not found or already deleted.")
            return None  # Return None or raise an exception if preferred

        # Update fields if new values are provided
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if gender:
            user.gender = gender
        if email:
            user.email = email
        if password:
            user.set_password(password)  # Update the user's password securely

        # Commit the changes to the database
        db.session.commit()
        current_app.logger.info(f"User with ID {user_id} successfully updated.")

        return user  # Return the updated user object

    except SQLAlchemyError as e:
        # Rollback the session if a database error occurs
        db.session.rollback()
        current_app.logger.error(f"Database error during update of user ID {user_id}: {str(e)}")
        return None

    except Exception as e:
        # Rollback the session and log any unexpected errors
        db.session.rollback()
        current_app.logger.error(f"Unexpected error during update of user ID {user_id}: {str(e)}")
        return None
