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


def _terms(text: str) -> set[str]:
    return {w.lower() for w in _WORD.findall(text)} - _STOP


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
    max_sentences: int = 5,
) -> str:

    terms = _terms(question)
    candidates = []

    for rank, result in enumerate(vector_results):
        for sentence in _SENT.split(result.get("content", "")):
            sentence = sentence.strip()
            if len(sentence) < 8:
                continue
            overlap = len(terms & _terms(sentence))
            # prefer keyword overlap, then better-ranked chunks
            candidates.append(
                (overlap, -rank, sentence, result.get("filename"))
            )

    candidates.sort(key=lambda c: (c[0], c[1]), reverse=True)

    picked, seen = [], set()

    for overlap, _, sentence, filename in candidates:
        if overlap == 0 and picked:
            break
        if sentence in seen:
            continue
        seen.add(sentence)
        picked.append((sentence, filename))
        if len(picked) >= max_sentences:
            break

    if not picked:
        return (
            "I could not find enough information in the uploaded "
            "documents."
        )

    lines = ["**Most relevant content from your documents:**", ""]

    for sentence, filename in picked:
        suffix = f" _({filename})_" if filename else ""
        lines.append(f"- {sentence}{suffix}")

    facts = []
    for g in graph_results:
        if g.get("relationship"):
            facts.append(
                f"{g['source']} → {g['relationship']} → {g['target']}"
            )

    if facts:
        lines += ["", "**Related knowledge-graph links:**", ""]
        lines += [f"- {f}" for f in facts[:5]]

    return "\n".join(lines)
