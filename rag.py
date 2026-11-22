"""Ask questions about local sports documents using Ollama, LlamaIndex, VectorAI DB and Phoenix.

Example:
    python rag.py --docs ./docs --question "How many points is a win worth?"
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from llama_index.core import Settings, SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.actian_vectorai import ActianVectorAIVectorStore
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from phoenix.otel import register

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
VECTORAI_URL = os.getenv("VECTORAI_URL", "localhost:6574")
PHOENIX_TRACES_URL = os.getenv("PHOENIX_TRACES_URL", "http://localhost:6006/v1/traces")
LLM_MODEL = "llama3.2:3b"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
COLLECTION_NAME = "sports_rag"
TOP_K = 3
logger = logging.getLogger("sports_rag")


def configure_tracing() -> None:
    provider = register(project_name="local-sports-rag", endpoint=PHOENIX_TRACES_URL)
    LlamaIndexInstrumentor().instrument(tracer_provider=provider)


def configure_models() -> None:
    Settings.llm = Ollama(
        model=LLM_MODEL, base_url=OLLAMA_URL,
        request_timeout=300.0, context_window=4096,
    )
    Settings.embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL)


def answer(docs_dir: Path, question: str) -> str:
    """Load sports documents, index their text, and answer with retrieved context."""
    documents = SimpleDirectoryReader(input_dir=str(docs_dir)).load_data()
    if not documents:
        raise ValueError(f"No readable documents found in {docs_dir}")

    logger.info("Loaded %d documents from %s", len(documents), docs_dir)
    with ActianVectorAIVectorStore(
        url=VECTORAI_URL,
        collection_name=COLLECTION_NAME,
        stores_text=True,
        clear_existing_collection=True,
    ) as store:
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=StorageContext.from_defaults(vector_store=store),
        )
        response = index.as_query_engine(similarity_top_k=TOP_K).query(question)
    return str(response)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local sports-document RAG demo")
    parser.add_argument("--docs", type=Path, default=Path("docs"))
    parser.add_argument("--question", required=True)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if not args.docs.is_dir():
        parser.error(f"Document folder not found: {args.docs}")
    configure_tracing()
    configure_models()
    print(answer(args.docs, args.question))
    return 0


if __name__ == "__main__":
    sys.exit(main())
