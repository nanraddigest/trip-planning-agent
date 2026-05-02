import { useState } from 'react';
import { PlannerSection } from './components/PlannerSection';
import { TravelResultCard } from './components/TravelResultCard';
import { Sidebar } from './components/Sidebar';
import { ItineraryPage } from './components/ItineraryPage';
import { FullResults } from './components/FullResults';
import { Brand } from './components/Brand';

const API_BASE = "http://localhost:8000";

export default function App() {
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searchNotes, setSearchNotes] = useState<string>("");
  const [allFlights, setAllFlights] = useState<any[]>([]);
  const [allHotels, setAllHotels] = useState<any[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [searchData, setSearchData] = useState<any>(null);
  const [currentView, setCurrentView] = useState<'matches' | 'itinerary'>('matches');
  const [selectedPackage, setSelectedPackage] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (data: any) => {
    setSearchData(data);
    setIsLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const response = await fetch(`${API_BASE}/api/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          departure: data.departure,
          destination: data.destination,
          startDate: data.startDate,
          endDate: data.endDate,
          travelerCount: data.travelerCount,
          chatMessage: data.chatMessage,
          travelers: data.travelers,
        }),
      });

      if (!response.ok) {
        const detail = await response.json().catch(() => null);
        throw new Error(detail?.detail || `Search failed (${response.status})`);
      }

      const result = await response.json();
      setSearchResults(result.packages || []);
      setSearchNotes(result.notes || "");
      setAllFlights(result.allFlights || []);
      setAllHotels(result.allHotels || []);
    } catch (e: any) {
      setError(e.message || "Search failed. Please try again.");
      setSearchResults([]);
      setSearchNotes("");
      setAllFlights([]);
      setAllHotels([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewSearch = () => {
    setHasSearched(false);
    setSearchData(null);
    setSearchResults([]);
    setSearchNotes("");
    setAllFlights([]);
    setAllHotels([]);
    setCurrentView('matches');
    setSelectedPackage(null);
    setError(null);
  };

  const handleSelectPackage = (packageData: any) => {
    setSelectedPackage(packageData);
    setCurrentView('itinerary');
  };

  return (
    <div className="min-h-screen bg-background">
      {hasSearched && (
        <Sidebar
          searchData={searchData}
          resultCount={searchResults.length}
          currentView={currentView}
          onViewChange={setCurrentView}
          onNewSearch={handleNewSearch}
        />
      )}

      <div className={`${hasSearched ? 'ml-80' : ''} transition-all duration-300`}>
        {!hasSearched ? (
          <div className="min-h-screen p-8">
            <div className="max-w-4xl mx-auto mb-8">
              <Brand size="lg" />
            </div>
            <div className="flex items-center justify-center">
              <div className="max-w-4xl w-full">
                <PlannerSection onSearch={handleSearch} />
              </div>
            </div>
          </div>
        ) : isLoading ? (
          <div className="p-8 flex items-center justify-center min-h-[60vh]">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground italic">
                Searching flights and hotels...
              </p>
            </div>
          </div>
        ) : error ? (
          <div className="p-8">
            <div className="max-w-2xl mx-auto text-center">
              <p className="text-destructive mb-4">{error}</p>
              <button
                onClick={handleNewSearch}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg"
              >
                Try Again
              </button>
            </div>
          </div>
        ) : currentView === 'matches' ? (
          <div className="p-8">
            <div className="max-w-6xl mx-auto">
              <div className="mb-8">
                <h2 className="text-foreground mb-2 tracking-tight">Your Perfect Matches</h2>
                <p className="text-muted-foreground italic">
                  {searchResults.length} curated combinations found
                </p>
              </div>

              {searchResults.length === 0 ? (
                <div className="bg-card border border-border rounded-2xl p-6 max-w-2xl">
                  <p className="text-foreground mb-3">
                    {searchNotes || "No packages found."}
                  </p>
                  <button
                    onClick={handleNewSearch}
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                  >
                    Try Again
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                  {searchResults.map((result, idx) => (
                    <TravelResultCard
                      key={idx}
                      flightInfo={result.flightInfo}
                      hotelInfo={result.hotelInfo}
                      totalPrice={result.totalPrice}
                      onSelect={() => handleSelectPackage(result)}
                    />
                  ))}
                </div>
              )}
            </div>

            <FullResults allFlights={allFlights} allHotels={allHotels} />
          </div>
        ) : (
          <ItineraryPage
            selectedPackage={selectedPackage}
            searchData={searchData}
          />
        )}
      </div>
    </div>
  );
}
