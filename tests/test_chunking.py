"""Phase 1 chunking tests — no network, no LLM."""
from trip_planner.chunking import (
    RELEVANT_SECTIONS,
    _split_text,
    chunk_destination,
    parse_article,
)

# Minimal but realistic fixture covering lead + multiple RELEVANT_SECTIONS.
FIXTURE_WIKITEXT = """{{pagebanner|TestCity banner.jpg}}
'''TestCity''' is a fictional coastal capital famous for its trams and its
delicious seafood. The historic center sits on seven hills overlooking a
broad estuary.

==Understand==
TestCity has been continuously inhabited for over two thousand years. The city
has Phoenician roots and was later a major Roman port. Today it is the cultural
and economic heart of the region.

==Get in==
By plane: TestCity International Airport sits 7 km north of downtown.
By train: high-speed rail connects from neighboring countries.

==See==
The cathedral on the upper hill dates to the 12th century. The waterfront
museum hosts a permanent exhibit on the city's seafaring history.
The castle ruins offer the best panoramic view in the city.

==Eat==
Local specialties include grilled sardines, salted cod, and custard tarts.
The historic Alfama neighborhood is known for tiny family-run tavernas.

==Drink==
Cherry liqueur is the signature local drink. The waterfront has many wine bars.

==Stay safe==
Pickpockets operate in tourist areas — keep valuables secure.
"""


def test_parse_article_lead_and_sections():
    parsed = parse_article("TestCity", FIXTURE_WIKITEXT)
    assert parsed.lead, "expected non-empty lead"
    assert "fictional coastal capital" in parsed.lead

    section_types = {s.section_type for s in parsed.sections}
    # ≥4 RELEVANT_SECTIONS extracted
    assert len(section_types) >= 4, f"got only {section_types}"
    assert section_types <= RELEVANT_SECTIONS, f"unexpected sections: {section_types}"
    assert "Stay safe" not in section_types  # filtered out


def test_parse_section_plaintext_drops_heading():
    parsed = parse_article("TestCity", FIXTURE_WIKITEXT)
    eat = next(s for s in parsed.sections if s.section_type == "Eat")
    # Heading should not appear at the start of plaintext
    assert not eat.text.startswith("Eat"), eat.text[:50]
    assert "sardines" in eat.text


def test_chunk_destination_emits_one_doc_and_section_chunks():
    parsed = parse_article("TestCity", FIXTURE_WIKITEXT)
    dest_doc, chunks = chunk_destination(parsed)
    assert dest_doc["id"] == "dest::TestCity"
    assert dest_doc["text"]
    assert len(chunks) >= 4  # at least one per relevant section in the fixture
    for c in chunks:
        assert c["id"].startswith("sec::TestCity::")
        assert c["metadata"]["destination_name"] == "TestCity"


def test_split_text_paragraph_chunking():
    # ~5000 chars across 10 paragraphs; max_chars=1500 -> expect >=3 chunks
    para = ("Sentence one. " * 36 + "\n\n") * 10
    assert len(para) > 4500
    chunks = _split_text(para, max_chars=1500, overlap=200)
    assert len(chunks) >= 3, f"expected >=3 chunks, got {len(chunks)}"
    for c in chunks:
        assert len(c) <= 1700, len(c)


def test_lead_only_article_emits_no_section_chunks():
    minimal = "'''A''' is a small place with no described sections."
    parsed = parse_article("A", minimal)
    assert parsed.lead
    assert parsed.sections == []
    dest_doc, chunks = chunk_destination(parsed)
    assert dest_doc["text"]
    assert chunks == []
