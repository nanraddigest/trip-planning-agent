interface TravelResultCardProps {
  flightInfo: {
    airline: string;
    departure: string;
    arrival: string;
    duration: string;
    price: number;
    stops: number;
  };
  hotelInfo: {
    name: string;
    rating: number;
    location: string;
    amenities: string[];
    pricePerNight: number;
  };
  totalPrice: number;
  onSelect: () => void;
}

export function TravelResultCard({ flightInfo, hotelInfo, totalPrice, onSelect }: TravelResultCardProps) {
  return (
    <div className="bg-card border border-border rounded-2xl overflow-hidden hover:shadow-xl transition-all cursor-pointer hover:scale-[1.02] duration-300">
      <div className="bg-gradient-to-r from-primary/10 to-transparent p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-card-foreground">Complete Package</h3>
            <p className="text-xs text-muted-foreground italic">Flight + Accommodation</p>
          </div>
          <div className="text-right bg-primary/20 px-4 py-2 rounded-xl">
            <div className="text-primary font-medium">${totalPrice}</div>
            <p className="text-xs text-muted-foreground">per person</p>
          </div>
        </div>
      </div>

      <div className="p-5 space-y-4">
        <div className="bg-accent/30 rounded-xl p-4 border border-border space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-primary/5 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <h4 className="text-card-foreground">{flightInfo.airline}</h4>
                <p className="text-xs text-muted-foreground">
                  {flightInfo.departure} → {flightInfo.arrival}
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-card-foreground">${flightInfo.price}</div>
              <p className="text-xs text-muted-foreground">{flightInfo.duration}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-background rounded-full text-xs text-foreground border border-border">
              {flightInfo.stops === 0 ? 'Direct Flight' : `${flightInfo.stops} stop${flightInfo.stops > 1 ? 's' : ''}`}
            </span>
          </div>
        </div>

        <div className="bg-accent/30 rounded-xl p-4 border border-border space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-primary/5 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
              </div>
              <div>
                <h4 className="text-card-foreground">{hotelInfo.name}</h4>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-muted-foreground">{hotelInfo.location}</span>
                  <span className="text-primary">{'★'.repeat(hotelInfo.rating)}</span>
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-card-foreground">${hotelInfo.pricePerNight}</div>
              <p className="text-xs text-muted-foreground">per night</p>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {hotelInfo.amenities.map((amenity, idx) => (
              <span key={idx} className="text-xs bg-background px-2.5 py-1 rounded-full text-muted-foreground border border-border">
                {amenity}
              </span>
            ))}
          </div>
        </div>

        <button
          onClick={onSelect}
          className="w-full bg-primary text-primary-foreground py-3 rounded-xl hover:bg-primary/90 transition-all shadow-md hover:shadow-lg tracking-wide"
        >
          Select Package
        </button>
      </div>
    </div>
  );
}
