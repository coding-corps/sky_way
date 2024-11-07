from datetime import datetime
from sqlalchemy.exc import IntegrityError
from utils.users.users import get_user_by_email
from models import Booking, db, User
import uuid
from flask import jsonify


def create_booking_entry(owner_id, departure_flight, returning_flight=None, passengers=[]):
    """
    Creates a new booking for a user, associates flights, and passengers.

    :param owner_id: ID of the user making the booking.
    :param departure_flight: ID of the departure flight.
    :param returning_flight: ID of the returning flight (nullable for one-way).
    :param passengers: List of user data dictionaries for passengers (can be empty for just the owner).
    :return: Newly created booking object or an error message.
    """

    try:
        # Create a new booking instance
        booking = Booking(
            reference_number=str(generate_reference_number()),  # Generate a reference number (implement as needed)
            owner_id=owner_id,  # Should be a user ID (e.g., integer or UUID)
            departure_flight_id=departure_flight,
            returning_flight_id=returning_flight,
            created_at=datetime.utcnow(),
        )

        # Process each passenger in the list
        for passenger in passengers:
            email = passenger.get("email")
            if email:
                # Check if the passenger already exists
                existing_passenger = get_user_by_email(email)
                if existing_passenger:
                    booking.passengers.append(existing_passenger)
                else:

                    dob_str = passenger.get("dob")
                    dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None

                    # If passenger does not exist, create a new user
                    new_user = User(
                        email=email,
                        first_name=passenger.get("first_name"),
                        last_name=passenger.get("last_name"),
                        gender=passenger.get("gender"),
                        dob=dob,
                    )
                    db.session.add(new_user)
                    db.session.flush()  # Ensure new_user ID is generated before associating
                    booking.passengers.append(new_user)

        # Add and commit the booking to the session
        db.session.add(booking)
        db.session.commit()

        return booking
    except IntegrityError as e:
        db.session.rollback()
        print(f"IntegrityError: {e}")
        return {"error": "Booking creation failed due to integrity error."}
    except Exception as e:
        db.session.rollback()
        print(f"Unexpected error: {e}")
        return {"error": "An unexpected error occurred during booking creation."}


def update_booking(booking_id, departure_flight_id=None, returning_flight_id=None, passengers=[]):
    """
    Update an existing booking by changing the flight or adding/removing passengers.

    :param booking_id: ID of the booking to be updated.
    :param departure_flight_id: New departure flight ID (nullable).
    :param returning_flight_id: New returning flight ID (nullable).
    :param passengers: List of user IDs for passengers to be added/removed.
    :return: Updated booking object or an error message.
    """
    booking = Booking.query.get(booking_id)
    if not booking:
        return {"error": "Booking not found."}

    if departure_flight_id:
        booking.departure_flight_id = departure_flight_id
    if returning_flight_id is not None:
        booking.returning_flight_id = returning_flight_id

    # Update passengers list
    for passenger_id in passengers:
        user = User.query.get(passenger_id)
        if user and user not in booking.passengers:
            booking.passengers.append(user)

    db.session.commit()
    return booking


def pay_booking(booking_id):
    """
    Process payment for a booking and mark it as completed.

    :param booking_id: ID of the booking being paid for.
    :return: Booking object with payment processed or an error message.
    """
    booking = Booking.query.get(booking_id)
    if not booking:
        return {"error": "Booking not found."}, 404

    if booking.payment_received:
        return {"error": "This booking has already been paid for."}, 409

    # Process the payment here (e.g., integrate with payment gateway)
    booking.payment_received = datetime.utcnow()
    booking.completed = datetime.utcnow()

    db.session.commit()
    return jsonify({
        'reference_number': booking.reference_number,
        'status': 'Paid',
        'payment_received': booking.payment_received
    }), 200


def get_booking(booking_id=None, reference_number=None):
    """
    Retrieve a booking by its ID or reference number.

    :param booking_id: ID of the booking.
    :param reference_number: Reference number of the booking (nullable).
    :return: Booking object or an error message.
    """
    if booking_id:
        booking = Booking.query.get(booking_id)
        if booking:
            return booking
    elif reference_number:
        booking = Booking.query.filter_by(reference_number=reference_number).first()
        if booking:
            return booking

    return {"error": "Booking not found."}


def generate_reference_number():
    return f"SKY-{uuid.uuid4()}"
