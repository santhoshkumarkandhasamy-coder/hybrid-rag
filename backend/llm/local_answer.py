"""Offline answer builder (no LLM): returns the passages and graph
facts that best match the question, with their source files."""

import re

_WORD = re.compile(r"[A-Za-z0-9]{3,}")
_SENT = re.compile(r"(?<=[.!?])\s+|\n+")
_OVERVIEW = re.compile(
    r"\b(tell|about|summar\w*|overview|describe|explain|details?|"
    r"brief|what is|who is|what are|introduc\w*|give me)\b",
    re.I,
)
_HEADING = re.compile(r"^[A-Za-z][A-Za-z &/,\-]{2,45}$")
_STOP = {
    "this", "these", "document", "documents", "file", "files", "resume",
    "about", "tell", "please", "me", "us", "all", "it",
    "the", "and", "for", "are", "was", "were", "what", "which", "who",
    "how", "why", "when", "where", "does", "did", "this", "that", "with",
    "from", "about", "have", "has", "can", "you", "tell", "give", "show",
}


# Offline stand-in for "understanding": related words per topic.
_TOPICS = [
    {"study", "studied", "studying", "education", "educational",
     "qualification", "qualifications", "qualified", "degree", "graduate",
     "graduated", "graduation", "university", "college", "school",
     "institute", "bachelor", "master", "diploma", "certified",
     "certification", "course", "academic"},
    {"work", "worked", "working", "experience", "employer", "employment",
     "job", "career", "company", "role", "position", "designation",
     "responsibilities", "organisation", "organization", "joined"},
    {"skill", "skills", "expertise", "proficient", "tools", "technologies",
     "technology", "competencies", "knowledge"},
    {"contact", "email", "mail", "phone", "mobile", "number", "address",
     "linkedin", "reach"},
    {"salary", "pay", "ctc", "compensation", "price", "cost", "fee", "fees",
     "amount", "payment"},
    {"date", "when", "year", "years", "period", "duration", "tenure"},
    {"project", "projects", "achievement", "achievements", "accomplished",
     "executed", "delivered"},
    {"policy", "rule", "rules", "guideline", "guidelines", "procedure"},
]


def _stem(word: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def _terms(text: str) -> set[str]:
    return {w.lower() for w in _WORD.findall(text)} - _STOP


def _expand(terms: set[str]) -> set[str]:
    """Add related words so 'studied' also finds 'Education'."""

    expanded = set(terms)
    stems = {_stem(t) for t in terms}

    for topic in _TOPICS:
        if terms & topic or stems & {_stem(w) for w in topic}:
            expanded |= topic

    return expanded


def _hits(terms: set[str], text: str) -> int:
    words = {w.lower() for w in _WORD.findall(text)}
    stemmed = {_stem(w) for w in words}
    return sum(1 for t in terms if t in words or _stem(t) in stemmed)


def wants_overview(question: str) -> bool:
    """Broad question ("tell me about this resume") rather than a lookup."""

    content = _terms(question)
    return bool(_OVERVIEW.search(question)) and len(content) <= 3


def _clean(text: str) -> str:
    text = re.sub(r"\[(?:Page|Slide) \d+\]", "", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def build_overview(documents: list[tuple[str, str]]) -> str:
    """Structured overview of up to a few documents (no LLM)."""

    parts = []

    for filename, text in documents[:3]:
        text = _clean(text)
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        headings = []
        for line in lines:
            if (
                _HEADING.match(line)
                and (line.isupper() or line.istitle())
                and line not in headings
            ):
                headings.append(line)

        intro = " ".join(lines)[:900].rsplit(" ", 1)[0]

        block = [f"### {filename}", "", "**Beginning of the document:**", "",
                 f"> {intro}…"]

        if headings:
            block += ["", "**Sections / headings found:** "
                      + " · ".join(headings[:14])]

        block += ["", f"_{len(text):,} characters in total._"]
        parts.append("\n".join(block))

    return (
        "\n\n".join(parts)
        + "\n\n_Offline mode shows extracts, not a written summary. "
        "Add an OpenAI key in `.env` for AI-written summaries, or ask a "
        "specific question._"
    )


def generate_answer(
    question: str,
    vector_results: list[dict],
    graph_results: list[dict],
    max_sentences: int = 6,
) -> str:

    terms = _expand(_terms(question))
    candidates = []

    for rank, result in enumerate(vector_results):

        content = _clean(result.get("content", ""))
        lines = [l.strip() for l in content.splitlines() if l.strip()]

        for index, line in enumerate(lines):

            for sentence in _SENT.split(line):
                sentence = sentence.strip(" -•\t")

                if len(sentence) < 8:
                    continue

                score = _hits(terms, sentence)

                if score == 0:
                    continue

                # include the following line: headings like
                # "EDUCATION" are followed by the actual details
                if len(sentence) < 40 and index + 1 < len(lines):
                    sentence = f"{sentence}: {lines[index + 1]}"

                candidates.append(
                    (score, -rank, sentence, result.get("filename"))
                )

    candidates.sort(key=lambda c: (c[0], c[1]), reverse=True)

    picked, seen = [], set()

    for _, _, sentence, filename in candidates:
        if sentence in seen:
            continue
        seen.add(sentence)
        picked.append((sentence, filename))
        if len(picked) >= max_sentences:
            break

    # Nothing matched by words: show the best-ranked passages instead
    # (the vector search found them by meaning).
    if not picked:
        for result in vector_results[:2]:
            text = _clean(result.get("content", ""))[:700]
            if text:
                picked.append((text, result.get("filename")))

    if not picked:
        return (
            "I could not find enough information in the uploaded "
            "documents."
        )

    lines = ["**Most relevant content from your documents:**", ""]

    for sentence, filename in picked:
        suffix = f" _({filename})_" if filename else ""
        lines.append(f"- {sentence}{suffix}")

    facts = [
        f"{g['source']} → {g['relationship']} → {g['target']}"
        for g in graph_results
        if g.get("relationship")
    ]

    if facts:
        lines += ["", "**Related knowledge-graph links:**", ""]
        lines += [f"- {f}" for f in facts[:5]]

    return "\n".join(lines)
