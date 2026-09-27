import os
from pathlib import Path
from html import escape

import requests
import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AKSAN INTELLIGENCE - Hybrid RAG",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# BACKEND URL
# ============================================================

# Local:
# BACKEND_URL=http://127.0.0.1:8000
#
# Docker:
# BACKEND_URL=http://backend:8000

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


# ============================================================
# SUPPORTED FILE TYPES
# ============================================================

SUPPORTED_FILE_TYPES = [
    "pdf",
    "doc",
    "docx",
    "xlsx",
    "png",
    "jpg",
    "jpeg",
]


SUPPORTED_FILE_LABEL = (
    "PDF, DOCX, XLSX, PNG, JPG, JPEG"
)


# ============================================================
# SESSION STATE
# ============================================================

if "document_id" not in st.session_state:
    st.session_state.document_id = None

if "filename" not in st.session_state:
    st.session_state.filename = None

if "file_type" not in st.session_state:
    st.session_state.file_type = None

if "ingestion_complete" not in st.session_state:
    st.session_state.ingestion_complete = False

if "upload_response" not in st.session_state:
    st.session_state.upload_response = None

if "graph_response" not in st.session_state:
    st.session_state.graph_response = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def check_backend_health():
    """Check whether FastAPI backend is available."""

    try:
        response = requests.get(
            f"{BACKEND_URL}/health",
            timeout=10,
        )

        if response.status_code == 200:
            return True, response.json()

        return False, {
            "status": response.status_code,
            "message": response.text,
        }

    except requests.exceptions.RequestException as e:
        return False, {
            "status": "offline",
            "message": str(e),
        }


def upload_document(uploaded_file):
    """Upload document to FastAPI backend."""

    try:

        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type,
            )
        }

        response = requests.post(
            f"{BACKEND_URL}/documents/upload",
            files=files,
            timeout=600,
        )

        return response

    except requests.exceptions.RequestException as e:

        st.error(
            f"Unable to connect to backend: {e}"
        )

        return None


def ingest_graph(document_id, filename, text):
    """Send extracted text to Neo4j graph ingestion."""

    try:

        response = requests.post(
            f"{BACKEND_URL}/graph/ingest",
            json={
                "document_id": document_id,
                "filename": filename,
                "text": text,
            },
            timeout=600,
        )

        return response

    except requests.exceptions.RequestException as e:

        st.error(
            f"Unable to connect to graph service: {e}"
        )

        return None


def get_document_graph(document_id):
    """Get Neo4j graph for a document."""

    try:

        response = requests.get(
            f"{BACKEND_URL}/graph/{document_id}",
            timeout=60,
        )

        if response.status_code == 200:
            return response.json()

        return None

    except requests.exceptions.RequestException:
        return None


def ask_chat(
    document_id,
    question,
    top_k=5,
):
    """Ask hybrid RAG chat endpoint."""

    try:

        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={
                "document_id": document_id,
                "query": question,
                "vector_top_k": top_k,
                "graph_limit": top_k,
            },
            timeout=600,
        )

        return response

    except requests.exceptions.RequestException as e:

        st.error(
            f"Unable to connect to chat service: {e}"
        )

        return None


def create_graph_html(graph_data):
    """Create PyVis HTML visualization."""

    network = Network(
        height="600px",
        width="100%",
        bgcolor="#ffffff",
        font_color="#000000",
        directed=True,
    )

    network.set_options(
        """
        {
          "nodes": {
            "shape": "dot",
            "size": 20,
            "font": {
              "size": 14
            }
          },
          "edges": {
            "arrows": {
              "to": {
                "enabled": true
              }
            },
            "font": {
              "size": 10,
              "align": "middle"
            },
            "smooth": {
              "enabled": true
            }
          },
          "physics": {
            "enabled": true,
            "stabilization": {
              "iterations": 200
            }
          }
        }
        """
    )

    entities = graph_data.get(
        "entities",
        [],
    )

    relationships = graph_data.get(
        "relationships",
        [],
    )

    # --------------------------------------------------------
    # Add entities
    # --------------------------------------------------------

    for entity in entities:

        name = entity.get(
            "name",
            "Unknown",
        )

        entity_type = entity.get(
            "type",
            "Entity",
        )

        network.add_node(
            name,
            label=name,
            title=f"Type: {entity_type}",
        )

    # --------------------------------------------------------
    # Add relationships
    # --------------------------------------------------------

    for relationship in relationships:

        source = relationship.get(
            "source"
        )

        target = relationship.get(
            "target"
        )

        relation_type = relationship.get(
            "type",
            "RELATES_TO",
        )

        if source and target:

            network.add_edge(
                source,
                target,
                label=relation_type,
                title=relation_type,
            )

    return network.generate_html()


# ============================================================
# HEADER
# ============================================================

st.title("🧠 AKSAN INTELLIGENCE - Hybrid RAG")

st.markdown(
    """
    ### Vector Search + Knowledge Graph + LLM

    Upload a document, build the knowledge graph and vector
    database, and then ask questions using Hybrid RAG.
    """
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Settings")

    st.write("Backend URL")

    st.code(
        BACKEND_URL,
        language="text",
    )

    st.divider()

    top_k = st.slider(
        "Number of search results",
        min_value=1,
        max_value=10,
        value=5,
    )

    st.divider()

    st.subheader("📄 Supported Files")

    st.write(
    """
    • PDF
    • DOC
    • DOCX
    • XLSX
    • PNG
    • JPG
    • JPEG
    """
 )

    st.divider()

    if st.session_state.document_id:

        st.subheader("Current Document")

        st.write(
            st.session_state.filename
        )

        st.caption(
            f"ID: {st.session_state.document_id}"
        )


# ============================================================
# BACKEND STATUS
# ============================================================

st.subheader("🔌 Backend Status")

backend_online, backend_info = check_backend_health()

if backend_online:

    st.success(
        "FastAPI backend is connected."
    )

else:

    st.error(
        "FastAPI backend is not reachable."
    )

    st.code(
        BACKEND_URL,
        language="text",
    )

    st.warning(
        "Start the FastAPI backend before uploading files."
    )


# ============================================================
# FILE UPLOAD
# ============================================================

st.divider()

st.header("📤 Upload Document")

st.write(
    "Upload a document to start the Hybrid RAG pipeline."
)

uploaded_file = st.file_uploader(
    "Choose a file",
    type=SUPPORTED_FILE_TYPES,
    help=(
        "Supported formats: "
        + SUPPORTED_FILE_LABEL
    ),
)


# ============================================================
# SHOW SELECTED FILE
# ============================================================

if uploaded_file:

    extension = Path(
        uploaded_file.name
    ).suffix.lower()

    st.info(
        f"Selected file: **{uploaded_file.name}** "
        f"({extension.upper()})"
    )

    st.write(
        f"File size: "
        f"{uploaded_file.size / 1024:.2f} KB"
    )


# ============================================================
# INGEST BUTTON
# ============================================================

if uploaded_file and backend_online:

    if st.button(
        "🚀 Start Ingestion",
        type="primary",
        use_container_width=True,
    ):

        # Reset previous state

        st.session_state.document_id = None
        st.session_state.filename = None
        st.session_state.file_type = None
        st.session_state.ingestion_complete = False
        st.session_state.upload_response = None
        st.session_state.graph_response = None
        st.session_state.chat_history = []

        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        progress = st.progress(0)

        status_text = st.empty()

        # ====================================================
        # STEP 1 - FILE + FAISS
        # ====================================================

        status_text.info(
            "Step 1/2: Uploading file and creating FAISS index..."
        )

        progress.progress(10)

        upload_response = upload_document(
            uploaded_file
        )

        if upload_response is None:

            progress.empty()
            status_text.error(
                "Upload failed."
            )
            st.stop()

        if upload_response.status_code != 200:

            progress.empty()
            status_text.error(
                "Document ingestion failed."
            )

            try:
                error_data = upload_response.json()

                st.error(
                    error_data.get(
                        "detail",
                        "Unknown backend error.",
                    )
                )

            except Exception:

                st.error(
                    upload_response.text
                )

            st.stop()

        upload_data = upload_response.json()

        st.session_state.upload_response = upload_data

        document_id = upload_data.get(
            "document_id"
        )

        st.session_state.document_id = document_id

        st.session_state.filename = upload_data.get(
            "filename",
            uploaded_file.name,
        )

        st.session_state.file_type = upload_data.get(
            "file_type",
            Path(uploaded_file.name)
            .suffix
            .lower(),
        )

        progress.progress(50)

        status_text.success(
            "FAISS ingestion completed."
        )

        # ====================================================
        # STEP 2 - KNOWLEDGE GRAPH
        # ====================================================

        status_text.info(
            "Step 2/2: Extracting entities and relationships into Neo4j..."
        )

        progress.progress(60)

        extracted_text = upload_data.get(
            "text",
            "",
        )

        if not extracted_text:

            progress.empty()

            status_text.warning(
                "FAISS ingestion completed, but extracted text "
                "was not returned by the upload API."
            )

            st.warning(
                "Your backend upload endpoint needs to return "
                "`text` for the current /graph/ingest API."
            )

            st.stop()

        # ----------------------------------------------------
        # Send document + filename + text to Neo4j
        # ----------------------------------------------------

        graph_response = ingest_graph(
            document_id=document_id,
            filename=st.session_state.filename,
            text=extracted_text,
        )

        if graph_response is None:

            progress.empty()

            status_text.error(
                "Neo4j graph ingestion failed."
            )

            st.stop()

        if graph_response.status_code not in [
            200,
            201,
        ]:

            progress.empty()

            status_text.error(
                "Neo4j graph ingestion failed."
            )

            try:

                graph_error = graph_response.json()

                st.error(
                    graph_error.get(
                        "detail",
                        "Unknown graph error.",
                    )
                )

            except Exception:

                st.error(
                    graph_response.text
                )

            st.stop()

        graph_data = graph_response.json()

        st.session_state.graph_response = graph_data

        progress.progress(100)

        status_text.success(
            "Knowledge graph ingestion completed."
        )

        # ====================================================
        # COMPLETE
        # ====================================================

        st.session_state.ingestion_complete = True

        st.success(
            "🎉 Document ingestion completed successfully!"
        )

        st.info(
            "💬 Hybrid RAG chat is now enabled."
        )

        st.rerun()

        # ====================================================
        # COMPLETE
        # ====================================================

        st.session_state.ingestion_complete = True

        st.success(
            "🎉 Document ingestion completed successfully!"
        )

        st.info(
            "💬 Hybrid RAG chat is now enabled."
        )

        st.rerun()


# ============================================================
# INGESTION SUMMARY
# ============================================================

if st.session_state.upload_response:

    st.divider()

    st.header("📊 Document Overview")

    data = st.session_state.upload_response

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "File",
            data.get(
                "filename",
                "-",
            ),
        )

    with col2:

        st.metric(
            "Type",
            data.get(
                "file_type",
                "-",
            ).upper(),
        )

    with col3:

        st.metric(
            "Characters",
            f"{data.get('characters', 0):,}",
        )

    with col4:

        st.metric(
            "Chunks",
            data.get(
                "chunks",
                0,
            ),
        )

    if data.get("pages"):

        st.caption(
            f"Pages: {data.get('pages')}"
        )

# ============================================================
# KNOWLEDGE GRAPH
# ============================================================

if (
    st.session_state.document_id
    and st.session_state.ingestion_complete
):

    st.divider()

    st.header("🕸️ Knowledge Graph")

    with st.spinner(
        "Loading knowledge graph..."
    ):

        graph_data = get_document_graph(
            st.session_state.document_id
        )

    if graph_data:

        entities = graph_data.get(
            "entities",
            [],
        )

        relationships = graph_data.get(
            "relationships",
            [],
        )

        # ----------------------------------------------------
        # Graph statistics
        # ----------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Entities",
                len(entities),
            )

        with col2:

            st.metric(
                "Relationships",
                len(relationships),
            )

        # ----------------------------------------------------
        # Entity table
        # ----------------------------------------------------

        if entities:

            st.subheader(
                "🔹 Entities"
            )

            entity_rows = []

            for entity in entities:

                entity_rows.append(
                    {
                        "Entity": entity.get(
                            "name",
                            "",
                        ),
                        "Type": entity.get(
                            "type",
                            "",
                        ),
                    }
                )

            entity_table = """
            <table style="width:100%; border-collapse:collapse;">
                <thead>
                    <tr>
                        <th style="text-align:left; padding:8px; border-bottom:1px solid #ddd;">
                            Entity
                        </th>
                        <th style="text-align:left; padding:8px; border-bottom:1px solid #ddd;">
                            Type
                        </th>
                    </tr>
                </thead>
                <tbody>
            """

            for row in entity_rows:

                entity_table += f"""
                    <tr>
                        <td style="padding:8px; border-bottom:1px solid #eee;">
                            {escape(str(row["Entity"]))}
                        </td>
                        <td style="padding:8px; border-bottom:1px solid #eee;">
                            {escape(str(row["Type"]))}
                        </td>
                    </tr>
                """

            entity_table += """
                </tbody>
            </table>
            """

            st.markdown(
                entity_table,
                unsafe_allow_html=True,
            )

        # ----------------------------------------------------
        # Relationship table
        # ----------------------------------------------------

        if relationships:

            st.subheader(
                "🔗 Relationships"
            )

            relationship_rows = []

            for relationship in relationships:

                relationship_rows.append(
                    {
                        "Source": relationship.get(
                            "source",
                            "",
                        ),
                        "Relationship": relationship.get(
                            "type",
                            "",
                        ),
                        "Target": relationship.get(
                            "target",
                            "",
                        ),
                    }
                )

            relationship_table = """
            <table style="width:100%; border-collapse:collapse;">
                <thead>
                    <tr>
                        <th style="text-align:left; padding:8px; border-bottom:1px solid #ddd;">
                            Source
                        </th>
                        <th style="text-align:left; padding:8px; border-bottom:1px solid #ddd;">
                            Relationship
                        </th>
                        <th style="text-align:left; padding:8px; border-bottom:1px solid #ddd;">
                            Target
                        </th>
                    </tr>
                </thead>
                <tbody>
            """

            for row in relationship_rows:

                relationship_table += f"""
                    <tr>
                        <td style="padding:8px; border-bottom:1px solid #eee;">
                            {escape(str(row["Source"]))}
                        </td>
                        <td style="padding:8px; border-bottom:1px solid #eee;">
                            {escape(str(row["Relationship"]))}
                        </td>
                        <td style="padding:8px; border-bottom:1px solid #eee;">
                            {escape(str(row["Target"]))}
                        </td>
                    </tr>
                """

            relationship_table += """
                </tbody>
            </table>
            """

            st.markdown(
                relationship_table,
                unsafe_allow_html=True,
            )

        # ----------------------------------------------------
        # Interactive graph
        # ----------------------------------------------------

        if entities:

            st.subheader(
                "🌐 Interactive Graph"
            )

            graph_html = create_graph_html(
                graph_data
            )

            components.html(
                graph_html,
                height=650,
                scrolling=True,
            )

    else:

        st.warning(
            "Knowledge graph data could not be loaded."
        )



# ============================================================
# CHAT
# ============================================================

st.divider()

st.header("💬 Hybrid RAG Chat")


if not st.session_state.ingestion_complete:

    st.info(
        "🔒 Chat is disabled. "
        "Upload and ingest a document first."
    )

else:

    st.success(
        "🟢 Chat is enabled."
    )

    st.caption(
        "Answers are generated using both "
        "FAISS vector search and Neo4j knowledge graph."
    )

    # --------------------------------------------------------
    # Display previous messages
    # --------------------------------------------------------

    for message in st.session_state.chat_history:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

    # --------------------------------------------------------
    # Chat input
    # --------------------------------------------------------

    question = st.chat_input(
        "Ask a question about your document..."
    )

    if question:

        # ----------------------------------------------------
        # User message
        # ----------------------------------------------------

        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": question,
            }
        )

        with st.chat_message("user"):

            st.markdown(question)

        # ----------------------------------------------------
        # Assistant response
        # ----------------------------------------------------

        with st.chat_message(
            "assistant"
        ):

            with st.spinner(
                "Searching FAISS + Neo4j and generating answer..."
            ):

                response = ask_chat(
                    document_id=(
                        st.session_state.document_id
                    ),
                    question=question,
                    top_k=top_k,
                )

            if response is None:

                answer = (
                    "Unable to connect to the "
                    "chat backend."
                )

                st.error(answer)

            elif response.status_code != 200:

                try:

                    error_data = response.json()

                    answer = error_data.get(
                        "detail",
                        "Chat request failed.",
                    )

                except Exception:

                    answer = response.text

                st.error(answer)

            else:

                try:

                    chat_data = response.json()

                    answer = chat_data.get(
                        "answer",
                        "No answer was returned.",
                    )

                    st.markdown(answer)

                    # ----------------------------------------
                    # Retrieval statistics
                    # ----------------------------------------

                    vector_count = chat_data.get(
                        "vector_result_count"
                    )

                    graph_count = chat_data.get(
                        "graph_result_count"
                    )

                    if (
                        vector_count is not None
                        or graph_count is not None
                    ):

                        st.caption(
                            f"Vector results: "
                            f"{vector_count or 0} | "
                            f"Graph results: "
                            f"{graph_count or 0}"
                        )

                except Exception as e:

                    answer = (
                        f"Unable to process response: {e}"
                    )

                    st.error(answer)

        # ----------------------------------------------------
        # Save assistant response
        # ----------------------------------------------------

        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )


# ============================================================
# RESET
# ============================================================

if st.session_state.document_id:

    st.divider()

    if st.button(
        "🔄 Start New Document",
        use_container_width=True,
    ):

        st.session_state.document_id = None
        st.session_state.filename = None
        st.session_state.file_type = None
        st.session_state.ingestion_complete = False
        st.session_state.upload_response = None
        st.session_state.graph_response = None
        st.session_state.chat_history = []

        st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Hybrid RAG • FastAPI • Streamlit • FAISS • Neo4j • OpenAI"
)