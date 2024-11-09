from datetime import datetime
import bcrypt
from flask_sqlalchemy import SQLAlchemy
import uuid

from flask import current_app

# Initialize SQLAlchemy instance
db = SQLAlchemy()


def default_uuid_generator():
    """
    Generate a unique identifier (UUID) for new entries.

    UUID (Universally Unique Identifier) is a 128-bit number used to uniquely identify data.
    This function uses Python's built-in uuid library to generate a random UUID.

    Returns:
        str: A string representation of the generated UUID.
    """
    return str(uuid.uuid4())  # Generate a random UUID and convert it to a string


class Airport(db.Model):
    __tablename__ = 'airports'  # Table name in the database

    # Define columns for the Airport table
    id = db.Column(db.String(36), primary_key=True,
                   default=default_uuid_generator)  # UUID primary key with default generator
    code = db.Column(db.String(3))  # 3-character airport code (e.g., 'BGI')
    name = db.Column(db.String, nullable=False)  # Full name of the airport (e.g., 'Barbados, Grantley Adams Int'l')

    arriving_flights = db.relationship(
        'Flight',
        back_populates='arrival_airport',
        lazy=True,
        foreign_keys='Flight.arrival_airport_id'
    )
    departing_flights = db.relationship(
        'Flight',
        back_populates='departure_airport',
        lazy=True,
        foreign_keys='Flight.departure_airport_id'
    )

    # String representation for debugging
    def __repr__(self):
        return f"Airport(code={self.code}, name={self.name})"

    def get_arriving_flights(self):
        """
        Get a list of all flights arriving at this airport.
        """
        return self.arriving_flights

    def get_departing_flights(self):
        """
        Get a list of all flights departing from this airport.
        """
        return self.departing_flights

    def to_dict(self):
        """
        Convert the Airport object to a dictionary for easy serialization.
        """
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code
        }

    # Another string representation for debugging
    def __repr__(self):
        return f'<Airport {self.code}: {self.name} >'


class Flight(db.Model):
    __tablename__ = 'flights'

    id = db.Column(db.String(36), primary_key=True, default=default_uuid_generator)  # UUID primary key
    flight_num = db.Column(db.String(10), unique=True, nullable=False)

    departure_airport_id = db.Column(db.String(36), db.ForeignKey('airports.id'),
                                     nullable=False)  # Foreign key adjusted to match UUID type
    arrival_airport_id = db.Column(db.String(36), db.ForeignKey('airports.id'),
                                   nullable=False)  # Foreign key adjusted to match UUID type

    departure_time = db.Column(db.String(10), nullable=False)  # Time stored in 12-hour format
    arrival_time = db.Column(db.String(10), nullable=False)  # Time stored in 12-hour format
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships to the Airport model

    departure_airport = db.relationship('Airport', foreign_keys=[departure_airport_id],
                                        back_populates='departing_flights')
    arrival_airport = db.relationship('Airport', foreign_keys=[arrival_airport_id], back_populates='arriving_flights')

    def duration(self):
        try:
            # Combine the start_date and departure_time into a single datetime object
            departure_datetime = datetime.combine(self.start_date,
                                                  datetime.strptime(self.departure_time, '%I:%M %p').time())
            arrival_datetime = datetime.combine(self.end_date, datetime.strptime(self.arrival_time, '%I:%M %p').time())

            # Calculate the duration of the flight in hours
            duration = (arrival_datetime - departure_datetime).total_seconds() / 3600  # duration in hours

            return round(duration, 1)  # Rounded to two decimal places, or use {:.2g} for significant figures


        except Exception as e:
            current_app.logger.error(e)
            arrival_time = datetime.strptime(str(self.arrival_time)[:10], "%Y-%m-%d %H:%M:%S")
            departure_time = datetime.strptime(str(self.departure_time)[:10], "%Y-%m-%d %H:%M:%S")

            # Calculate the difference between the two datetime objects
            time_difference = arrival_time - departure_time
            difference_in_hours = time_difference.total_seconds() / 3600

            return difference_in_hours

    def cost(self):
        try:
            # Calculate the cost (cost per hour = $180)
            cost = self.duration() * 47

            # Return the cost as a formatted string with a dollar sign
            return f'${cost:.2f}'

        except Exception as e:
            cost = 12 * 47
            return f'${cost:.2f}'

    def to_dict(self):
        return {
            'id': self.id,
            'flight_num': self.flight_num,
            'departure_airport': self.departure_airport.to_dict() if self.departure_airport else None,
            'arrival_airport': self.arrival_airport.to_dict() if self.arrival_airport else None,
            'departure_time': self.departure_time,
            'arrival_time': self.arrival_time,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'cost': self.cost(),
            'duration': self.duration(),
        }

    def __repr__(self):
        return f'<Flight {self.flight_num} from {self.departure_airport.name} to {self.arrival_airport.name}>'


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=default_uuid_generator)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    gender = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    dob = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Method to set hashed password
    def set_password(self, password):
        """
        Set the hashed password for the user.
        """
        if password:
            self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        else:
            raise ValueError("Password cannot be empty")

    # Method to verify password
    def verify_password(self, password):
        """
        Verify the password matches the hashed password.
        """
        if not self.password_hash:
            raise ValueError("Password hash not set")
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def full_name(self):
        """
        Get the full name of the user.
        """
        return f'{self.first_name} {self.last_name}'

    def get_bookings(self):
        """
        Retrieve all bookings associated with the user.
        """
        try:
            passenger_bookings = Booking.query.join(booking_passenger).filter(
                booking_passenger.c.user_id == self.id).all()
            return passenger_bookings
        except Exception as e:
            print(f"Error fetching bookings: {e}")
            return []

    def soft_delete(self):
        """
        Marks the user as deleted by setting the deleted_at timestamp.
        """
        self.deleted_at = datetime.utcnow()
        db.session.commit()

    def to_dict(self, include_sensitive=False):
        """
        Converts the User instance to a dictionary format.
        Optionally, excludes sensitive fields like password_hash and deleted_at.
        """
        user_data = {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "gender": self.gender,
            "email": self.email,
            "dob": self.dob.isoformat() if self.dob else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "full_name": self.full_name()
        }

        if include_sensitive:
            user_data["password_hash"] = self.password_hash
            user_data["deleted_at"] = self.deleted_at.isoformat() if self.deleted_at else None

        return user_data

    def __repr__(self):
        return f'<User {self.full_name()} ({self.email})>'


# Association Table for Many-to-Many Relationship between Booking and User
booking_passenger = db.Table(
    'booking_passenger',  # Table name
    db.Column('booking_id', db.String(36), db.ForeignKey('bookings.id'), primary_key=True),  # Foreign key to Booking
    db.Column('user_id', db.String(36), db.ForeignKey('users.id'), primary_key=True)  # Foreign key to User
)


class Booking(db.Model):
    __tablename__ = 'bookings'  # Table name for this model

    id = db.Column(db.String(36), primary_key=True, default=default_uuid_generator)  # Primary key, UUID for uniqueness
    reference_number = db.Column(db.String(10), unique=True)  # Unique booking reference number
    owner_id = db.Column(db.String(36), db.ForeignKey('users.id'))  # Foreign key to the owner (User)
    departure_flight_id = db.Column(db.String(36), db.ForeignKey('flights.id'),
                                    nullable=False)  # Foreign key to Departure Flight
    returning_flight_id = db.Column(db.String(36), db.ForeignKey('flights.id'),
                                    nullable=True)  # Foreign key to Return Flight (nullable)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp when the booking was created
    completed = db.Column(db.DateTime)  # Timestamp when the booking was completed (nullable)
    payment_received = db.Column(db.DateTime)  # Timestamp when payment was received (nullable)

    # Relationship to User (owner of the booking)
    owner = db.relationship('User', backref='bookings')  # One-to-many relationship (one User can own multiple bookings)

    # Relationships to Flight (Departure and Return Flights)
    departure_flight = db.relationship('Flight', foreign_keys=[departure_flight_id],
                                       backref='departure_bookings')  # One-to-many with departure flight
    returning_flight = db.relationship('Flight', foreign_keys=[returning_flight_id],
                                       backref='returning_bookings')  # One-to-many with return flight

    # Relationship to User (Passengers in the booking)
    passengers = db.relationship('User', secondary=booking_passenger,
                                 backref='user_bookings')  # Many-to-many through association table

    def __repr__(self):
        """
        Return a string representation of the Booking instance.
        Shows the reference number, owner, and number of passengers.
        """
        return f"<Booking reference_number={self.reference_number}, owner={self.owner.full_name()}, passengers={len(self.passengers)}>"

    def is_round_trip(self):
        """
        Check if the booking is a round trip (i.e., has a return flight).
        Returns True if there is a returning flight, otherwise False.
        """
        return self.returning_flight_id is not None

    def get_trip_status(self):
        """
        Determine the status of the trip based on the departure flight date.
        Returns:
            - "future" if the flight is scheduled for a future date.
            - "current" if the flight is on the current date.
            - "past" if the flight has already passed.
            - "unknown" if no flight date is available.
        """
        flight_date = self.departure_flight.start_date if self.departure_flight else None  # Get departure date of the flight
        today = datetime.utcnow().date()  # Get today's date
        if flight_date:
            if flight_date > today:
                return "future"  # Trip is scheduled for a future date
            elif flight_date == today:
                return "current"  # Trip is happening today
            else:
                return "past"  # Trip has already passed
        return "unknown"  # If no departure flight date, return unknown status

    def to_dict(self):
        """
        Convert the Booking instance to a dictionary format for easy serialization.
        Includes details of the owner, flights, trip status, and passengers.
        """
        return {
            "id": self.id,  # Booking ID
            "reference_number": self.reference_number,  # Booking reference number
            "owner": self.owner.to_dict() if self.owner else None,  # Convert the owner User to a dict
            "departure_flight": self.departure_flight.to_dict() if self.departure_flight else None,
            # Convert the departure Flight to a dict
            "returning_flight": self.returning_flight.to_dict() if self.returning_flight else None,
            # Convert the returning Flight to a dict (if exists)
            "created_at": self.created_at.isoformat() if self.created_at else None,  # Creation timestamp in ISO format
            "completed": self.completed.isoformat() if self.completed else None,
            # Completion timestamp in ISO format (if exists)
            "payment_received": self.payment_received.isoformat() if self.payment_received else None,
            # Payment received timestamp in ISO format (if exists)
            "is_round_trip": self.is_round_trip(),  # Check if this is a round trip
            "trip_status": self.get_trip_status(),  # Get the status of the trip (future, current, past, unknown)
            "passengers": [p.to_dict() for p in self.passengers]  # List of passengers in the booking, each as a dict
        }


class SearchHistory(db.Model):
    __tablename__ = 'search_history'  # Table name for this model

    id = db.Column(db.String(36), primary_key=True, default=default_uuid_generator)  # Unique ID for each search
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)  # Reference to the user
    departure_city = db.Column(db.String(100)   )  # Departure city
    arrival_city = db.Column(db.String(100)   )  # Arrival city
    departure_date = db.Column(db.DateTime )  # Departure date
    return_date = db.Column(db.DateTime )  # Return date (optional)
    trip_type = db.Column(db.String(20) )  # Trip type (e.g., "Roundtrip" or "One-way")
    guests = db.Column(db.Integer, nullable=False, default=1)  # Number of guests
    searched_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Timestamp for the search

    def to_dict(self):
        """Helper method to convert a search record to a dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'departure_city': self.departure_city,
            'arrival_city': self.arrival_city,
            'departure_date': self.departure_date,
            'return_date': self.return_date,
            'trip_type': self.trip_type,
            'guests': self.guests,
            'searched_at': self.searched_at
        }

    def __repr__(self):
        return f'<SearchHistory {self.departure_city} to {self.arrival_city}>'