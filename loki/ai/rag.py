"""FAISS-based RAG engine."""

from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from ..core.types import CodeChunk, Language


class RAGEngine:
    """Manages FAISS index for code retrieval."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.index_dir = cache_dir / "embeddings"
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = None
        self.chunks: list[CodeChunk] = []

    def build_index(self, code_chunks: list[CodeChunk]) -> None:
        """Build FAISS index from code chunks."""
        if not code_chunks:
            return

        self.chunks = code_chunks
        texts = [chunk.content for chunk in code_chunks]
        embeddings = self.embedder.encode(texts, convert_to_numpy=True)

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype(np.float32))

        self._save_index()

    def query(self, question: str, top_k: int = 5) -> list[CodeChunk]:
        """Query index for relevant code chunks."""
        if self.index is None:
            self._load_index()

        if self.index is None or self.index.ntotal == 0:
            return []

        question_embedding = self.embedder.encode([question], convert_to_numpy=True)
        distances, indices = self.index.search(
            question_embedding.astype(np.float32), min(top_k, self.index.ntotal)
        )

        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self.chunks):
                results.append(self.chunks[idx])

        return results

    def chunk_code(self, file_path: str, content: str, language: Language) -> list[CodeChunk]:
        """Split code into chunks."""
        lines = content.split("\n")
        chunk_size = 50
        overlap = 10
        chunks = []

        for i in range(0, len(lines), chunk_size - overlap):
            end = min(i + chunk_size, len(lines))
            chunk_content = "\n".join(lines[i:end])

            if chunk_content.strip():
                chunks.append(CodeChunk(
                    file_path=file_path,
                    start_line=i + 1,
                    end_line=end,
                    content=chunk_content,
                    language=language,
                ))

        return chunks

    def _save_index(self) -> None:
        """Save FAISS index to disk."""
        if self.index is None:
            return

        self.index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_dir / "index.faiss"))

        import json
        chunks_data = [
            {
                "file_path": c.file_path,
                "start_line": c.start_line,
                "end_line": c.end_line,
                "content": c.content,
                "language": c.language.value,
            }
            for c in self.chunks
        ]
        with open(self.index_dir / "chunks.json", "w") as f:
            json.dump(chunks_data, f)

    def _load_index(self) -> None:
        """Load FAISS index from disk."""
        index_path = self.index_dir / "index.faiss"
        chunks_path = self.index_dir / "chunks.json"

        if not index_path.exists() or not chunks_path.exists():
            return

        self.index = faiss.read_index(str(index_path))

        import json
        with open(chunks_path) as f:
            chunks_data = json.load(f)

        self.chunks = [
            CodeChunk(
                file_path=c["file_path"],
                start_line=c["start_line"],
                end_line=c["end_line"],
                content=c["content"],
                language=Language(c["language"]),
            )
            for c in chunks_data
        ]
