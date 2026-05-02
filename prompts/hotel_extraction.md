You are extracting hotel listings from a Google Hotels page that has been scraped to markdown. The user is searching for hotels in **{destination}** for {check_in_date} to {check_out_date}, {guests} guest(s).

CRITICAL RULES:
- ONLY extract hotels that are EXPLICITLY named in the markdown text below. Do NOT invent, fabricate, or recall hotels from your training data.
- Every hotel you return MUST have its name appear verbatim in the markdown. If you cannot find a name in the markdown, do NOT include it.
- The hotels MUST be in or near {destination}. If a hotel name suggests a different city (e.g. "Denver", "Aurora", "London" when searching Lisbon), DROP IT — it is likely an irrelevant ad.
- Hotels typically appear with patterns like: name on one line, then a price like "$155", then a rating like "4.5/5 (129)", and a star class like "3-star hotel".

Field rules:
- price_per_night: numeric nightly price; strip currency symbols. If only a total is shown, divide by number of nights.
- rating: the numeric guest rating out of 5 (e.g. 4.5). Do NOT confuse this with star class.
- hotel_class: the star classification (3, 4, or 5). Look for "3-star hotel", "4-star hotel", etc.
- amenities: short strings only, e.g. ["Pet-friendly", "Restaurant", "Free cancellation", "Pool", "Spa", "Breakfast", "Kid-friendly"].
- Return up to 10 distinct hotels in the order they appear.
- The notes field should be one short sentence stating where the hotels are and how many you found.

If the markdown contains NO clearly identifiable hotels in {destination}, return an empty hotels list and explain in notes.

--- MARKDOWN ---
{markdown}
