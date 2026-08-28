import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from scraper.fetcher import DocumentFetcher
from scraper.parser import HTMLParser
from ingestion.chunker import SemanticChunker, Chunk

logger = logging.getLogger(__name__)


class BGEEmbeddingFunction:
    """
    Embedding function wrapper for BAAI BGE Model (BAAI/bge-small-en-v1.5).
    """

    def __init__(self, model_name: str = settings.BGE_MODEL_NAME):
        logger.info(f"Loading BGE Embedding Model: {model_name}...")
        self.model = SentenceTransformer(model_name)

    def __call__(self, input: List[str]) -> List[List[float]]:
        # BGE models perform best with optional instruction prefix for queries if needed,
        # but standard encoding works cleanly for documents and queries.
        embeddings = self.model.encode(input, normalize_embeddings=True)
        return embeddings.tolist()


class VectorStoreManager:
    """
    Manages persistent ChromaDB vector storage, document indexing,
    and similarity search using BAAI BGE Embeddings.
    """

    COLLECTION_NAME = "hdfc_mutual_funds"

    def __init__(self, vector_db_dir: Optional[Path] = None):
        self.vector_db_dir = vector_db_dir or settings.VECTOR_DB_DIR
        self.vector_db_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing Persistent ChromaDB Client at: {self.vector_db_dir}")
        self.client = chromadb.PersistentClient(path=str(self.vector_db_dir))
        
        self.embedding_fn = BGEEmbeddingFunction()
        
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: List[Chunk]) -> int:
        """
        Embeds and stores a list of Chunk objects in ChromaDB.
        """
        if not chunks:
            return 0

        ids = [c.chunk_id for c in chunks]
        texts = [c.text for c in chunks]
        metadatas = [c.metadata for c in chunks]

        # Generate BGE Embeddings
        embeddings = self.embedding_fn(texts)

        # Add or update chunks in collection
        self.collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        logger.info(f"Successfully indexed {len(chunks)} chunks in ChromaDB.")
        return len(chunks)

    def search(
        self,
        query: str,
        top_k: int = 3,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs dense vector similarity search against indexed financial chunks.
        """
        query_embedding = self.embedding_fn([query])[0]
        
        where_clause = filter_dict if filter_dict else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause,
        )

        search_results = []
        if results and results.get("documents"):
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)
            ids = results["ids"][0]

            for doc, meta, dist, cid in zip(docs, metas, distances, ids):
                search_results.append({
                    "chunk_id": cid,
                    "text": doc,
                    "metadata": meta,
                    "distance": dist,
                    "similarity_score": 1.0 - dist  # Cosine similarity score
                })

        return search_results

    def ingest_all_target_schemes(self, force_refresh: bool = False) -> int:
        """
        End-to-end ingestion pipeline: Fetch HTML -> Parse Metrics -> Chunk -> Store BGE Vectors.
        """
        fetcher = DocumentFetcher()
        parser = HTMLParser()
        chunker = SemanticChunker()

        total_indexed_chunks = 0
        logger.info("Starting End-to-End Ingestion for 5 HDFC Groww Schemes...")

        for url in settings.TARGET_SCHEME_URLS:
            res = fetcher.fetch_url(url, use_cache=True, force_refresh=force_refresh)
            if res.success and res.html_content:
                metrics = parser.parse(res.html_content, url)
                chunks = chunker.create_chunks(metrics)
                count = self.add_chunks(chunks)
                total_indexed_chunks += count

        logger.info(f"End-to-End Ingestion Completed. Total Chunks in DB: {self.collection.count()}")
        return total_indexed_chunks


if __name__ == "__main__":
    vdb = VectorStoreManager()
    count = vdb.ingest_all_target_schemes()
    print(f"Total chunks indexed in ChromaDB: {count}")

    # Test search query
    query = "What is the exit load for HDFC Small Cap Fund?"
    res = vdb.search(query, top_k=2)
    print("\nSearch Results for:", query)
    for r in res:
        print("-" * 50)
        print(f"ID: {r['chunk_id']} | Score: {r['similarity_score']:.4f}")
        print(r['text'])
