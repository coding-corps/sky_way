import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root' // This makes the service available throughout your app
})

export class BookingService {
  private apiUrl = 'http://127.0.0.1:5000/api'; // Your API endpoint

  constructor(private http: HttpClient) {}

  // Interfaces should not be decorated, they are for type-checking only
  createBooking(bookingData: any): Observable<any> {
    let params = new HttpParams();
    const token = localStorage.getItem('token');  // Get token from local storage

    // Create headers object with the Authorization token if it exists
    let headers = new HttpHeaders();
    if (token) {
      headers = headers.set('Authorization', `Bearer ${token}`);
    }

    // Send the POST request with the bookingData in the body and headers
    return this.http.post<any>(`${this.apiUrl}/booking`, bookingData, { headers });
  }

  viewBookings(email: string | null, reference: string | null, bookingId:string | null): Observable<any> {
    // Set query parameters for the GET request
    let params = new HttpParams();

    if (email) {
      params = params.set('email', email);
    }
    if (reference){
      params = params.set('reference_number', reference);
    }
    if (bookingId){
      params = params.set('bookingId', bookingId);
    }

    // Include token in headers
    const token = localStorage.getItem('token');
    let headers = new HttpHeaders();
    if (token) {
      headers = headers.set('Authorization', `Bearer ${token}`);
    }

    // Send the GET request with the query parameters and headers
    return this.http.get<any>(`${this.apiUrl}/booking`, { params, headers });
  }


  payBookings(booking_id: string): Observable<any> {
    // Get token from local storage
    const token = localStorage.getItem('token');

    // Create headers object with the Authorization token if it exists
    let headers = new HttpHeaders();
    if (token) {
      headers = headers.set('Authorization', `Bearer ${token}`);
    }

    // Set up the body with booking_id as an object
    const body = { booking_id };

    // Send the POST request with the headers and body
    return this.http.post<any>(`${this.apiUrl}/booking/confirmation`, body, { headers });
  }


}

// Interfaces should be outside of the service class and should not have decorators

export interface Passenger {
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  email: string;
  phone: string;
}

interface Airport {
  code: string;
  id: string;
  name: string;
}


export interface Flight {
  flight_id: string;
  departure_airport: Airport;
  arrival_airport: Airport;
  start_date: string;
  end_date: string;
  duration: string;
  departure_time: string;

  taxes: string;
  base_cost: string;
  departure: string;
  arrival: string;
}


export interface Flight {
  flight_id: string;
  taxes: string;
  base_cost: string;
  departure: string;
  arrival: string;
}

export interface Booking {
  passengers: Passenger[];
  owner: Passenger;
  departing_flight: Flight;
  departure_flight: Flight;
  returning_flight: Flight;
  payment_received: boolean;
  reference_number:string;
  trip_status: string;
  trip_type: string;
}

export interface BookingResponse {
  booking_id: string;
  departing_flight: Flight;
  returning_flight: Flight;
  passengers: Passenger[];
  reference_number: string
  total: string;
}
