import json
import os

from dotenv import load_dotenv
from openai import OpenAI


# Load environment variables
load_dotenv()


# ==========================================
# OpenAI Configuration
# ==========================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OPENAI_MODEL = os.getenv(
    "OPENAI_CHAT_MODEL",
    "gpt-5.6-luna",
)


if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is missing. "
        "Please check your .env file."
    )


client = OpenAI(
    api_key=OPENAI_API_KEY
)


# ==========================================
# Graph Extraction Prompt
# ==========================================

SYSTEM_PROMPT = """
You are an information extraction system.

Your job is to extract entities and relationships
from the supplied document text.

Return ONLY valid JSON.

The JSON must have exactly this structure:

{
    "entities": [
        {
            "name": "entity name",
            "type": "entity type"
        }
    ],
    "relationships": [
        {
            "source": "source entity",
            "target": "target entity",
            "type": "relationship type"
        }
    ]
}

Rules:

1. Extract meaningful entities only.

2. Do not invent information.

3. Use the exact entity names appearing
   in the supplied text whenever possible.

4. Entity types should be concise.

Examples:

PERSON
COMPANY
ORGANIZATION
LOCATION
PRODUCT
TECHNOLOGY
SERVICE
DATABASE
FRAMEWORK
PROGRAMMING_LANGUAGE
CONCEPT

5. Relationship types should be concise
   and descriptive.

Examples:

FOUNDED_BY
WORKS_FOR
USES
LOCATED_IN
OWNS
PROVIDES
DEPENDS_ON
BUILT_WITH
HAS_SERVICE
USES_DATABASE
USES_TECHNOLOGY

6. Only create a relationship when the
   supplied text provides evidence for it.

7. Do not create relationships from
   general world knowledge.

8. If there are no entities or relationships,
   return empty arrays.

9. Return JSON only.
"""


# ==========================================
# Extract Entities + Relationships
# ==========================================

def extract_graph_data(text: str) -> dict:

    if not text or not text.strip():
        return {
            "entities": [],
            "relationships": [],
        }

    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=SYSTEM_PROMPT,
        input=text,
    )

    raw_output = response.output_text.strip()

    # Remove markdown code fences if returned
    if raw_output.startswith("```"):
        raw_output = raw_output.replace(
            "```json",
            "",
        )
        raw_output = raw_output.replace(
            "```",
            "",
        )
        raw_output = raw_output.strip()

    try:
        data = json.loads(raw_output)

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"OpenAI returned invalid JSON: {exc}"
        )

    if not isinstance(data, dict):
        raise ValueError(
            "Graph extraction result must be a JSON object."
        )

    entities = data.get(
        "entities",
        [],
    )

    relationships = data.get(
        "relationships",
        [],
    )

    if not isinstance(entities, list):
        entities = []

    if not isinstance(relationships, list):
        relationships = []

    return {
        "entities": entities,
        "relationships": relationships,
    }