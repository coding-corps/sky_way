import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, AbstractControl, ValidationErrors, ReactiveFormsModule } from '@angular/forms';
import { PriceSummaryComponent } from '../price-summary/price-summary.component';
import { FlightDetailsComponent } from '../../flight-details/flight-details.component';
import { ActivatedRoute, Router } from '@angular/router';
import { BookingService } from '../../../services/booking.service';

// Define interface for Airport
interface Airport {
  code: string;
  id: string;
  name: string;
}

// Define interface for Flight
interface Flight {
  arrival_airport: Airport;
  arrival_time: string;
  cost: string;
  departure_airport: Airport;
  departure_time: string;
  duration: number;
  end_date: string;
  flight_num: string;
  id: string;
  start_date: string;
}

// Define interface for User (Owner and Passenger)
interface User {
  created_at: string;
  dob: string | null;
  email: string;
  first_name: string;
  full_name: string;
  gender: string | null;
  id: string;
  last_name: string;
  updated_at: string;
}

// Define interface for Booking
interface Booking {
  completed: string | null;
  created_at: string;
  departure_flight: Flight;
  id: string;
  is_round_trip: boolean;
  owner: User;
  passengers: User[];
  payment_received: string | null;
  reference_number: string;
  returning_flight: Flight | null;
  trip_status: string;
}

@Component({
  selector: 'app-payment-info',
  templateUrl: './payment-info.component.html',
  styleUrls: ['./payment-info.component.css'],
  imports: [ReactiveFormsModule, CommonModule, FlightDetailsComponent, PriceSummaryComponent],
  standalone: true
})
export class PaymentInfoComponent implements OnInit {
  paymentForm: FormGroup;
  bookingId!: string;
  departure_flight: Flight | null = null;
  is_round_trip: boolean = false;
  returning_flight: Flight | null = null;
  trip_status: string = '';
  reference_number: string = '';
  passengers: User[] = [];
  booking_id:string;
  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private bookingService: BookingService
  ) {
    this.paymentForm = this.fb.group({
      cardholderName: ['', [Validators.required, Validators.minLength(3)]],
      cardNumber: ['', [Validators.required, Validators.pattern(/^\d{16}$/)]],
      expirationDate: ['', [Validators.required, this.expirationDateValidator]],
      cvv: ['', [Validators.required, Validators.pattern(/^\d{3}$/)]],
    });
  }

  ngOnInit(): void {
    this.route.params.subscribe(params => {
      this.bookingId = params['bookingId'];
    });

    this.bookingService.viewBookings(null, this.bookingId).subscribe(
      (response: Booking[]) => {
        console.log('Booking details:', response);
        this.departure_flight = response[0].departure_flight;
        this.is_round_trip = response[0].is_round_trip;
        this.returning_flight = response[0].returning_flight;
        this.trip_status = response[0].trip_status;
        this.reference_number = response[0].reference_number;
        this.passengers = response[0].passengers;
        this.booking_id = response[0].id;
      },
      (error) => {
        if (error.status === 401) {
          this.router.navigate(['/sw/login']);
        } else {
          console.error('Error viewing booking:', error);
        }
      }
    );
  }

  expirationDateValidator(control: AbstractControl): ValidationErrors | null {
    const value = control.value;
    if (!value) return null;

    const [month, year] = value.split('/').map((v: string) => parseInt(v, 10));

    if (!month || !year) return { invalidDate: true };

    const expirationDate = new Date(Number(`20${year}`), month - 1);
    const today = new Date();

    return expirationDate < today ? { expired: true } : null;
  }

  navigateToConfirmation(bookingId: string) {
    if (bookingId) {
      this.router.navigate(['/sw/booking/confirmation/'+bookingId], {
        queryParams: { bookingId: bookingId }
      });
    } else {
      console.error('Booking ID is not defined!');
    }
  }

  onSubmit(): void {
    if (this.paymentForm.valid) {
      console.log('Payment Information:', this.paymentForm.value);

      this.bookingService.payBookings(this.booking_id).subscribe(
        (response) => {
          console.log('Booking created:', response);
        },
        (error) => {
          if (error.status === 401) {
            // Redirect to login page on 401 Unauthorized error
            this.router.navigate(['/sw/login']);
          }
           console.error('Error creating booking:', error);
          if (error.status=== 409){
            // already paid
            this.navigateToConfirmation(this.booking_id);
          }
          // Handle error gracefully (e.g., show a message to the user)
        }
      );

      this.navigateToConfirmation(this.booking_id);
    } else {
      console.log(this.paymentForm.errors);
    }
  }

  get formControls() {
    return this.paymentForm.controls;
  }
}
