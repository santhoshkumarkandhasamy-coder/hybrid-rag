"""Answer generation with a local Ollama model (no API key, no cloud)."""

import requests

from backend.core import config

SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question using ONLY "
    "the document context provided (text passages and knowledge-graph "
    "facts). If the context is not enough, say you could not find enough "
    "information in the uploaded documents. Be clear and well organised. "
    "Mention the source file names you used."
)


def generate_answer(
    question: str,
    vector_results: list[dict],
    graph_results: list[dict],
    overview_text: str | None = None,
) -> str:

    passages = [
        f"[Source: {r.get('filename')}]\n{r['content']}"
        for r in vector_results
        if r.get("content", "").strip()
    ]

    facts = [
        f"{g['source']} -[{g['relationship']}]-> {g['target']}"
        for g in graph_results
        if g.get("relationship")
    ]

    context = "\n\n".join(passages)

    if overview_text:
        context = overview_text[:12000] + "\n\n" + context

    prompt = (
        f"QUESTION:\n{question}\n\nDOCUMENT CONTEXT:\n{context}\n\n"
        f"GRAPH FACTS:\n" + "\n".join(facts)
    )

    response = requests.post(
        f"{config.OLLAMA_URL}/api/chat",
        json={
            "model": config.OLLAMA_MODEL,
            "stream": False,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=600,
    )
    response.raise_for_status()

    answer = response.json()["message"]["content"].strip()

    if not answer:
        raise RuntimeError("Ollama returned an empty answer.")

    return answer
