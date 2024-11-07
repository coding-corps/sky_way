import { Component, Input, OnInit } from '@angular/core';
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';
import QRCode from 'qrcode';
import { Booking, BookingService,Flight} from '../../../services/booking.service';
 import { ActivatedRoute ,Router } from '@angular/router';

@Component({
  selector: 'app-success',
  standalone: true,
  templateUrl: './success.component.html',
  styleUrls: ['./success.component.css']
})
export class SuccessComponent implements OnInit {
  @Input() bookingId!: string;
  @Input() flightDetails!: { from: string; to: string; date: string; time: string };
  @Input() passengerList!: string[];
  qrCodeUrl!: string;
  constructor(private route: ActivatedRoute, private router: Router, private bookingService: BookingService) {}

  ngOnInit(): void {
    this.route.params.subscribe(params => {
      this.bookingId = params['bookingId'];
    });

    this.bookingService.viewBookings(null, this.bookingId).subscribe(
      (response: Booking[]) => {
        const booking = response[0];

        console.log(booking)
        // this.flightDetails = {
        //   from: booking.departing_flight.arrival_airport.name,
        //   to: booking.arrival_city,
        //   date: booking.departing_flight.departure,
        //   time: booking.departure_time,
        // };
        // this.passengerList = booking.passengers.map(passenger => passenger.first_name);
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

  ngAfterViewInit() {
    this.generateQRCode();
  }

  async generateQRCode() {
    try {
      this.qrCodeUrl = await QRCode.toDataURL(this.bookingId, { errorCorrectionLevel: 'H' });
    } catch (error) {
      console.error('Error generating QR Code:', error);
    }
  }
  downloadPDF() {
    // Create a PDF document
    const pdf = new jsPDF();
  
    // Define the content for the PDF
    const content = ` 
<div style="font-family: Arial, sans-serif; margin: 20px; padding: 20px; border: 2px dashed #dc2626; border-radius: 10px; background-color: #f9f9f9; text-align: left; width: 51vw!important">
  <h1 style="font-size: 24px; color: #333;">SkyWay E-ticket: ${this.bookingReferenceId}</h1>
  <p>Thank you for choosing Skyway Airlines. Your booking has been successfully confirmed.</p>
      <div>
    <ul>
    <li><strong>Carry-On:</strong> 1 bag (up to 22 lbs) per passenger</li>
    <li><strong>Checked Baggage:</strong> 1 bag included (up to 50 lbs) per passenger.</li>
    <li><strong>Excess Baggage Fee:</strong> $75 per additional bag.</li>
</ul>
    </div>

  <div style="margin-top: 20px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: #fff; display: flex; align-items: center; width: 50vw">
    <div style="margin-right: 20px;">
      <img src="${this.qrCodeUrl}" alt="QR Code" style="width: 200px; height: 200px;" />
    </div>

    <div style="text-align: left;">
      <p><strong>Reference ID:</strong> ${this.bookingReferenceId}</p>
      <p><strong>Depart from:</strong> ${this.flightDetails.from} on ${this.flightDetails.date} at ${this.flightDetails.time}</p>
      <p><strong>To Arrive at:</strong> ${this.flightDetails.to}</p>
      <p><strong>Passenger List:</strong> ${this.passengerList.join(', ')}</p>
    </div>

      <div style="display: flex; align-items: center;">
<svg version="1.2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 303 188" width="303" height="188"><defs><image  width="303" height="188" id="img1" href="data:image/png;base64,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"/></defs><style></style><use  href="#img1" x="0" y="0"/></svg> 
</div>
  </div>
  <div>

  <ul>
    <li><strong>Cancellation Policy:</strong> Non-refundable ticket, changes subject to fee.</li>
    <li><strong>Check-In:</strong> Online check-in available 24 hours before departure.</li>
    <li><strong>Seat Selection:</strong> Seats can be selected during check-in or for an additional fee.</li>
</ul>
</div>
</div>


    `;
  
    // Create a temporary div to hold the content
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = content;
    document.body.appendChild(tempDiv); // Append it to the body for rendering
  
    // Use html2canvas to create a canvas from the HTML content
    html2canvas(tempDiv).then((canvas) => {
      const imgData = canvas.toDataURL('image/png');
      const imgWidth = 190; // Adjust to your desired width
      const imgHeight = (canvas.height * imgWidth) / canvas.width; // Calculate imgHeight based on the canvas size
  
      // Add image to PDF
      pdf.addImage(imgData, 'PNG', 10, 10, imgWidth, imgHeight);
      
      // Save the PDF
      pdf.save('e-ticket.pdf');
  
      // Clean up: remove the temporary div after PDF generation
      document.body.removeChild(tempDiv);
    }).catch(error => {
      console.error("Error capturing the content: ", error);
    });
  }
  


  printPage() {
    window.print();
  }


}
