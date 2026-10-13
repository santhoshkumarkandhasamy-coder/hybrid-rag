"""Offline answer builder (no LLM): returns the passages and graph
facts that best match the question, with their source files."""

import re

_WORD = re.compile(r"[A-Za-z0-9]{3,}")
_SENT = re.compile(r"(?<=[.!?])\s+|\n+")
_STOP = {
    "the", "and", "for", "are", "was", "were", "what", "which", "who",
    "how", "why", "when", "where", "does", "did", "this", "that", "with",
    "from", "about", "have", "has", "can", "you", "tell", "give", "show",
}


def _terms(text: str) -> set[str]:
    return {w.lower() for w in _WORD.findall(text)} - _STOP


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
