import { useState } from 'react';

interface RawFlight {
  destination: string;
  airline: string;
  departure: string;
  arrival: string;
  duration: string;
  price: number;
  stops: number;
}

interface RawHotel {
  destination: string;
  name: string;
  rating: number;
  location: string;
  amenities: string[];
  pricePerNight: number;
}

interface FullResultsProps {
  allFlights: RawFlight[];
  allHotels: RawHotel[];
}

function groupByDestination<T extends { destination: string }>(items: T[]): Record<string, T[]> {
  const out: Record<string, T[]> = {};
  for (const item of items) {
    if (!out[item.destination]) out[item.destination] = [];
    out[item.destination].push(item);
  }
  return out;
}

function FlightRow({ flight }: { flight: RawFlight }) {
  return (
    <div className="bg-card border border-border rounded-xl p-4 flex items-center justify-between gap-4">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-medium text-foreground truncate">{flight.airline}</span>
          <span className="text-muted-foreground text-sm">·</span>
          <span className="text-sm text-muted-foreground">
            {flight.departure} → {flight.arrival}
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span>{flight.duration}</span>
          <span>·</span>
          <span className={flight.stops === 0 ? 'text-primary' : ''}>
            {flight.stops === 0 ? 'Nonstop' : `${flight.stops} stop${flight.stops > 1 ? 's' : ''}`}
          </span>
        </div>
      </div>
      <div className="text-right shrink-0">
        <div className="text-lg text-primary font-medium">${flight.price.toFixed(0)}</div>
        <p className="text-xs text-muted-foreground">per person</p>
      </div>
    </div>
  );
}

function HotelRow({ hotel }: { hotel: RawHotel }) {
  const stars = '★'.repeat(Math.round(hotel.rating || 0));
  return (
    <div className="bg-card border border-border rounded-xl p-4 flex items-start justify-between gap-4">
      <div className="flex-1 min-w-0">
        <div className="font-medium text-foreground mb-1 truncate">{hotel.name}</div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
          {hotel.rating > 0 && <span className="text-primary">{stars} {hotel.rating.toFixed(1)}</span>}
          {hotel.rating > 0 && hotel.location && <span>·</span>}
          <span className="truncate">{hotel.location}</span>
        </div>
        {hotel.amenities.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {hotel.amenities.slice(0, 4).map((a, idx) => (
              <span
                key={idx}
                className="text-xs px-2 py-0.5 bg-accent/40 border border-border rounded-full text-foreground"
              >
                {a}
              </span>
            ))}
          </div>
        )}
      </div>
      <div className="text-right shrink-0">
        <div className="text-lg text-primary font-medium">${hotel.pricePerNight.toFixed(0)}</div>
        <p className="text-xs text-muted-foreground">per night</p>
      </div>
    </div>
  );
}

export function FullResults({ allFlights, allHotels }: FullResultsProps) {
  const [open, setOpen] = useState(false);

  if (allFlights.length === 0 && allHotels.length === 0) return null;

  const flightsByDest = groupByDestination(allFlights);
  const hotelsByDest = groupByDestination(allHotels);
  const destinations = Array.from(
    new Set([...Object.keys(flightsByDest), ...Object.keys(hotelsByDest)])
  );

  return (
    <div className="mt-12 max-w-6xl mx-auto">
      <div className="flex items-center justify-between bg-card border border-border rounded-2xl p-5">
        <div>
          <h3 className="text-foreground">Show all scraped flights and hotels</h3>
          <p className="text-sm text-muted-foreground italic">
            {allFlights.length} flights · {allHotels.length} hotels found
          </p>
        </div>
        <button
          onClick={() => setOpen(!open)}
          role="switch"
          aria-checked={open}
          className={`relative w-14 h-7 rounded-full transition-colors ${
            open ? 'bg-primary' : 'bg-accent border border-border'
          }`}
        >
          <span
            className={`absolute top-0.5 left-0.5 w-6 h-6 bg-card rounded-full shadow transition-transform ${
              open ? 'translate-x-7' : 'translate-x-0'
            }`}
          />
        </button>
      </div>

      {open && (
        <div className="mt-6 space-y-8">
          {destinations.map((dest) => (
            <section key={dest} className="space-y-4">
              {destinations.length > 1 && (
                <h2 className="text-foreground text-xl tracking-tight border-b border-border pb-2">
                  {dest}
                </h2>
              )}

              {flightsByDest[dest] && flightsByDest[dest].length > 0 && (
                <div>
                  <h4 className="text-foreground mb-3 tracking-tight">
                    Flights ({flightsByDest[dest].length})
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {flightsByDest[dest].map((f, idx) => (
                      <FlightRow key={idx} flight={f} />
                    ))}
                  </div>
                </div>
              )}

              {hotelsByDest[dest] && hotelsByDest[dest].length > 0 && (
                <div>
                  <h4 className="text-foreground mb-3 tracking-tight">
                    Hotels ({hotelsByDest[dest].length})
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {hotelsByDest[dest].map((h, idx) => (
                      <HotelRow key={idx} hotel={h} />
                    ))}
                  </div>
                </div>
              )}
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
