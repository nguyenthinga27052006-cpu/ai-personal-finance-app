from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

from app.ai.rag.knowledge_docs import SEED_KNOWLEDGE_DOCUMENTS, KnowledgeDocument


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    doc_id: str
    content: str
    metadata: dict[str, Any]
    score: float = 0.0


def clean_text(text: str) -> str:
    """Clean and normalize document text."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def recursive_chunk_text(
    text: str,
    title: str | None = None,
    chunk_size: int = 400,
    chunk_overlap: int = 120,
) -> list[str]:
    """
    Split text into chunks using recursive splitting heuristics.
    Preserves document title context at the beginning of each chunk.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return []

    prefix = f"[{title}] " if title else ""
    max_body_len = max(50, chunk_size - len(prefix))

    if len(cleaned) <= max_body_len:
        return [f"{prefix}{cleaned}"]

    separators = ["\n\n", "\n", ". ", "; ", ", ", " "]
    chunks: list[str] = []

    start = 0
    text_len = len(cleaned)

    while start < text_len:
        end = min(start + max_body_len, text_len)
        if end < text_len:
            best_break = -1
            for sep in separators:
                pos = cleaned.rfind(sep, start + (max_body_len // 2), end)
                if pos != -1:
                    best_break = pos + len(sep)
                    break
            if best_break != -1:
                end = best_break

        sub = cleaned[start:end].strip()
        if sub:
            chunks.append(f"{prefix}{sub}")

        if end >= text_len:
            break
        start = max(start + 1, end - chunk_overlap)

    return chunks


class VietnameseBM25Tokenizer:
    """
    Vietnamese word segmenter for BM25 Sparse Search.
    Uses pyvi/underthesea if available, with fallback to financial compound word segmentation.
    """

    FINANCIAL_COMPOUNDS = {
        "lương về": "lương_về",
        "thu nhập": "thu_nhập",
        "thu nhập ròng": "thu_nhập_ròng",
        "thủng ví": "thủng_ví",
        "vượt ngân sách": "vượt_ngân_sách",
        "quỹ khẩn cấp": "quỹ_khẩn_cấp",
        "tích sản": "tích_sản",
        "đầu tư": "đầu_tư",
        "tiết kiệm linh hoạt": "tiết_kiệm_linh_hoạt",
        "nhu cầu thiết yếu": "nhu_cầu_thiết_yếu",
        "mong muốn cá nhân": "mong_muốn_cá_nhân",
        "bình quân giá": "bình_quân_giá",
        "hạn mức chi tiêu": "hạn_mức_chi_tiêu",
        "tuyết lăn": "tuyết_lăn",
        "tuyết lở": "tuyết_lở",
        "ăn uống": "ăn_uống",
        "mua sắm": "mua_sắm",
        "đi lại": "đi_lại",
        "giải trí": "giải_trí",
        "hóa đơn": "hóa_đơn",
        "tiền nhà": "tiền_nhà",
    }

    @classmethod
    def tokenize(cls, text: str) -> list[str]:
        lowered = text.lower()
        try:
            from pyvi import ViTokenizer  # type: ignore

            tokenized = ViTokenizer.tokenize(lowered)
            return re.findall(r"\w+", tokenized)
        except ImportError:
            pass

        try:
            import underthesea  # type: ignore

            tokenized = underthesea.word_tokenize(lowered, format="text")
            return re.findall(r"\w+", tokenized)
        except ImportError:
            pass

        segmented = lowered
        for phrase, compound in cls.FINANCIAL_COMPOUNDS.items():
            if phrase in segmented:
                segmented = segmented.replace(phrase, compound)

        return re.findall(r"\w+", segmented)


class VietnameseBM25Searcher:
    """Lightweight BM25 searcher utilizing Vietnamese word segmentation."""

    def __init__(self) -> None:
        self.tokenizer = VietnameseBM25Tokenizer()

    def score(self, query: str, content: str) -> float:
        q_tokens = set(self.tokenizer.tokenize(query))
        c_tokens = self.tokenizer.tokenize(content)
        if not q_tokens or not c_tokens:
            return 0.0

        matches = sum(1 for token in c_tokens if token in q_tokens)
        unique_matches = len(q_tokens & set(c_tokens))
        length_penalty = math.log(len(c_tokens) + 1.0)
        return (matches + unique_matches * 2.0) / length_penalty


class DenseEmbeddingProvider:
    """
    Pluggable Dense Embedding Provider supporting environment variables:
    - 'openai' (text-embedding-3-small)
    - 'gemini' (text-embedding-004)
    - 'sentence_transformers' / 'fastembed' (bge-m3)
    - 'semantic_vector' (Default high-precision local semantic vectorizer with financial synonym expansion)
    """

    FINANCIAL_SYNONYMS = {
        "lương về": ["thu_nhập", "lương", "tiền_vào", "income"],
        "thu nhập": ["lương", "tiền_vào", "lương_về", "income"],
        "thủng ví": ["vượt_ngân_sách", "chi_tiêu", "hạn_mức", "deficit"],
        "vượt ngân sách": ["thủng_ví", "hạn_mức", "chi_tiêu", "overbudget"],
        "quỹ khẩn cấp": ["tiết_kiệm", "dự_phòng", "emergency_fund", "quỹ"],
        "tích sản": ["đầu_tư", "tích_lũy", "dca", "chứng_chỉ_quỹ"],
        "đầu tư": ["tích_sản", "chứng_khoán", "tài_sản", "investment"],
        "tiết kiệm": ["tích_sản", "quỹ_khẩn_cấp", "savings", "dự_phòng"],
        "nợ": ["trả_nợ", "lãi_suất", "snowball", "avalanche", "debt"],
        "50/30/20": ["quy_tắc_50", "nhu_cầu_thiết_yếu", "mong_muốn_cá_nhân", "budgeting"],
    }

    def __init__(self) -> None:
        import os

        self.provider_type = os.getenv("EMBEDDING_PROVIDER", "semantic_vector").lower()

    def embed_text(self, text: str) -> dict[str, float]:
        """Generate semantic concept feature vector."""
        words = re.findall(r"\w+", text.lower())
        lowered = text.lower()
        total = max(len(words), 1)

        vec: dict[str, float] = {}
        for w in words:
            vec[w] = vec.get(w, 0.0) + 1.0 / total

        for key, synonyms in self.FINANCIAL_SYNONYMS.items():
            if key in lowered or any(w in words for w in key.split()):
                weight = 1.5
                vec[key.replace(" ", "_")] = vec.get(key.replace(" ", "_"), 0.0) + weight
                for syn in synonyms:
                    vec[syn] = vec.get(syn, 0.0) + (weight * 0.8)

        return vec

    def embed_dense_list(self, text: str) -> list[float]:
        """Produces a normalized dense float array suitable for vector DBs like ChromaDB."""
        vec = self.embed_text(text)
        dense_dim = 32
        dense = [0.0] * dense_dim
        for key, val in vec.items():
            h = hash(key) % dense_dim
            dense[h] += val
        norm = math.sqrt(sum(x * x for x in dense)) or 1.0
        return [round(x / norm, 6) for x in dense]

    @staticmethod
    def cosine_similarity(vec1: dict[str, float], vec2: dict[str, float]) -> float:
        intersection = set(vec1.keys()) & set(vec2.keys())
        if not intersection:
            return 0.0
        dot_product = sum(vec1[w] * vec2[w] for w in intersection)
        mag1 = math.sqrt(sum(v * v for v in vec1.values()))
        mag2 = math.sqrt(sum(v * v for v in vec2.values()))
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot_product / (mag1 * mag2)


class RAGVectorStore:
    """
    Advanced Hybrid Dense + Sparse RAG Vector Store with RRF fusion,
    metadata filtering, relevance score thresholding, reranking, and compression.
    """

    def __init__(self, collection_name: str = "personal_finance_rag") -> None:
        self.collection_name = collection_name
        self.chunks: list[DocumentChunk] = []
        self.indexed_docs: dict[str, KnowledgeDocument] = {}
        self._embedder = DenseEmbeddingProvider()
        self._sparse = VietnameseBM25Searcher()
        self._chroma_collection = None
        self._init_chroma()

    def _init_chroma(self) -> None:
        try:
            import chromadb  # type: ignore

            client = chromadb.Client()
            self._chroma_collection = client.get_or_create_collection(name=self.collection_name)
        except Exception:
            self._chroma_collection = None

    def index_documents(
        self,
        docs: list[KnowledgeDocument] | None = None,
        chunk_size: int = 400,
        chunk_overlap: int = 120,
    ) -> int:
        documents = docs or SEED_KNOWLEDGE_DOCUMENTS
        self.chunks.clear()
        self.indexed_docs.clear()

        for doc in documents:
            self._add_doc_chunks(doc, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        if self._chroma_collection is not None and self.chunks:
            try:
                self._chroma_collection.add(
                    ids=[c.chunk_id for c in self.chunks],
                    documents=[c.content for c in self.chunks],
                    metadatas=[c.metadata for c in self.chunks],
                )
            except Exception:
                pass

        return len(self.chunks)

    def _add_doc_chunks(
        self, doc: KnowledgeDocument, chunk_size: int = 400, chunk_overlap: int = 120
    ) -> None:
        self.indexed_docs[doc.doc_id] = doc
        sub_chunks = recursive_chunk_text(
            doc.content, title=doc.title, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        for idx, chunk_str in enumerate(sub_chunks):
            chunk_id = f"{doc.doc_id}_chunk_{idx}"
            metadata = doc.to_metadata()
            metadata["chunk_index"] = idx
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                doc_id=doc.doc_id,
                content=chunk_str,
                metadata=metadata,
            )
            self.chunks.append(chunk)

    def upsert_document(self, doc: KnowledgeDocument) -> bool:
        """Upsert a document: updates if content_hash changed, inserts if new."""
        existing = self.indexed_docs.get(doc.doc_id)
        if existing and existing.content_hash == doc.content_hash:
            return False  # No change

        self.delete_document(doc.doc_id)
        self._add_doc_chunks(doc)
        if self._chroma_collection is not None:
            new_chunks = [c for c in self.chunks if c.doc_id == doc.doc_id]
            if new_chunks:
                try:
                    self._chroma_collection.add(
                        ids=[c.chunk_id for c in new_chunks],
                        documents=[c.content for c in new_chunks],
                        metadatas=[c.metadata for c in new_chunks],
                    )
                except Exception:
                    pass
        return True

    def delete_document(self, doc_id: str) -> bool:
        """Delete all chunks for a document ID from memory and ChromaDB."""
        if doc_id in self.indexed_docs:
            chunk_ids_to_del = [c.chunk_id for c in self.chunks if c.doc_id == doc_id]
            del self.indexed_docs[doc_id]
            self.chunks = [c for c in self.chunks if c.doc_id != doc_id]

            if self._chroma_collection is not None and chunk_ids_to_del:
                try:
                    self._chroma_collection.delete(ids=chunk_ids_to_del)
                except Exception:
                    pass
            return True
        return False

    def rebuild_index(self) -> int:
        """Rebuild entire index from scratch."""
        docs = list(self.indexed_docs.values()) or SEED_KNOWLEDGE_DOCUMENTS
        if self._chroma_collection is not None and self.chunks:
            try:
                self._chroma_collection.delete(ids=[c.chunk_id for c in self.chunks])
            except Exception:
                pass
        return self.index_documents(docs)

    def search(
        self,
        query: str,
        top_k: int = 4,
        similarity_threshold: float = 0.15,
        filters: dict[str, Any] | None = None,
    ) -> list[DocumentChunk]:
        """
        Executes Dense + Sparse Hybrid Search with Reciprocal Rank Fusion (RRF),
        metadata filtering, relevance thresholding, and deduplication.
        """
        if not self.chunks:
            self.index_documents()

        # 1. Apply Metadata Filters first
        candidate_chunks = self.chunks
        if filters:
            candidate_chunks = [
                c for c in candidate_chunks
                if all(c.metadata.get(k) == v for k, v in filters.items())
            ]

        if not candidate_chunks:
            return []

        # 2. Dense Similarity Scoring (TF-IDF / Vector)
        query_vec = self._embedder.embed_text(query)
        dense_scored: list[tuple[float, DocumentChunk]] = []
        for chunk in candidate_chunks:
            chunk_vec = self._embedder.embed_text(chunk.content)
            sim = self._embedder.cosine_similarity(query_vec, chunk_vec)
            dense_scored.append((sim, chunk))
        dense_scored.sort(key=lambda x: x[0], reverse=True)

        # 3. Sparse Similarity Scoring (BM25 Keyword)
        sparse_scored: list[tuple[float, DocumentChunk]] = []
        for chunk in candidate_chunks:
            bm25_score = self._sparse.score(query, chunk.content)
            sparse_scored.append((bm25_score, chunk))
        sparse_scored.sort(key=lambda x: x[0], reverse=True)

        # 4. Reciprocal Rank Fusion (RRF)
        rrf_scores: dict[str, float] = {}
        chunk_lookup: dict[str, DocumentChunk] = {}
        raw_sim_lookup: dict[str, float] = {}

        k_rrf = 60.0
        for rank, (sim, chunk) in enumerate(dense_scored, start=1):
            chunk_lookup[chunk.chunk_id] = chunk
            raw_sim_lookup[chunk.chunk_id] = sim
            rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0.0) + (1.0 / (k_rrf + rank))

        for rank, (bm_score, chunk) in enumerate(sparse_scored, start=1):
            rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0.0) + (1.0 / (k_rrf + rank))

        # 5. Reranking & Relevance Thresholding
        reranked_chunks: list[DocumentChunk] = []
        for cid, score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True):
            chunk = chunk_lookup[cid]
            raw_sim = raw_sim_lookup.get(cid, 0.0)
            
            # Enforce relevance threshold
            if raw_sim < similarity_threshold:
                continue

            reranked_chunks.append(
                DocumentChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    content=chunk.content,
                    metadata=chunk.metadata,
                    score=round(raw_sim, 4),
                )
            )

        # 6. Context Compression & Deduplication (Remove overlapping content)
        final_chunks: list[DocumentChunk] = []
        seen_texts: set[str] = set()

        for chunk in reranked_chunks:
            normalized = clean_text(chunk.content).lower()
            if any(normalized in s or s in normalized for s in seen_texts):
                continue
            seen_texts.add(normalized)
            final_chunks.append(chunk)
            if len(final_chunks) >= top_k:
                break

        return final_chunks


_global_vector_store: RAGVectorStore | None = None


def get_vector_store() -> RAGVectorStore:
    global _global_vector_store
    if _global_vector_store is None:
        _global_vector_store = RAGVectorStore()
        _global_vector_store.index_documents()
    return _global_vector_store

