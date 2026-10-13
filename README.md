# Hybrid RAG — Vector Database + Knowledge Graph

A Hybrid Retrieval-Augmented Generation (RAG) application that combines **vector similarity search** with **knowledge graph retrieval** to answer questions from uploaded PDF documents.

The project uses FastAPI for the backend, Streamlit for the frontend, FAISS for vector search, Neo4j for knowledge graph storage, and LangChain to orchestrate the RAG pipeline.

## Features

- **PDF Upload:** Upload PDF documents through the Streamlit interface.
- **Text Extraction:** Extract document content using PyPDF.
- **Text Chunking:** Split extracted text into manageable chunks using LangChain text splitters.
- **Vector Search:** Store document embeddings in FAISS and retrieve semantically relevant content.
- **Knowledge Graph:** Extract entities and relationships and store them in Neo4j.
- **Hybrid Retrieval:** Combine vector search results with knowledge graph results.
- **LLM Answer Generation:** Use an OpenAI model through LangChain to generate a unified answer.
- **Automatic Chat Activation:** Enable chat when both vector indexing and graph indexing complete successfully.
- **REST API:** Expose document ingestion and question-answering functionality through FastAPI.
- **Source References:** Design the retrieval pipeline to retain document and chunk metadata for answer citations.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Frontend | Streamlit |
| Backend | FastAPI |
| API Server | Uvicorn |
| PDF Processing | PyPDF |
| RAG Orchestration | LangChain |
| Text Splitting | LangChain Text Splitters |
| Embeddings Integration | LangChain OpenAI |
| Vector Index | FAISS |
| Knowledge Graph | Neo4j |
| LLM | OpenAI API |
| Configuration | python-dotenv, pydantic-settings |
| HTTP Communication | HTTPX |

## System Architecture

```text
                 USER
                   |
                   v
          +------------------+
          | Streamlit UI     |
          | Upload and Chat  |
          +--------+---------+
                   |
                   v
          +------------------+
          | FastAPI Backend  |
          +--------+---------+
                   |
             PDF Ingestion
                   |
                   v
          +------------------+
          | PyPDF Text Loader |
          +--------+---------+
                   |
                   v
          +------------------+
          | Text Chunking    |
          +--------+---------+
                   |
          +--------+---------+
          |                  |
          v                  v
  +---------------+  +------------------+
  | Embeddings    |  | Entity and        |
  | Generation    |  | Relationship      |
  |               |  | Extraction        |
  +-------+-------+  +---------+--------+
          |                    |
          v                    v
  +---------------+  +------------------+
  | FAISS         |  | Neo4j            |
  | Vector Index  |  | Knowledge Graph  |
  +-------+-------+  +---------+--------+
          |                    |
          +---------+----------+
                    |
                    v
          +------------------+
          | Hybrid Retriever |
          +--------+---------+
                   |
                   v
          +------------------+
          | Context Fusion   |
          +--------+---------+
                   |
                   v
          +------------------+
          | OpenAI LLM       |
          +--------+---------+
                   |
                   v
          +------------------+
          | Final Answer     |
          +------------------+
```

## Project Structure

```text
hybrid-rag/
|
|-- backend/
|   |-- app/
|   |   |-- __init__.py
|   |   |-- main.py
|   |   |
|   |   |-- api/
|   |   |   |-- __init__.py
|   |   |   |-- upload.py
|   |   |   |-- chat.py
|   |   |
|   |   |-- core/
|   |   |   |-- __init__.py
|   |   |   |-- config.py
|   |   |
|   |   |-- ingestion/
|   |   |   |-- __init__.py
|   |   |   |-- loader.py
|   |   |   |-- chunker.py
|   |   |   |-- pipeline.py
|   |   |
|   |   |-- vectorstore/
|   |   |   |-- __init__.py
|   |   |   |-- faiss_store.py
|   |   |
|   |   |-- knowledge_graph/
|   |   |   |-- __init__.py
|   |   |   |-- ner.py
|   |   |   |-- neo4j_store.py
|   |   |
|   |   |-- retrieval/
|   |   |   |-- __init__.py
|   |   |   |-- vector_retriever.py
|   |   |   |-- graph_retriever.py
|   |   |   |-- hybrid_retriever.py
|   |   |
|   |   |-- llm/
|   |       |-- __init__.py
|   |       |-- generator.py
|   |
|   |-- data/
|   |   |-- uploads/
|   |   |-- processed/
|   |
|   |-- faiss_db/
|   |-- requirements.txt
|   |-- .env
|
|-- frontend/
|   |-- app.py
|   |-- api_client.py
|   |-- requirements.txt
|
|-- docker-compose.yml
|-- .gitignore
|-- README.md
```

## Prerequisites

Install the following before starting:

- Python 3.11 or a compatible Python version supported by the selected dependencies.
- Visual Studio Code.
- Git (optional, for version control).
- An OpenAI API key.
- A running Neo4j instance, either local or hosted.
- Internet access for installing packages and calling the OpenAI API.

Docker can be used later to simplify Neo4j setup and application deployment.

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/santhoshkumarkandhasamy-coder/hybrid-rag.git
cd hybrid-rag
```

Alternatively, open your existing project folder in Visual Studio Code.

### 2. Create a Virtual Environment

On Windows PowerShell:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, you can use:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate the environment again.

### 3. Install Backend Dependencies

```powershell
pip install -r backend/requirements.txt
```

### 4. Install Frontend Dependencies

```powershell
pip install -r frontend/requirements.txt
```

### 5. Configure Environment Variables

Create or edit `backend/.env`:

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password

# Application
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000

# Storage
FAISS_DB_PATH=./faiss_db
UPLOAD_DIR=./data/uploads
```

Replace the example credentials with your own values.

**Security:** Never commit `.env` or expose API keys and database passwords in GitHub.

### 6. Start Neo4j

Start your Neo4j database and verify that it is accessible.

For a local installation, the default Bolt connection is:

```text
bolt://localhost:7687
```

For Neo4j Aura, use the connection URI and credentials supplied by your Aura instance.

Ensure the connection details match `backend/.env`.

## Running the Application

Run the backend and frontend in separate terminals.

### 1. Start FastAPI

From the project root:

```powershell
cd backend
..\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

The API will be available at:

- API root: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### 2. Start Streamlit

Open another terminal from the project root:

```powershell
cd frontend
..\venv\Scripts\Activate.ps1
streamlit run app.py
```

Streamlit will display the local URL in the terminal, usually:

http://localhost:8501

Keep both applications running while using the system.

## Pipeline 1 — Document Ingestion

The ingestion pipeline processes the uploaded PDF and indexes its content in both storage systems.

```text
Upload PDF
    |
    v
Validate File
    |
    v
Extract Text with PyPDF
    |
    v
Split Text into Chunks
    |
    +------------------------+
    |                        |
    v                        v
Generate Embeddings    Extract Entities
    |                  and Relationships
    v                        |
Store in FAISS               v
                       Create Graph
                       in Neo4j
    |                        |
    +------------+-----------+
                 |
                 v
        Verify Both Indexes
                 |
                 v
       Mark Ingestion Complete
                 |
                 v
          Enable Chat
```

The application should enable chat only when both indexing operations have succeeded for the selected document.

## Pipeline 2 — Hybrid Question Answering

When a user submits a question, the backend queries both retrieval systems.

```text
User Question
      |
      +----------------------+
      |                      |
      v                      v
FAISS Vector Search    Neo4j Graph Search
      |                      |
      v                      v
Relevant Chunks        Related Entities
and Metadata           and Relationships
      |                      |
      +-----------+----------+
                  |
                  v
           Combine Context
                  |
                  v
          LangChain + OpenAI
                  |
                  v
          Generate One Answer
                  |
                  v
          Return to Streamlit
```

Vector retrieval finds semantically relevant passages. Graph retrieval finds explicit entity relationships and connected facts. The combined evidence is provided to the language model to generate a single response.

## API Design

The following endpoints are planned for the application. Their availability depends on implementation.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Backend welcome message |
| GET | `/health` | Check backend health |
| POST | `/upload` | Upload a PDF |
| POST | `/ingest` | Start document ingestion, if exposed separately |
| GET | `/ingest/status` | Check ingestion status |
| POST | `/chat` | Ask a question about indexed documents |

The Swagger interface at `/docs` can be used to test implemented endpoints.

## Core Modules

| File | Responsibility |
|---|---|
| `main.py` | Create the FastAPI application and register routes |
| `core/config.py` | Load environment configuration |
| `api/upload.py` | Handle document upload requests |
| `api/chat.py` | Handle question-answering requests |
| `ingestion/loader.py` | Extract PDF text |
| `ingestion/chunker.py` | Split text into chunks |
| `ingestion/pipeline.py` | Coordinate ingestion and indexing |
| `vectorstore/faiss_store.py` | Manage embeddings and FAISS persistence |
| `knowledge_graph/ner.py` | Extract entities and relationships |
| `knowledge_graph/neo4j_store.py` | Create and query graph data |
| `retrieval/vector_retriever.py` | Retrieve relevant document chunks |
| `retrieval/graph_retriever.py` | Retrieve graph-related facts |
| `retrieval/hybrid_retriever.py` | Combine vector and graph results |
| `llm/generator.py` | Generate final answers using the LLM |
| `frontend/api_client.py` | Communicate with FastAPI |
| `frontend/app.py` | Provide upload, status, and chat UI |

## Storage and Persistence

### FAISS

FAISS stores vectors for semantic retrieval. The application must save and reload the index and its associated document metadata so that indexed content remains available after a backend restart.

The configured directory is:

```text
backend/faiss_db/
```

### Neo4j

Neo4j stores entities and their relationships as a graph. The graph schema, entity extraction logic, and Cypher queries will be implemented in the backend.

### Uploaded Documents

Uploaded PDFs are stored under:

```text
backend/data/uploads/
```

Processed content and intermediate data can be stored under:

```text
backend/data/processed/
```

Ensure these directories are writable and configure suitable file-size limits and access controls.

## Error Handling and Reliability

The application should:

- Validate uploaded file types and sizes.
- Handle empty or unreadable PDFs.
- Report ingestion failures clearly.
- Track vector and graph indexing status separately.
- Avoid enabling chat when either indexing operation fails.
- Preserve document IDs and chunk metadata for retrieval.
- Handle unavailable Neo4j and OpenAI services.
- Avoid returning unsupported answers when the retrieved context is insufficient.

## Security

- Keep secrets in environment variables.
- Exclude `.env` from version control.
- Validate uploaded files.
- Use authenticated database connections.
- Avoid exposing internal exception details to users.
- Configure authentication and HTTPS before public deployment.
- Use appropriate permissions for uploaded files and persistent indexes.

## Development Roadmap

- [ ] Create the project structure.
- [ ] Configure FastAPI and Streamlit.
- [ ] Connect Neo4j.
- [ ] Implement PDF text extraction.
- [ ] Implement text chunking.
- [ ] Generate embeddings and create a FAISS index.
- [ ] Extract entities and relationships.
- [ ] Store graph data in Neo4j.
- [ ] Implement vector retrieval.
- [ ] Implement graph retrieval.
- [ ] Implement hybrid retrieval and context fusion.
- [ ] Integrate OpenAI answer generation.
- [ ] Connect the upload API to the ingestion pipeline.
- [ ] Enable chat automatically after successful indexing.
- [ ] Add source citations and error handling.
- [ ] Add tests and logging.
- [ ] Containerize the application with Docker.
- [ ] Deploy to a VPS.

## Troubleshooting

### FastAPI Does Not Start

Confirm that the virtual environment is activated and the dependencies are installed.

```powershell
pip install -r backend/requirements.txt
```

Run the backend from the `backend` directory:

```powershell
uvicorn app.main:app --reload
```

### Streamlit Cannot Connect to FastAPI

Verify that FastAPI is running and that the frontend API URL matches:

```text
http://127.0.0.1:8000
```

### OpenAI Authentication Errors

Check that `OPENAI_API_KEY` is valid and that the application loads `backend/.env` correctly.

### Neo4j Connection Errors

Check the URI, username, password, database availability, and network connectivity.

### FAISS Loading Errors

Ensure the saved index and metadata belong to compatible versions and have not been moved or corrupted. Only load locally saved FAISS indexes from trusted sources.

## License

Choose and add a license before distributing this project publicly.

---

**Project:** Hybrid RAG — Vector Database + Knowledge Graph  
**Backend:** FastAPI  
**Frontend:** Streamlit  
**Vector Index:** FAISS  
**Graph Database:** Neo4j  
**RAG Framework:** LangChain  
**LLM Integration:** OpenAI

## Multi-user, secure edition

- **Accounts & roles:** username/password login (scrypt hashes, signed
  expiring tokens, lockout after repeated failures). Roles: `admin`, `user`.
- **Formats:** PDF (scanned pages fall back to OCR), Word (`doc`, `docx`),
  Excel (`xls`, `xlsx`, `csv`), PowerPoint (`ppt`, `pptx`), HTML, text/Markdown,
  and images (PNG/JPG/TIFF/BMP/WebP via OCR).
- **Multiple files & storage:** upload many files at once; each user has a
  private library with a storage quota (default 500 MB) and per-file size cap.
- **Isolation:** users can only list, read, chat with or delete their own
  documents. Admins can manage/delete any file but cannot read its content.
- **Dashboard:** per-user usage, file types, recent uploads.
- **Admin control panel:** create/disable/delete users, change roles, set
  quotas, reset passwords, view all documents, audit log, toggle self sign-up.
- **Hybrid chat across many documents:** vector + graph results are merged
  and the answer cites source files. If Neo4j is down, uploads still work
  (vector-only) and a warning is shown.

### First run

```bash
cp .env.example .env   # set ADMIN_PASSWORD; OPENAI_*/NEO4J_* are optional
uvicorn backend.main:app --reload          # API on :8000
streamlit run frontend/app.py               # UI on :8501
```

Sign in with `ADMIN_USERNAME` / `ADMIN_PASSWORD`. If `ADMIN_PASSWORD` is unset,
a random one is printed once in the backend log. Run tests with `pytest`.
Put the app behind HTTPS (reverse proxy) in production.

### No API keys needed

Leave `OPENAI_*` and `NEO4J_*` blank and the app runs fully offline:
embeddings are local (BAAI/bge-small, downloaded once), the knowledge graph is
stored in SQLite with built-in entity extraction, and answers are assembled
from the best-matching passages of your files (with source names). Add an
OpenAI key and/or Neo4j credentials later to switch to LLM answers and Neo4j.
