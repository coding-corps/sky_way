# routes.py
from flask import Blueprint, request, jsonify, current_app, abort
from models import db, Flight, User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import uuid
import random
from datetime import datetime, timedelta  # Add timedelta for time manipulation
from utils.flights.flights import get_close_flights, get_flight_by_id, save_searched_flight
from utils.flights.airports import get_all_airports
from utils.bookings.booking import pay_booking, create_booking_entry, get_booking
from models import SearchHistory

bp = Blueprint('routes', __name__)


###################################################
# Login
@bp.route('/login', methods=['POST'])
def login():
    """
    Handle the login process for users.
    Verifies user credentials (email and password) and returns a JWT access token upon successful login.
    """
    # Log the start of the login process for debugging purposes
    current_app.logger.debug("Starting login process")

    # Get the JSON data from the request
    data = request.json

    # Check if the required fields ('email' and 'password') are present in the request data
    if not data or 'email' not in data or 'password' not in data:
        # Log an error and return a 400 response if either 'email' or 'password' is missing
        current_app.logger.error("Username or password are missing")
        abort(400, description="Email and password are required.")  # Abort with a 400 error

    # Extract email and password from the request data
    email = data['email']
    password = data['password']

    # Query the User model to find a user with the given email
    user = User.query.filter_by(email=email).first()

    # If no user is found, return a 404 response with an error message
    if not user:
        current_app.logger.error("User not found")
        return jsonify({"message": "User not found"}), 404

    # Verify if the provided password matches the stored hashed password
    if user.verify_password(password):
        # Create a JWT access token for the authenticated user
        access_token = create_access_token(identity=user.id)

        # Prepare a response with a success message and the generated access token
        response = jsonify({"message": "Login successful.", "access_token": f'{access_token}'})

        # Set the JWT token in the response header for future requests
        response.headers['Authorization'] = f'Bearer {access_token}'

        # Return the response with a 200 status code (OK)
        return response, 200
    else:
        # Return a 401 response if the password is incorrect
        return jsonify({"message": "Invalid login credentials."}), 401


# Create User API
@bp.route('/register', methods=['POST'])
def create_user():
    """
    Handles user registration by accepting a name, email, and password.
    Creates a new user, hashes the password, and stores the user in the database.
    """
    # Get the JSON data from the request
    data = request.json

    # Extract name, email, and password from the request data
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    # Check if any required fields (name, email, password) are missing
    if not name or not email or not password:
        # Abort the request and return a 400 error if any field is missing
        abort(400, description="Name, email, and password are required.")

    # Split the name into first name and last name
    # If the name doesn't contain a space, it will assign None to last_name
    first_name, last_name = (name.split(' ', 1) + [None])[:2]  # Split on the first space only

    # Check if a user with the provided email already exists in the database
    if User.query.filter_by(email=email).first():
        # Return a 409 (Conflict) error if a user with this email is found
        return jsonify({"message": "User with this email already exists."}), 409

    # Create a new user instance with the provided details
    new_user = User(first_name=first_name, last_name=last_name, email=email)

    # Set the user's password after hashing it
    new_user.set_password(password)

    # Add the new user to the database session
    db.session.add(new_user)

    # Commit the changes to the database, saving the new user
    db.session.commit()

    # Return a success message and the new user's ID as part of the response
    return jsonify({"message": "User created successfully.", "user_id": str(new_user.id)}), 201


# Get User API - Retrieves a user's information based on their user ID
@bp.route('/get_user/<user_id>', methods=['GET'])
@jwt_required()  # Requires JWT authentication to access this route
def get_user(user_id):
    """
    Retrieves the user details for the given user ID. This route is protected
    and can only be accessed by the user who owns the account or an authorized user.
    The request requires a valid JWT token for authentication.
    """
    # Get the current user's ID from the JWT token
    current_user_id = get_jwt_identity()

    # Check if the user making the request is trying to access their own data
    # If the user is not authorized (i.e., user_id does not match current_user_id)
    if str(current_user_id) != user_id:
        # Return a 403 Forbidden response if the user is not authorized
        return jsonify({"message": "Unauthorized access."}), 403

    # Query the database for the user based on the user_id
    user = User.query.get(user_id)

    # If the user is not found, return a 404 Not Found error
    if not user:
        return jsonify({"message": "User not found."}), 404

    # If the user is found, return the user data as a JSON response
    return jsonify({
        "first_name": user.first_name,
        "last_name": user.last_name,
        "gender": user.gender,
        "email": user.email,
        "dob": user.dob,
        "created_at": user.created_at,
    }), 200


###################################################

@bp.route('/airports', methods=['GET'])
def get_airports():
    """
    Fetches a list of all airports.

    This endpoint returns all available airports in the system. The function delegates the
    fetching of airport data to a separate function (`get_all_airports`).

    - Returns a list of all airports in JSON format.
    - Can be accessed via a GET request.
    """
    # Call the function to fetch all airports and return the result as a JSON response
    return jsonify(get_all_airports())  # Return the list of airports in JSON format


###################################################
# Search Flights API - Retrieves available flights based on search parameters
@bp.route('/search_flights', methods=['GET'])
@jwt_required()  # Requires JWT authentication to access this route
def search_flights():
    """
    Handles a flight search request. It retrieves the available outgoing and returning flights
    based on the provided search parameters (departure city, arrival city, departure date, etc.).
    The request requires a valid JWT token for authentication.
    """
    # Retrieve search parameters from query string
    departure_city = request.args.get('from')  # Departure city (from)
    arrival_city = request.args.get('to')  # Arrival city (to)
    departure_date = request.args.get('depart')  # Departure date
    return_date = request.args.get('return')  # Return date (optional, for round trips)
    trip_type = request.args.get('type')  # Trip type (e.g., "Roundtrip" or "One-way")
    guests = request.args.get('guests')  # Number of guests (optional)

    # Log the search request for debugging or tracking purposes
    current_app.logger.info(
        f"Search request: {departure_city}, {arrival_city}, {departure_date}, {return_date}, {trip_type}, {guests}")

    try:
        # Fetch the available outgoing flights based on the search parameters
        outgoing_flights, error_msg, err_code = get_close_flights(
            destination_airport=arrival_city,
            departure_airport=departure_city,
            departure_date=departure_date
        )

        # If there is an error fetching outgoing flights, return the error message and code
        if error_msg:
            return error_msg, err_code

        returning_flights = []
        # If the trip is roundtrip, fetch the returning flights as well
        if trip_type == "Roundtrip":
            returning_flights, error_msg, err_code = get_close_flights(
                destination_airport=departure_city,
                departure_airport=arrival_city,
                departure_date=return_date
            )
            # If there is an error fetching returning flights, return the error message and code
            if error_msg:
                return error_msg, err_code

        # Prepare the response data with the outgoing and returning flights
        response_data = {
            'outgoing_flights': [flight.to_dict() for flight in outgoing_flights],
            # Convert flight objects to dictionaries
            'returning_flights': [flight.to_dict() for flight in returning_flights] if trip_type == "Roundtrip" else []
            # Only include returning flights for roundtrips
        }

        # Return the search results as a JSON response
        return jsonify(response_data)

    except Exception as e:
        # Log any exception that occurs during the search process
        current_app.logger.error(f"Error processing flight search: {str(e)}")

        # Return a 500 Internal Server Error if an exception occurs
        return jsonify({"error": "Error processing flight search"}), 500


@bp.route('/add_to_search_history/<flight_id>', methods=['POST'])
@jwt_required()  # Requires JWT authentication to access this route
def add_to_search_history(flight_id):
    """
    Adds a flight to the search history of the authenticated user.
    This will create a new entry in the SearchHistory table if it doesn't exist
    or increment the search count if the user has already searched for this flight.
    """
    # Get the user ID from the JWT token
    user_id = get_jwt_identity()

    # Retrieve the user and flight objects from the database
    user = User.query.get(user_id)
    flight = Flight.query.get(flight_id)

    # Check if both the user and the flight exist
    if not user:
        return jsonify({"message": "User not found."}), 404
    if not flight:
        return jsonify({"message": "Flight not found."}), 404

    # Check if the flight has already been searched by the user
    return save_searched_flight(user_id, flight_id)


###################################################

# Create Booking API
@bp.route('/booking', methods=['POST'])
@jwt_required()
def create_booking():
    """
    Creates a new booking entry for the authenticated user.
    This function processes the booking details provided by the user, including flight information
    and passengers, and generates a booking record.

    - Validates required data from the request.
    - Retrieves flight details and creates a new return flight if necessary.
    - Calls the `create_booking_entry` helper function to create the booking record.
    - Returns a JSON response with the booking details or an error message.
    """
    # Extract data from the incoming JSON request
    data = request.json

    # Get the authenticated user's ID from the JWT token
    owner_id = get_jwt_identity()

    # Get the departing flight details from the request body
    departing_flight = data.get('departing_flight')
    return_date = data.get('return_date')  # Optional field for round-trip bookings
    passengers = data.get('passengers', [])  # List of passengers for the booking

    # Validate that the required fields (owner_id and departing_flight) are present
    if not owner_id or not departing_flight:
        return jsonify({"error": "Owner ID and Departure Flight ID are required"}), 400

    # Fetch the departure flight object from the database using the provided flight ID
    departure_flight = get_flight_by_id(departing_flight['flight_id'])
    if not departure_flight:
        return jsonify({"error": "Invalid Departure Flight ID"}), 400

    # Handle round-trip bookings by checking if a return date is provided
    returning_flight = None
    if return_date:
        # Convert the return date from string to a date object
        return_date_obj = datetime.strptime(return_date, "%Y-%m-%d").date()

        # Attempt to find available return flights for the user
        returning_flights, error_msg, err_code = get_close_flights(
            destination_airport=departure_flight.departure_airport.code,
            departure_airport=departure_flight.arrival_airport.code,
            departure_date=return_date
        )

        # If returning flights exist, select the first one as the return flight
        if returning_flights:
            returning_flight = returning_flights[0]
            print("Found returning flight:", returning_flights)
        else:
            print("No returning flight found, creating a new one.")
            # Create a new return flight if no matching flights are found

            # Create a new Flight object for the return flight
            new_flight = Flight(
                id=str(uuid.uuid4()),  # Generate a unique ID for the new flight
                flight_num=f"RF{random.randint(101, 505)}",  # Random flight number for return flight
                departure_airport_id=departure_flight.arrival_airport.id,
                arrival_airport_id=departure_flight.departure_airport.id,
                departure_time=(datetime.combine(return_date_obj, datetime.min.time()) + timedelta(hours=1)),
                arrival_time=(datetime.combine(return_date_obj, datetime.min.time()) + timedelta(hours=3)),
                start_date=return_date_obj,
                end_date=(return_date_obj + timedelta(days=1)),  # End date is one day after departure
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Add the new flight to the database session
            db.session.add(new_flight)
            db.session.commit()  # Commit to save the new flight to the database
            db.session.flush()  # Ensure the session is updated

            # Set the created return flight as the returning flight
            returning_flight = new_flight

    # Create the booking entry by calling the helper function
    booking = create_booking_entry(
        owner_id=owner_id,  # The authenticated user as the owner of the booking
        departure_flight=departure_flight.id,  # Departure flight ID
        returning_flight=returning_flight.id if returning_flight else None,  # Optional return flight ID
        passengers=passengers  # List of passengers for the booking
    )

    # If the booking creation returned an error, return the error response
    if isinstance(booking, dict) and "error" in booking:
        return jsonify(booking), 400

    # Return the booking details in a JSON response
    return jsonify(booking.to_dict()), 201


# View Bookings API
@bp.route('/booking', methods=['GET'])
@jwt_required()
def view_bookings():
    """
    Retrieves a list of bookings for a user, either by email or reference number.
    This function handles both queries and returns the matching bookings in a JSON response.

    - Either an email or reference number must be provided.
    - If email is provided, it fetches all bookings for the associated user.
    - If reference number is provided, it fetches the specific booking matching the reference.
    - Returns a list of bookings in JSON format, or an error message if no bookings are found.
    """
    # Retrieve email and reference number from the query parameters
    email = request.args.get('email')
    reference_number = request.args.get('reference_number')

    # Validate that at least one of the parameters (email or reference number) is provided
    if not email and not reference_number:
        return jsonify({"error": "Email or Reference Number must be provided"}), 400

    bookings = []  # List to store the bookings that match the search criteria

    # If email is provided, fetch the user and their associated bookings
    if email:
        user = User.query.filter_by(email=email).first()  # Find the user by email
        if not user:
            return jsonify({"error": "User not found"}), 404  # Return an error if the user is not found
        bookings = user.bookings  # Retrieve all bookings for the user

    # If reference number is provided, fetch the specific booking by reference number
    if reference_number:
        booking = get_booking(None, reference_number=reference_number)  # Retrieve the booking by reference number
        if booking:
            bookings.append(booking)  # Add the booking to the list

    # Return the list of bookings in JSON format
    return jsonify([booking.to_dict() for booking in bookings]), 200


@bp.route('/booking/confirmation', methods=['POST'])
@jwt_required()
def pay_for_booking():
    """
    Handles the payment confirmation for a booking.

    This endpoint is used to confirm the payment for a booking by providing the booking ID.
    The function expects the `booking_id` in the request JSON body. Upon successful validation,
    it proceeds to the payment handling logic.

    - Requires JWT authentication.
    - A `booking_id` is required in the request body.
    - If the `booking_id` is valid, the payment for the booking is processed.
    - Returns the result of the payment processing or an error if no `booking_id` is provided.
    """
    # Retrieve the booking_id from the request JSON
    data = request.json
    booking_id = data.get('booking_id')

    # Validate if the booking_id is provided in the request body
    if not booking_id:
        return jsonify({"error": "Booking ID is required"}), 400  # Return an error if booking_id is missing

    # Call the external payment handler function to process the payment for the booking
    return pay_booking(booking_id)  # Return the result of the payment processing


###################################################
