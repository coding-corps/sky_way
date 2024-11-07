from flask import jsonify, current_app
from datetime import datetime, timedelta
from models import Flight, Airport, SearchHistory, db
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


def get_flight_by_id(flight_id):
    """
    Given a flight ID, return the flight object if it exists, or raise an error if not found.
    """
    flight = Flight.query.filter_by(id=flight_id).first()
    if not flight:
        return jsonify({"error": "Flight not found."}), 404
    return flight


def save_searched_flight(user_id, flight_id):
    """
    Save or update the search history for a user and a flight.
    If the user searches the same flight again, increment the search count.
    """
    try:
        # Attempt to fetch an existing search history record
        existing_search = SearchHistory.query.filter_by(user_id=user_id, flight_id=flight_id).first()

        if existing_search:
            # If the search exists, increment the search count
            existing_search.search_count += 1
        else:
            # If it doesn't exist, create a new search history record
            existing_search = SearchHistory(user_id=user_id, flight_id=flight_id)
            db.session.add(existing_search)

        # Commit the changes once, reducing multiple commit calls
        db.session.commit()

        # Return the updated or newly created search history record
        return jsonify(existing_search.to_dict()), 200

    except IntegrityError as e:
        db.session.rollback()
        current_app.logging.error(f"IntegrityError while saving search history for user {user_id} and flight {flight_id}: {e}")
        return jsonify({"error": "An integrity error occurred while saving search history."}), 500
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logging.error(f"SQLAlchemyError while saving search history for user {user_id} and flight {flight_id}: {e}")
        return jsonify({"error": "A database error occurred while saving search history."}), 500
    except Exception as e:
        current_app.logging.error(f"Unexpected error while saving search history for user {user_id} and flight {flight_id}: {e}")
        return jsonify({"error": "An unexpected error occurred while saving search history."}), 500


def get_close_flights(destination_airport=None, departure_airport=None, departure_date=None):
    """
    Get flights based on destination, departure airport, and date range.
    Searches for flights on the exact date first, then searches ±3 days if no flights are found.
    """
    if departure_date is None:
        return jsonify({"error": "Departure date is required."}), 400

    # Initial search for the exact departure date
    flights = get_all_flights(destination_airport, departure_airport, departure_date, departure_date)

    if flights:
        return jsonify([flight.to_dict() for flight in flights]), 200
    else:
        # Set the range for "close" dates (e.g., ±3 days)
        date_range_days = 3

        # Parse the departure date and calculate the date range
        try:
            departure_date_obj = datetime.strptime(departure_date, '%Y-%m-%d')
            start_date = departure_date_obj - timedelta(days=date_range_days)
            end_date = departure_date_obj + timedelta(days=date_range_days)
        except ValueError:
            return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400

        # Search for flights within the date range
        flights = get_all_flights(destination_airport, departure_airport, start_date, end_date)

        if flights:
            return jsonify([flight.to_dict() for flight in flights]), 200
        return jsonify({"message": "No flights found close to the specified date."}), 404


def get_all_flights(to=None, from_airport=None, start_date=None, end_date=None):
    """
    Get a list of flights with optional filters.
    Filters are:
    - to: destination airport code (optional)
    - from_airport: departure airport code (optional)
    - start_date: start date for the flight (these are for searching flights within a range)
    - end_date: end date for the flight (these are for searching flights within a range)

    Returns a filtered list of flights based on the provided parameters.
    """
    query = Flight.query

    # Filter by 'to' (arrival airport)
    if to:
        arrival_airport = Airport.query.filter(Airport.code == to).first()
        if not arrival_airport:
            return []  # Return empty if no arrival airport found
        query = query.filter(Flight.arrival_airport_id == arrival_airport.id)

    # Filter by 'from_airport' (departure airport)
    if from_airport:
        departure_airport = Airport.query.filter(Airport.code == from_airport).first()
        if not departure_airport:
            return []  # Return empty if no departure airport found
        query = query.filter(Flight.departure_airport_id == departure_airport.id)

    # Filter by 'start_date' and 'end_date'
    if start_date:
        query = query.filter(Flight.start_date >= start_date)
    if end_date:
        query = query.filter(Flight.start_date <= end_date)

    # Execute the query and return the result
    flights = query.all()
    return flights
