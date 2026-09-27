import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# ==========================================
# Load .env from project root
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(
    dotenv_path=ENV_FILE,
)


# ==========================================
# OpenAI Configuration
# ==========================================

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY"
)

OPENAI_MODEL = os.getenv(
    "OPENAI_CHAT_MODEL"
)


# ==========================================
# Validate Configuration
# ==========================================

if not OPENAI_API_KEY:

    raise ValueError(
        "OPENAI_API_KEY is missing. "
        f"Check your .env file: {ENV_FILE}"
    )


if not OPENAI_MODEL:

    raise ValueError(
        "OPENAI_CHAT_MODEL is missing. "
        f"Check your .env file: {ENV_FILE}"
    )


# ==========================================
# OpenAI Client
# ==========================================

client = OpenAI(
    api_key=OPENAI_API_KEY
)


# ==========================================
# System Prompt
# ==========================================

SYSTEM_PROMPT = """
You are a helpful Hybrid RAG assistant.

Answer the user's question using ONLY
the information provided in the retrieved
document context.

The context contains two sources:

1. VECTOR CONTEXT
   Relevant text retrieved from the uploaded
   document using semantic vector search.

2. GRAPH CONTEXT
   Entities and relationships extracted from
   the uploaded document and stored in Neo4j.

Use both sources when useful.

Rules:

1. Do not invent information.

2. Do not use outside knowledge.

3. If the information is not available in the
   supplied context, say:

   "I could not find enough information
   in the uploaded document."

4. Give a clear and concise answer.

5. Combine vector and graph information when
   they support the same answer.
"""


# ==========================================
# Generate Answer
# ==========================================

def generate_answer(
    question: str,
    vector_results: list[dict],
    graph_results: list[dict],
) -> str:

    # --------------------------------------
    # Vector Context
    # --------------------------------------

    vector_context_parts = []

    for result in vector_results:

        content = result.get(
            "content",
            "",
        )

        if content.strip():

            vector_context_parts.append(
                content
            )

    vector_context = "\n\n".join(
        vector_context_parts
    )


    # --------------------------------------
    # Graph Context
    # --------------------------------------

    graph_context_parts = []

    for result in graph_results:

        source = result.get("source")
        source_type = result.get("source_type")
        relationship = result.get("relationship")
        target = result.get("target")
        target_type = result.get("target_type")

        if not relationship:

            graph_context_parts.append(
                f"Entity: {source} "
                f"({source_type})"
            )

        else:

            graph_context_parts.append(
                f"{source} "
                f"({source_type}) "
                f"-[{relationship}]-> "
                f"{target} "
                f"({target_type})"
            )

    graph_context = "\n".join(
        graph_context_parts
    )


    # --------------------------------------
    # User Prompt
    # --------------------------------------

    user_prompt = f"""
USER QUESTION:
{question}

VECTOR CONTEXT:
{vector_context}

GRAPH CONTEXT:
{graph_context}

Answer the user's question using only
the supplied document context.
"""


    # --------------------------------------
    # OpenAI Responses API
    # --------------------------------------

    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=SYSTEM_PROMPT,
        input=user_prompt,
    )


    # --------------------------------------
    # Final Answer
    # --------------------------------------

    answer = response.output_text.strip()

    if not answer:

        return (
            "I could not generate an answer "
            "from the uploaded document."
        )

    return answer