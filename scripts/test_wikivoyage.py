"""Phase 0 — validate Wikivoyage API access and parsing."""
import mwparserfromhell
import requests

USER_AGENT = "TripPlannerClassProject/0.1 (educational)"

r = requests.get(
    "https://en.wikivoyage.org/w/api.php",
    params={
        "action": "parse",
        "page": "Lisbon",
        "format": "json",
        "prop": "wikitext",
        "redirects": 1,
    },
    headers={"User-Agent": USER_AGENT},
    timeout=30,
)
data = r.json()
wikitext = data["parse"]["wikitext"]["*"]
print(f"Fetched {len(wikitext)} chars of wikitext")

parsed = mwparserfromhell.parse(wikitext)
sections = parsed.get_sections(levels=[2], include_lead=True)
print(f"Found {len(sections)} top-level sections:")
for s in sections[:12]:
    headings = s.filter_headings()
    title = str(headings[0].title).strip() if headings else "(lead)"
    print(f"  - {title} ({len(str(s))} chars)")
