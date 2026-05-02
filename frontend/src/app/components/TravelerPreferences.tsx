interface TravelerPreferencesProps {
  travelerNumber: number;
  vibe: string;
  flexibleDates: boolean;
  budgetFriendly: boolean;
  onChange: (updates: any) => void;
}

export function TravelerPreferences({
  travelerNumber,
  vibe,
  flexibleDates,
  budgetFriendly,
  onChange
}: TravelerPreferencesProps) {
  return (
    <div className="bg-card rounded-xl p-4 border border-border space-y-3">
      <h4 className="text-sm text-foreground">Traveler {travelerNumber}</h4>

      <div>
        <label className="block mb-1.5 text-xs text-muted-foreground">Vibe</label>
        <select
          value={vibe}
          onChange={(e) => onChange({ vibe: e.target.value })}
          className="w-full px-3 py-2 bg-background rounded-lg border border-border focus:border-primary focus:outline-none transition-colors text-sm"
        >
          <option value="">Any</option>
          <option value="adventure">🏔️ Adventure</option>
          <option value="relaxation">🏖️ Relaxation</option>
          <option value="cultural">🏛️ Cultural</option>
          <option value="nightlife">🌃 Nightlife</option>
          <option value="nature">🌲 Nature</option>
          <option value="urban">🏙️ Urban</option>
        </select>
      </div>

      <div className="space-y-2">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={flexibleDates}
            onChange={(e) => onChange({ flexibleDates: e.target.checked })}
            className="w-4 h-4 rounded accent-primary cursor-pointer"
          />
          <span className="text-xs text-foreground">Flexible dates</span>
        </label>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={budgetFriendly}
            onChange={(e) => onChange({ budgetFriendly: e.target.checked })}
            className="w-4 h-4 rounded accent-primary cursor-pointer"
          />
          <span className="text-xs text-foreground">Budget-friendly</span>
        </label>
      </div>
    </div>
  );
}
