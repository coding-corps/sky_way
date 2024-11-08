import { Component, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { Router } from '@angular/router';
import { FormGroup, FormControl, Validators, ReactiveFormsModule } from '@angular/forms';
import { AutoCompleteModule } from 'primeng/autocomplete';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { AirportService, Destination } from '../../../services/airport.service';
import { MatAutocompleteModule } from '@angular/material/autocomplete';

@Component({
  selector: 'app-flight-search',
  templateUrl: './flight-search.component.html',
  styleUrls: ['./flight-search.component.scss'],
  standalone: true,
  imports: [AutoCompleteModule, CommonModule, ReactiveFormsModule, HttpClientModule, MatAutocompleteModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FlightSearchComponent implements OnInit {
  selectedOption: string = 'Roundtrip';
  destinations: Destination[] = [];
  filteredDestinations: Destination[] = [];
  options: {name:string, code:string}[] = []; // Define options as an array of strings
  flightSearchForm: FormGroup;

  constructor(
    private airportService: AirportService,
    private router: Router
  ) {}

  ngOnInit() {
    this.flightSearchForm = new FormGroup({
      from: new FormControl('', Validators.required),
      to: new FormControl('', Validators.required),
      guests: new FormControl(1, Validators.required),
      depart: new FormControl('', Validators.required),
      return: new FormControl('', Validators.required),
    });

    this.loadDestinations();
  }

  loadDestinations() {
    this.airportService.getDestinations().subscribe({
      next: (response: Destination[]) => {
        this.destinations = response;
        this.options = response.map(dest => ({ name: dest.name, code: dest.code }));
      },
      error: (error) => {
        console.error('Error fetching destinations:', error);
      }
    });
  }

  filterCountry(event: any) {
    const query = event.query.toLowerCase();
    this.filteredDestinations = this.destinations.filter(dest =>
      dest.name.toLowerCase().includes(query)
    );
  }

  selectOption(option: string) {
    this.selectedOption = option;
  }

  navigateToSearchRes() {
    const selectedFrom = this.options.find(option => option.name === this.flightSearchForm.value.from);
    const selectedTo = this.options.find(option => option.name === this.flightSearchForm.value.to);


     const queryParams = {
      type: this.selectedOption,
      from: selectedFrom ? selectedFrom.code : '', // Set 'code' for 'from'
      to: selectedTo ? selectedTo.code : '', // Set 'code' for 'to'
      guests: this.flightSearchForm.value.guests,
      depart: this.flightSearchForm.value.depart,
      return: this.flightSearchForm.value.return,
    };

    console.log( this.flightSearchForm.value)
    this.router.navigate(['sw/explore'], { queryParams });
   }

  navigateToResent() {
    this.router.navigate(['sw/explore'], { queryParams: { recent: true } });
  }
}
