# Local RAG App: Ask Questions About Sports Documents

A **terminal-based retrieval-augmented generation (RAG) project**. Ask a question about local documents, using football league documents as the included example and get an answer using locally served models and a vector database. The command-line interface returns an answer, and Phoenix lets you inspect the retrieval and generation trace.

## Stack

- **Ollama + llama3.2:3b:** local LLM inference
- **BAAI/bge-small-en-v1.5:** local embedding model
- **LlamaIndex:** document ingestion, indexing, retrieval, and response synthesis
- **Actian VectorAI DB:** vector storage and similarity retrieval
- **Arize Phoenix:** local tracing and observability

The app reads files in `docs/`, creates embeddings, stores them in a `sports_rag` collection, retrieves the top three relevant chunks, and passes the retrieved context to the LLM to answer a question.

## Sample documents

The `docs/` folder contains **sample football documents**:

- `league-rules.txt`: points, substitutions, and competition rules
- `team-guide.txt`: training schedules and matchday instructions
- `season-fixtures.txt`: fictional fixtures, results, and statistics


Replace the documents with your own local TXT or other LlamaIndex-supported documents to experiment. 


## Requirements

- Docker with Docker Compose
- An internet connection for the initial Docker image, Ollama model, and embedding-model downloads
- Sufficient disk space and RAM for Ollama, VectorAI DB, Phoenix, and the Python embedding model (approximately 12 GB RAM is a practical starting point)
- Ports 11434, 6574, and 6006 available

## Run the project

From the repository root:

```bash
docker compose up -d
docker compose exec ollama ollama pull llama3.2:3b
docker compose build app
docker compose run --rm app --question "How many points does a team earn for a win?"
```

The first build and query can take several minutes because dependencies and the embedding model must download. Subsequent runs reuse the embedding-model cache, but **the documents are re-ingested and the vector collection is cleared and rebuilt for every query**. Rebuilding the collection keeps the index synchronized with the current documents without implementing incremental updates. For larger collections, separate indexing from querying.

Other questions to try:

```bash
docker compose run --rm app --question "When does the senior squad train?"
docker compose run --rm app --question "Who scored against Cedar Athletic?"
docker compose run --rm app --question "When is Riverside Rovers playing Eastgate Town?"
```

Phoenix traces: http://localhost:6006

To stop the services:

```bash
docker compose down
```

To remove stored model, database, and trace volumes too, run `docker compose down -v` only if you are happy to lose those local files.

## Run the Python script directly (optional)

If Ollama, VectorAI DB, and Phoenix are already running locally, install the Python dependencies in a Python 3.12 environment and run:

```bash
pip install -r requirements.txt
ollama pull llama3.2:3b
python rag.py --docs ./docs --question "What time do players arrive before kickoff?"
```

The default service endpoints are `http://localhost:11434`, `localhost:6574`, and `http://localhost:6006/v1/traces`. The Docker Compose app overrides them with container hostnames.

## How RAG works here

1. **Load:** `SimpleDirectoryReader` reads the sports documents.
2. **Embed:** BGE turns document chunks into numeric vectors.
3. **Store:** Actian VectorAI DB holds those vectors and text.
4. **Retrieve:** The question is embedded, and the top three similar chunks are retrieved.
5. **Generate:** Ollama's Llama 3.2 model produces an answer using the retrieved context.
6. **Trace:** Phoenix records the instrumented LlamaIndex pipeline.
