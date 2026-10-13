"""Offline entity / relationship extraction (no LLM).

Entities are proper-noun phrases, acronyms and capitalised terms;
two entities in the same sentence are linked as RELATED_TO."""

import re
from collections import Counter
from itertools import combinations

_PHRASE = re.compile(
    r"\b(?:[A-Z][\w&\-]+)(?:\s+(?:of|and|the|for|&)?\s*[A-Z][\w&\-]+)*"
)
_ACRONYM = re.compile(r"\b[A-Z]{2,6}\b")
_SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")

_STOP = {
    "The", "This", "That", "These", "Those", "There", "Then", "When",
    "Where", "What", "Which", "Who", "How", "Why", "And", "But", "For",
    "With", "From", "Page", "Table", "Slide", "Notes", "Worksheet",
    "However", "Also", "In", "On", "At", "As", "It", "Its", "If", "We",
    "You", "They", "He", "She", "A", "An", "Of", "To", "By", "Is", "Are",
}

_ORG_HINTS = ("Inc", "Ltd", "LLC", "Corp", "Company", "University",
              "Bank", "Group", "Technologies", "Systems", "Solutions")

MAX_ENTITIES = 200
MIN_MENTIONS = 1
MAX_RELATIONS = 400


def _clean(name: str) -> str:
    words = [w for w in name.split() if w not in _STOP]
    return " ".join(words).strip(" -&")


def _entity_type(name: str) -> str:
    if any(h in name for h in _ORG_HINTS):
        return "ORGANIZATION"
    if name.isupper() and len(name) <= 6:
        return "ACRONYM"
    if len(name.split()) >= 2:
        return "NAMED_ENTITY"
    return "CONCEPT"


def extract_graph_data(text: str) -> dict:

    if not text or not text.strip():
        return {"entities": [], "relationships": []}

    counts: Counter = Counter()
    per_sentence: list[list[str]] = []

    for sentence in _SENTENCE.split(text):

        found = []

        phrases = [_clean(m) for m in _PHRASE.findall(sentence)]
        multiword = " ".join(p for p in phrases if " " in p)

        for name in phrases:
            if len(name) > 2 and name not in _STOP:
                found.append(name)

        for acro in _ACRONYM.findall(sentence):
            # skip pieces of a longer name, e.g. RAO in "ESWARA RAO DUDDU"
            if acro not in multiword.split() and acro not in found:
                found.append(acro)

        found = list(dict.fromkeys(found))
        counts.update(found)
        per_sentence.append(found)

    keep = {
        name for name, n in counts.most_common(MAX_ENTITIES)
        if n >= MIN_MENTIONS
    }

    relations: Counter = Counter()

    for found in per_sentence:
        names = [n for n in found if n in keep][:6]
        for a, b in combinations(names, 2):
            if a != b:
                relations[(a, b)] += 1

    return {
        "entities": [
            {"name": n, "type": _entity_type(n)} for n in sorted(keep)
        ],
        "relationships": [
            {"source": a, "target": b, "type": "RELATED_TO"}
            for (a, b), _ in relations.most_common(MAX_RELATIONS)
        ],
    }
