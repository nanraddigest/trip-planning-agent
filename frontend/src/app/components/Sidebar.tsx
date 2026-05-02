import { Brand } from './Brand';

interface SidebarProps {
  searchData: any;
  resultCount: number;
  currentView: 'matches' | 'itinerary';
  onViewChange: (view: 'matches' | 'itinerary') => void;
  onNewSearch: () => void;
}

export function Sidebar({ searchData, resultCount, currentView, onViewChange, onNewSearch }: SidebarProps) {
  return (
    <div className="w-80 h-screen fixed left-0 top-0 bg-card border-r border-border overflow-y-auto">
      <div className="p-6 space-y-6">
        <div className="border-b border-border pb-4">
          <Brand size="md" />
        </div>

        <div className="border-b border-border pb-4">
          <h2 className="text-foreground mb-1">Your Search</h2>
          <p className="text-xs text-muted-foreground">Current trip preferences</p>
        </div>

        <div className="space-y-4">
          {searchData.chatMessage && (
            <div className="bg-accent/30 rounded-lg p-4 border border-border">
              <p className="text-xs text-muted-foreground mb-2">Your Description</p>
              <p className="text-sm text-foreground">{searchData.chatMessage}</p>
            </div>
          )}

          <div className="space-y-3">
            {searchData.departure && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">From</p>
                <p className="text-sm text-foreground">{searchData.departure}</p>
              </div>
            )}

            {searchData.destination && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">To</p>
                <p className="text-sm text-foreground">{searchData.destination}</p>
              </div>
            )}

            {searchData.startDate && searchData.endDate && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">Dates</p>
                <p className="text-sm text-foreground">
                  {new Date(searchData.startDate).toLocaleDateString()} - {new Date(searchData.endDate).toLocaleDateString()}
                </p>
              </div>
            )}

            {searchData.travelerCount && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">Travelers</p>
                <p className="text-sm text-foreground">{searchData.travelerCount} {searchData.travelerCount === 1 ? 'person' : 'people'}</p>
              </div>
            )}
          </div>

          <div className="space-y-2 pt-2">
            <button
              onClick={onNewSearch}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-accent/50 transition-colors text-left"
            >
              <div className="w-8 h-8 bg-muted rounded-lg"></div>
              <div>
                <p className="text-sm text-foreground">New Search</p>
                <p className="text-xs text-muted-foreground">Start over</p>
              </div>
            </button>

            <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-accent/50 transition-colors text-left">
              <div className="w-8 h-8 bg-muted rounded-lg"></div>
              <div>
                <p className="text-sm text-foreground">Update Preferences</p>
                <p className="text-xs text-muted-foreground">Refine search</p>
              </div>
            </button>
          </div>
        </div>

        <div className="border-t border-border pt-4 space-y-2">
          <button
            onClick={() => onViewChange('matches')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-left ${
              currentView === 'matches' ? 'bg-primary/10 border border-primary/20' : 'hover:bg-accent/50'
            }`}
          >
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
              currentView === 'matches' ? 'bg-primary/20' : 'bg-muted'
            }`}>
              <svg className={`w-4 h-4 ${currentView === 'matches' ? 'text-primary' : 'text-muted-foreground'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-foreground">Flight + Hotel</p>
              <p className="text-xs text-muted-foreground">{resultCount} matches</p>
            </div>
          </button>

          <button
            onClick={() => onViewChange('itinerary')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-left ${
              currentView === 'itinerary' ? 'bg-primary/10 border border-primary/20' : 'hover:bg-accent/50'
            }`}
          >
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
              currentView === 'itinerary' ? 'bg-primary/20' : 'bg-muted'
            }`}>
              <svg className={`w-4 h-4 ${currentView === 'itinerary' ? 'text-primary' : 'text-muted-foreground'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-foreground">Itinerary</p>
              <p className="text-xs text-muted-foreground">Plan your days</p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
