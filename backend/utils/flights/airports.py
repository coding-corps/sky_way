# Function to get a list of all airports
from models import Airport, Flight


def get_all_airports():
    """
    Get a list of all airports in the system.
    Excludes any soft-deleted airports and returns the data in a dictionary format.
    """
    airports = Airport.query.filter_by(deleted_at=None).all()  # Exclude soft-deleted airports
    return [airport.to_dict() for airport in airports]


def get_airport_by_id(airport_id):
    """
    Fetch an airport by its ID.

    Args:
        airport_id (str): The unique identifier of the airport.

    Returns:
        dict: Airport data if found, None otherwise.
    """
    airport = Airport.query.filter_by(id=airport_id).first()
    if airport is None:
        return None  # Explicitly return None if not found
    return airport.to_dict()


def get_arrival_airports_for_departing_flights(departing_airport_id):
    """
    Given an airport, get a list of arrival airports from all the departing flights' arrival_airport_id.

    Args:
        departing_airport_id (str): The ID of the departing airport.

    Returns:
        list: A list of unique arrival airports for all departing flights.
    """
    # Fetch all unique arrival airports for departing flights from the given airport
    departing_flights = Flight.query.filter_by(
        departure_airport_id=departing_airport_id,
        deleted_at=None
    ).distinct(Flight.arrival_airport_id).all()  # Use distinct to avoid duplicates

    # Ensure that we handle cases where no results are found
    if not departing_flights:
        return []

    # Extract and return the arrival airports (unique)
    arrival_airports = [flight.arrival_airport.to_dict() for flight in departing_flights]
    return arrival_airports
