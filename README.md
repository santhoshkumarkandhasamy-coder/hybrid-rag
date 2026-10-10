Hybrid RAG: Vector Search + Knowledge Graph
A Retrieval-Augmented Generation (RAG) application that combines semantic vector search with a Neo4j knowledge graph to answer questions from uploaded documents. The project separates document ingestion from chat retrieval and uses a FastAPI backend with a Streamlit frontend.
Repository: https://github.com/santhoshkumarkandhasamy-coder/hybrid-rag
Table of Contents
Overview
Features
Architecture
Technology Stack
Project Structure
Prerequisites
Installation
Environment Configuration
Run the Application
How It Works
API Documentation
Troubleshooting
Security Notes
Roadmap
Overview
Traditional RAG systems usually retrieve relevant text chunks from a vector database. A knowledge graph adds another way to retrieve information: it represents entities and their relationships, making it useful for questions involving people, organizations, locations, concepts, and connections between them.
This project is designed to:
Accept document uploads through the frontend.
Extract and split document text into manageable chunks.
Create local embeddings and index the chunks in FAISS.
Extract entities and relationships and store them in Neo4j.
Retrieve relevant context from both the vector index and the knowledge graph when a user asks a question.
Combine the retrieved context and send it to the language model to generate one grounded answer.
> **Note:** Exact file types and endpoints depend on the loaders and API routes implemented in the current checkout. The setup below describes the intended architecture; keep the README aligned with the code as the project evolves.
Features
Document upload through a Streamlit user interface.
FastAPI backend for ingestion and question-answering APIs.
Vector retrieval using FAISS.
Local embeddings using Sentence Transformers, intended to use `BAAI/bge-small-en-v1.5`.
Knowledge graph storage using Neo4j Aura or a self-hosted Neo4j instance.
Entity and relationship extraction using an LLM.
Hybrid retrieval that combines vector-search results and graph context.
Grounded answers generated from retrieved document context.
Separate ingestion and chat pipelines for easier debugging and maintenance.
Architecture
Pipeline 1: Document ingestion
```text
User uploads a document
        |
        v
FastAPI upload endpoint
        |
        v
Text extraction
        |
        v
Text cleaning and chunking
        |
        +-------------------------------+
        |                               |
        v                               v
Embedding model                 Entity / relationship
        |                       extraction with an LLM
        v                               |
FAISS vector index                      v
                                Neo4j knowledge graph
        |                               |
        +---------------+---------------+
                        |
                        v
                 Ingestion complete
```
Pipeline 2: Question answering
```text
User asks a question in Streamlit
        |
        v
FastAPI chat endpoint
        |
        +-------------------------------+
        |                               |
        v                               v
Vector similarity search        Neo4j graph retrieval
        |                               |
        +---------------+---------------+
                        |
                        v
             Merge relevant context
                        |
                        v
              LLM answer generation
                        |
                        v
             Answer shown in Streamlit
```
The vector index is useful for semantic similarity between a question and document passages. The graph is useful for entity and relationship lookups. Combining both can improve retrieval for questions that need both descriptive passages and connected facts.
Technology Stack
Component	Technology
Frontend	Streamlit
Backend API	FastAPI
ASGI server	Uvicorn
Vector database/index	FAISS
Embeddings	Sentence Transformers (`BAAI/bge-small-en-v1.5`, intended model)
Knowledge graph	Neo4j / Neo4j Aura
LLM	OpenAI API
PDF text extraction	pypdf
Configuration	python-dotenv
Language	Python
Project Structure
The following is a reference structure for the intended application. Your repository may contain additional files or different module names.
```text
hybrid-rag/
├── backend/
│   ├── main.py
│   ├── api/
│   │   └── upload.py
│   ├── ingestion/
│   │   ├── pdf_loader.py
│   │   ├── chunker.py
│   │   ├── embeddings.py
│   │   └── vector_store.py
│   ├── retrieval/
│   │   └── vector_search.py
│   └── models/
│       └── schemas.py
├── frontend/
│   └── app.py
├── data/
│   ├── uploads/
│   └── faiss/
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```
Keep uploaded documents, FAISS index files, credentials, and generated private data out of version control.
Prerequisites
Install the following before starting:
Python 3.10 or newer (use the version supported by your dependencies).
Git.
An OpenAI API key with API access and available billing/credits.
A Neo4j database, such as a Neo4j Aura instance.
Internet access for installing packages and downloading the embedding model on first use.
Installation
1. Clone the repository
```bash
git clone https://github.com/santhoshkumarkandhasamy-coder/hybrid-rag.git
cd hybrid-rag
```
2. Create and activate a virtual environment
Windows — PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
Windows — Command Prompt
```bat
python -m venv .venv
.venv\Scripts\activate.bat
```
Linux / macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
```
3. Install dependencies
If the repository contains `requirements.txt`:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```
If a requirements file is not present, create one containing the dependencies actually imported by your code. Typical packages for this architecture include:
```text
fastapi
uvicorn[standard]
python-multipart
python-dotenv
pypdf
sentence-transformers
faiss-cpu
neo4j
openai
streamlit
```
Do not install this example list in addition to an existing dependency file without checking for version conflicts.
Environment Configuration
Create a `.env` file in the project root. Do not commit it to Git.
```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# Neo4j
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password

# Optional application settings, if supported by your code
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```
Use the exact environment-variable names expected by your source code. For Neo4j Aura, copy the connection URI and credentials from your database's connection details. Never publish API keys or database passwords in your repository, screenshots, logs, or issue reports.
Run the Application
Run these commands from the repository root, with the virtual environment activated.
1. Start the FastAPI backend
```bash
uvicorn backend.main:app --reload
```
If your entry point is different, replace `backend.main:app` with the module and application variable used in your code.
The backend will typically be available at:
API base: `http://127.0.0.1:8000`
Swagger UI: `http://127.0.0.1:8000/docs`
ReDoc: `http://127.0.0.1:8000/redoc`
2. Start the Streamlit frontend
Open a second terminal, activate the same virtual environment, and run:
```bash
streamlit run frontend/app.py
```
Streamlit normally opens the UI in your browser. If the frontend cannot connect to the backend, check the API base URL configured in the frontend and confirm that FastAPI is running.
3. Use the application
Open the Streamlit page.
Upload a supported document.
Start ingestion and wait for the operation to complete.
Ask a question about the uploaded content.
Review the answer and, where implemented, the retrieved context or source information.
Chat should be enabled after ingestion succeeds and the required vector and graph resources are available.
How It Works
1. Text extraction and chunking
The ingestion pipeline extracts text from a supported document and divides it into smaller chunks. Chunking helps retrieve focused passages rather than sending an entire document to the language model.
2. Embedding and FAISS indexing
Each chunk is converted into a numerical embedding by the configured Sentence Transformers model. FAISS indexes these vectors so the system can find semantically similar passages for a question.
3. Knowledge graph construction
An LLM-based extraction step identifies entities and relationships from the document text. These are written to Neo4j as graph nodes and relationships. Validate extracted facts and use stable identifiers to reduce duplicate entities.
4. Hybrid retrieval
When a user asks a question, the system retrieves relevant vector chunks and queries the graph for related entities and relationships. The results are combined into context for answer generation.
5. Answer generation
The LLM receives the user's question and the retrieved context. The prompt should instruct it to prioritize that context, avoid inventing unsupported facts, and clearly say when the available documents do not contain the answer.
API Documentation
FastAPI can generate interactive API documentation automatically. After starting the backend, open:
```text
http://127.0.0.1:8000/docs
```
Use the documentation to inspect the actual endpoints, request schemas, and response formats exposed by your current code. Common operations in this type of project include document upload/ingestion, ingestion status, and question answering; endpoint paths may vary by implementation.
Troubleshooting
`ModuleNotFoundError`
Activate the project's virtual environment and install the packages from `requirements.txt`. Run commands from the repository root so Python can resolve the `backend` package.
`Error loading ASGI app`
Confirm that the module path and FastAPI variable match your source code. For example, `uvicorn backend.main:app --reload` expects `backend/main.py` to define an object named `app`.
OpenAI authentication or quota error
Check that `OPENAI_API_KEY` is set correctly, that the application loads the `.env` file, and that your API account has access and available quota. ChatGPT subscriptions and OpenAI API billing are separate.
Neo4j connection failure
Verify the URI, username, password, network access, and database status. Use the URI scheme supplied by your Neo4j provider. Do not print credentials when debugging.
FAISS index or embedding errors
Check that the embedding model downloads successfully, the same model is used for indexing and querying, and the stored index is compatible with the installed FAISS version. Rebuild the index if the embedding model or vector dimension changes.
Frontend cannot reach the backend
Ensure both services are running, check the backend URL configured in Streamlit, and inspect the FastAPI terminal for errors.
Chat is unavailable after upload
Confirm that ingestion completed successfully and that the application has initialized the required vector index and graph connection. Check backend logs for failures in text extraction, embedding, entity extraction, or Neo4j writes.
Security Notes
Keep `.env`, API keys, database credentials, uploaded private documents, and local indexes out of Git.
Add `.env`, virtual environments, Python cache files, and generated data directories to `.gitignore` as appropriate.
Validate upload file types and sizes.
Do not expose the development server publicly without appropriate authentication, HTTPS, and deployment configuration.
Treat LLM-extracted entities and relationships as potentially inaccurate and validate them where correctness matters.
Roadmap
Potential improvements for this project include:
Improve document format support and extraction quality.
Add ingestion progress and clear error messages in the UI.
Add source citations and document/page metadata to answers.
Add graph-aware retrieval and configurable vector/graph result fusion.
Add document deletion, re-ingestion, and index rebuild operations.
Add automated tests for ingestion, retrieval, and API endpoints.
Add Docker and Docker Compose deployment support.
Add evaluation tests for answer relevance and grounding.
Contributing
Contributions and suggestions are welcome. Please open an issue to discuss a significant change before submitting a pull request.
License
Add the license that applies to this repository. Do not claim a license unless a corresponding `LICENSE` file is included.
