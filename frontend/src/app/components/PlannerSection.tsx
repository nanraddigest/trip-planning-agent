import { useState } from 'react';
import { TravelerPreferences } from './TravelerPreferences';

interface PlannerSectionProps {
  onSearch: (searchData: any) => void;
}

export function PlannerSection({ onSearch }: PlannerSectionProps) {
  const [departure, setDeparture] = useState('');
  const [destination, setDestination] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [travelerCount, setTravelerCount] = useState(1);
  const [chatMessage, setChatMessage] = useState('');
  const [travelers, setTravelers] = useState([{ id: 1, vibe: '', flexibleDates: false, budgetFriendly: false }]);

  const handleTravelerCountChange = (count: number) => {
    setTravelerCount(count);
    const newTravelers = Array.from({ length: count }, (_, i) =>
      travelers[i] || { id: i + 1, vibe: '', flexibleDates: false, budgetFriendly: false }
    );
    setTravelers(newTravelers);
  };

  const updateTraveler = (id: number, updates: any) => {
    setTravelers(travelers.map(t => t.id === id ? { ...t, ...updates } : t));
  };

  const handleSearch = () => {
    onSearch({
      departure,
      destination,
      startDate,
      endDate,
      travelerCount,
      travelers,
      chatMessage
    });
  };

  return (
    <div className="bg-card border-2 border-border shadow-lg rounded-2xl">
      <div className="p-8">
        <div className="text-center mb-8">
          <h1 className="text-foreground mb-2 tracking-tight">Plan Your Perfect Journey</h1>
          <p className="text-sm text-muted-foreground italic">Tell us where wanderlust is taking you</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-accent/40 rounded-xl p-5 border border-border">
              <label className="text-foreground text-sm mb-3 block">Describe your dream trip</label>
              <textarea
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                placeholder="I want a relaxing beach vacation in Southeast Asia for 2 weeks starting mid-June. Budget around $3000 per person..."
                className="w-full px-4 py-3 bg-background rounded-lg border border-border focus:border-primary focus:outline-none transition-colors resize-none h-24"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gradient-to-br from-accent/20 to-transparent rounded-xl p-4 border border-border">
                <label className="text-foreground text-sm mb-2 block">Departing From</label>
                <input
                  type="text"
                  value={departure}
                  onChange={(e) => setDeparture(e.target.value)}
                  placeholder="New York, JFK"
                  className="w-full px-3 py-2 bg-background rounded-lg border border-transparent focus:border-primary focus:outline-none transition-colors"
                />
              </div>

              <div className="bg-gradient-to-br from-accent/20 to-transparent rounded-xl p-4 border border-border">
                <label className="text-foreground text-sm mb-2 block">Destination</label>
                <input
                  type="text"
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  placeholder="Paris, Tokyo, Bali..."
                  className="w-full px-3 py-2 bg-background rounded-lg border border-transparent focus:border-primary focus:outline-none transition-colors"
                />
              </div>

              <div className="bg-gradient-to-br from-accent/20 to-transparent rounded-xl p-4 border border-border">
                <label className="text-foreground text-sm mb-2 block">Start Date</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full px-3 py-2 bg-background rounded-lg border border-transparent focus:border-primary focus:outline-none transition-colors"
                />
              </div>

              <div className="bg-gradient-to-br from-accent/20 to-transparent rounded-xl p-4 border border-border">
                <label className="text-foreground text-sm mb-2 block">End Date</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full px-3 py-2 bg-background rounded-lg border border-transparent focus:border-primary focus:outline-none transition-colors"
                />
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="bg-gradient-to-br from-primary/10 to-transparent rounded-xl p-5 border border-border">
              <label className="text-foreground text-sm mb-3 block">Number of Travelers</label>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => handleTravelerCountChange(Math.max(1, travelerCount - 1))}
                  className="w-10 h-10 bg-accent hover:bg-accent/80 rounded-lg transition-colors border border-border"
                >
                  −
                </button>
                <div className="flex-1 text-center bg-background rounded-lg py-2.5 border border-border">
                  {travelerCount}
                </div>
                <button
                  onClick={() => handleTravelerCountChange(travelerCount + 1)}
                  className="w-10 h-10 bg-accent hover:bg-accent/80 rounded-lg transition-colors border border-border"
                >
                  +
                </button>
              </div>
            </div>

            <button
              onClick={handleSearch}
              className="w-full bg-primary text-primary-foreground py-3.5 rounded-xl hover:bg-primary/90 transition-all shadow-md hover:shadow-lg tracking-wide"
            >
              Make my trip!
            </button>
          </div>
        </div>

        {travelerCount >= 2 && (
          <div className="mt-6 pt-6 border-t border-border">
            <h3 className="text-foreground text-sm mb-4">Individual Preferences</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {travelers.map((traveler) => (
                <TravelerPreferences
                  key={traveler.id}
                  travelerNumber={traveler.id}
                  vibe={traveler.vibe}
                  flexibleDates={traveler.flexibleDates}
                  budgetFriendly={traveler.budgetFriendly}
                  onChange={(updates) => updateTraveler(traveler.id, updates)}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
