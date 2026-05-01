"""Wikivoyage section parsing and chunking."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

import mwparserfromhell

RELEVANT_SECTIONS = {
    "Understand", "Get in", "Get around", "See", "Do",
    "Eat", "Drink", "Sleep", "Buy", "Go next",
}


@dataclass
class ParsedSection:
    section_type: str
    text: str
    char_count: int


@dataclass
class ParsedDestination:
    name: str
    lead: str
    sections: list[ParsedSection] = field(default_factory=list)
    raw_chars: int = 0


def _heading_title(section) -> str | None:
    headings = section.filter_headings()
    if not headings:
        return None
    return str(headings[0].title).strip()


def _section_plaintext(section) -> str:
    """Strip the leading heading node, then convert wikitext to plaintext.

    Avoids the fragile ``text.replace(title, "", 1)`` approach which can clip
    body-text occurrences of the section title.
    """
    headings = section.filter_headings()
    if headings:
        try:
            section.remove(headings[0])
        except ValueError:
            pass  # heading not directly contained — leave it; strip_code handles it
    return section.strip_code().strip()


def parse_article(name: str, wikitext: str) -> ParsedDestination:
    code = mwparserfromhell.parse(wikitext)

    # Lead = nodes before the first level-2 heading.
    lead_nodes = []
    for node in code.nodes:
        if hasattr(node, "level") and node.level == 2:
            break
        lead_nodes.append(node)
    lead_text = (
        mwparserfromhell.parse("".join(str(n) for n in lead_nodes))
        .strip_code()
        .strip()
    )

    sections: list[ParsedSection] = []
    for s in code.get_sections(levels=[2]):
        title = _heading_title(s)
        if not title or title not in RELEVANT_SECTIONS:
            continue
        plaintext = _section_plaintext(s)
        if len(plaintext) < 50:
            continue
        sections.append(ParsedSection(
            section_type=title,
            text=plaintext,
            char_count=len(plaintext),
        ))

    return ParsedDestination(
        name=name,
        lead=lead_text,
        sections=sections,
        raw_chars=len(wikitext),
    )


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _split_text(text: str, max_chars: int = 1500, overlap: int = 200) -> list[str]:
    """Paragraph-aware splitter with sentence fallback for huge paragraphs."""
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buf = ""

    def _flush():
        if buf.strip():
            chunks.append(buf.strip())

    for para in paragraphs:
        if len(para) > max_chars:
            # Split a giant paragraph on sentence boundaries.
            _flush()
            buf = ""
            sentences = _SENTENCE_SPLIT.split(para)
            sbuf = ""
            for sent in sentences:
                if len(sbuf) + len(sent) + 1 > max_chars and sbuf:
                    chunks.append(sbuf.strip())
                    sbuf = sbuf[-overlap:] if overlap else ""
                sbuf += (" " if sbuf else "") + sent
            if sbuf.strip():
                chunks.append(sbuf.strip())
            continue

        if len(buf) + len(para) + 2 > max_chars and buf:
            _flush()
            buf = buf[-overlap:] if overlap else ""
        buf += ("\n\n" if buf else "") + para

    _flush()
    return chunks


def chunk_destination(parsed: ParsedDestination) -> tuple[dict, list[dict]]:
    """Returns ``(destination_doc, list_of_section_chunks)``.

    The destination doc lives in the ``destinations`` collection (one per city,
    used by brainstorm queries). Section chunks live in the ``sections``
    collection (used by itinerary queries).
    """
    summary = (parsed.lead[:1500] if parsed.lead else "").strip()
    if not summary and parsed.sections:
        summary = parsed.sections[0].text[:1500]

    destination_doc = {
        "id": f"dest::{parsed.name}",
        "text": summary,
        "metadata": {"destination_name": parsed.name},
    }

    chunks: list[dict] = []
    for sec in parsed.sections:
        for i, chunk_text in enumerate(_split_text(sec.text, max_chars=1500, overlap=200)):
            chunks.append({
                "id": f"sec::{parsed.name}::{sec.section_type}::{i}",
                "text": chunk_text,
                "metadata": {
                    "destination_name": parsed.name,
                    "section_type": sec.section_type,
                    "chunk_index": i,
                },
            })
    return destination_doc, chunks
