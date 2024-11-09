import itertools
import json
import os
import random
import uuid
from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy.exc import IntegrityError

from models import db, Flight, Airport  # Ensure you have imported your models


def load_airports_from_json(json_file_path):
    """
    Load airport data from a JSON file.

    This function reads a JSON file containing airport information and loads it into
    a Python dictionary.

    Args:
        json_file_path (str): The relative or absolute path to the JSON file containing airport data.

    Returns:
        dict: A dictionary containing the parsed airport data.

    Raises:
        FileNotFoundError: If the JSON file cannot be found at the given path.
        JSONDecodeError: If the file is not a valid JSON document.
    """
    try:
        # Ensure the correct relative path is used for the JSON file
        json_file_path = os.path.join(os.path.dirname(__file__), 'data', 'airports.json')

        # Open the JSON file for reading
        with open(json_file_path, 'r') as f:
            data = json.load(f)  # Parse the JSON data into a Python dictionary

        return data  # Return the parsed data from the JSON file

    except FileNotFoundError as e:
        # Log error if the file is not found
        current_app.logger.error(f"File not found: {json_file_path}")
        raise e

    except json.JSONDecodeError as e:
        # Log error if the file content is not valid JSON
        current_app.logger.error(f"Invalid JSON format in file: {json_file_path}")
        raise e


def seed_data():
    """
    Seed the database with initial data.

    This function:
        - Loads airport data from a JSON file.
        - Inserts the airport data into the database.
        - Retrieves the list of airports from the database.
        - Adds flight data for each airport into the database.

    Logs:
        - Errors if loading data or inserting records fails.
    """
    try:
        # Load airport data from the JSON file
        airports_data = load_airports_from_json('airports.json')

        # Insert the airport data into the database
        create_airports(airports_data)

        # Retrieve all airports from the database
        airports = Airport.query.all()

        # Add flight data for each airport to the database
        add_flight_data_to_db(airports)

        current_app.logger.info("Database seeded successfully with airport and flight data.")

    except Exception as e:
        current_app.logger.error(f"Error while seeding database: {str(e)}")
        raise e  # Re-raise the exception after logging it


def create_airports(entries):
    """
    Function to insert airport entries into the database.

    This function iterates over a list of dictionaries containing airport data and inserts each entry
    into the database. It handles integrity errors, such as duplicate airport codes, and commits the
    changes to the database.

    Args:
        entries (list of dict): A list of dictionaries where each dictionary contains the airport's
                                 'code' and 'name' to be inserted into the database.

    Returns:
        None

    Logs:
        - Errors encountered during insertion or commit operations.
    """
    for airport in entries:
        try:
            # Create a new Airport object for each entry
            new_airport = Airport(code=airport['code'], name=airport['name'])

            # Add the new airport object to the session for insertion into the database
            db.session.add(new_airport)

        except IntegrityError as e:
            # Handle cases where the airport code already exists in the database
            print(f"Error inserting airport with code {airport['code']}: {e.orig}")
            db.session.rollback()  # Rollback the session in case of integrity error

    try:
        # Commit all entries to the database after processing the list
        db.session.commit()
        print(f"Successfully inserted {len(entries)} airports into the database.")

    except Exception as e:
        # Rollback in case of any errors during the commit
        db.session.rollback()
        print(f"Error committing to the database: {e}")


def add_flight_data_to_db(airports):
    """
    Generate and insert flight data for all unique combinations of airports.

    This function generates flight details such as flight number, departure and arrival times,
    flight duration, start and end dates for flights between all airport pairs. It adds these
    flight records to the database.

    Args:
        airports (list): A list of airport records from the database, each containing 'id' and 'code'.

    Returns:
        None

    Logs:
        - Prints success or failure messages for flight insertion.
    """
    flight_num_counter = random.randint(100, 900)  # Starting flight number (BW101)

    # Generate all unique airport code pairs using permutations (from_airport -> to_airport)
    airport_pairs = list(itertools.permutations(airports, 2))

    for from_airport, to_airport in airport_pairs:
        # Generate a random departure time between 6:00 AM and 9:00 PM
        random_hour = random.randint(6, 21)  # Random hour between 6 AM and 9 PM
        random_minute = random.randint(0, 59)  # Random minute between 0 and 59

        # Adjust time format to 12-hour AM/PM (e.g., 6 AM or 6 PM)
        if random_hour == 12:
            hour_12 = 12
            am_pm = 'PM'
        elif random_hour > 12:
            hour_12 = random_hour - 12
            am_pm = 'PM'
        else:
            hour_12 = random_hour
            am_pm = 'AM'

        # Construct the time string (e.g., '06:45 AM')
        departure_time_str = f"{hour_12:02d}:{random_minute:02d} {am_pm}"

        # Convert to a datetime object using 12-hour format
        try:
            departure_time = datetime.strptime(str(departure_time_str)[:10], "%I:%M %p")
        except ValueError as ve:
            # Handle invalid time format and skip this flight
            print(f"Error parsing time '{departure_time_str}': {ve}")
            continue  # Skip to the next flight if there's an error in time format

        # Generate a random flight duration between 55 minutes and 3 hours
        flight_duration_minutes = random.randint(55, 180)  # Random duration in minutes
        flight_duration = timedelta(minutes=flight_duration_minutes)

        # Calculate arrival time by adding flight duration to departure time
        arrival_time = departure_time + flight_duration

        # Generate a random start date (1 to 365 days from today)
        today = datetime.utcnow()
        random_days_ahead = random.randint(1, 365)  # Random number of days in the future
        start_date = today + timedelta(days=random_days_ahead)

        # Ensure that the end date is after the start date (1 to 2 days after)
        added_days = random.randint(1, 2)
        if arrival_time < departure_time and added_days < 1:
            added_days = 1  # Ensure at least 1 day gap between start and end date

        end_date = start_date + timedelta(days=added_days)  # Random end date (1 to 2 days after start)
        id = str(uuid.uuid4())
        # Create a new Flight entry
        new_flight = Flight(
            id=id,  # Generate a unique UUID for the flight
            flight_num=f"SKY-{id}",  # Flight number in the format BW101, BW102, etc.
            departure_airport_id=from_airport.id,  # From airport ID
            arrival_airport_id=to_airport.id,     # To airport ID
            departure_time=departure_time.strftime("%I:%M %p"),  # Format as 12-hour time (AM/PM)
            arrival_time=arrival_time.strftime("%I:%M %p"),
            start_date=start_date,
            end_date=end_date,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Add the new flight object to the session for insertion
        db.session.add(new_flight)
        flight_num_counter += 1  # Increment the flight number for the next flight

    try:
        # Commit all the generated flight records to the database
        db.session.commit()
        print(f"Successfully inserted {flight_num_counter - 101} flights into the database.")

    except Exception as e:
        # Rollback the session if there's an error during commit
        db.session.rollback()
        print(f"Error committing flights to the database: {e}")