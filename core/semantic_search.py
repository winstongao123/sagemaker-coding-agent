"""
Semantic Search - Code search using Bedrock Titan Embeddings
"""
import boto3
import json
import os
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class CodeChunk:
    """Represents a chunk of code for indexing."""

    file_path: str
    start_line: int
    end_line: int
    content: str
    embedding: Optional[List[float]] = None


class SemanticSearch:
    """Semantic code search using Bedrock Titan Embeddings."""

    def __init__(self, region: str = "ap-southeast-2", index_path: str = "./.code_index"):
        """
        Initialize semantic search.

        Args:
            region: AWS region for Bedrock
            index_path: Path to store the search index
        """
        self.region = region
        self.index_path = index_path
        self.client = boto3.client("bedrock-runtime", region_name=region)
        self.model_id = "amazon.titan-embed-text-v2:0"
        self.chunks: List[CodeChunk] = []

    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text.

        Args:
            text: Text to embed (max 8000 chars)

        Returns:
            Embedding vector
        """
        # Truncate to Titan limit
        text = text[:8000]

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps({"inputText": text}),
            contentType="application/json",
        )
        result = json.loads(response["body"].read())
        return result["embedding"]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a_arr = np.array(a)
        b_arr = np.array(b)
        return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))

    def index_codebase(
        self,
        root_dir: str,
        extensions: Optional[List[str]] = None,
        chunk_size: int = 50,
    ) -> int:
        """
        Index all code files in directory.

        Args:
            root_dir: Root directory to index
            extensions: File extensions to include
            chunk_size: Lines per chunk

        Returns:
            Number of chunks indexed
        """
        extensions = extensions or [".py", ".js", ".ts", ".tsx", ".java", ".go", ".rs", ".c", ".cpp", ".h"]
        self.chunks = []

        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Skip hidden directories
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]

            for filename in filenames:
                if not any(filename.endswith(ext) for ext in extensions):
                    continue

                filepath = os.path.join(dirpath, filename)
                self._index_file(filepath, chunk_size)

        # Save index
        self._save_index()
        return len(self.chunks)

    def _index_file(self, filepath: str, chunk_size: int = 50):
        """
        Split file into chunks and index each.

        Args:
            filepath: Path to file
            chunk_size: Lines per chunk
        """
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except IOError:
            return

        # Split into chunks
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i : i + chunk_size]
            content = "".join(chunk_lines)

            # Skip tiny chunks
            if len(content.strip()) < 50:
                continue

            chunk = CodeChunk(
                file_path=filepath,
                start_line=i + 1,
                end_line=i + len(chunk_lines),
                content=content,
            )

            # Get embedding
            try:
                chunk.embedding = self._get_embedding(content)
                self.chunks.append(chunk)
            except Exception as e:
                print(f"Warning: Failed to embed {filepath}: {e}")

    def _save_index(self):
        """Save index to disk."""
        os.makedirs(self.index_path, exist_ok=True)

        data = []
        for chunk in self.chunks:
            data.append(
                {
                    "file_path": chunk.file_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "content": chunk.content,
                    "embedding": chunk.embedding,
                }
            )

        with open(os.path.join(self.index_path, "chunks.json"), "w") as f:
            json.dump(data, f)

    def _load_index(self) -> bool:
        """
        Load index from disk.

        Returns:
            True if loaded successfully
        """
        path = os.path.join(self.index_path, "chunks.json")
        if not os.path.exists(path):
            return False

        try:
            with open(path) as f:
                data = json.load(f)

            self.chunks = [CodeChunk(**d) for d in data]
            return True
        except (json.JSONDecodeError, TypeError):
            return False

    def search(self, query: str, top_k: int = 5) -> List[Tuple[CodeChunk, float]]:
        """
        Search for code matching query.

        Args:
            query: Natural language search query
            top_k: Number of results to return

        Returns:
            List of (chunk, similarity_score) tuples
        """
        if not self.chunks:
            if not self._load_index():
                return []

        # Get query embedding
        query_embedding = self._get_embedding(query)

        # Calculate similarities
        results = []
        for chunk in self.chunks:
            if chunk.embedding:
                sim = self._cosine_similarity(query_embedding, chunk.embedding)
                results.append((chunk, sim))

        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def format_results(self, results: List[Tuple[CodeChunk, float]]) -> str:
        """
        Format search results for display.

        Args:
            results: List of (chunk, score) tuples

        Returns:
            Formatted string
        """
        if not results:
            return "No matching code found. Try indexing the codebase first with index_codebase()."

        output = []
        for chunk, score in results:
            output.append(
                f"\n### {chunk.file_path}:{chunk.start_line}-{chunk.end_line} (score: {score:.3f})"
            )
            output.append("```")
            # Truncate long content
            content = chunk.content[:500]
            if len(chunk.content) > 500:
                content += "\n... (truncated)"
            output.append(content)
            output.append("```")

        return "\n".join(output)

    def is_indexed(self) -> bool:
        """Check if codebase is indexed."""
        path = os.path.join(self.index_path, "chunks.json")
        return os.path.exists(path)

    def get_index_stats(self) -> Dict:
        """Get statistics about the index."""
        if not self.chunks:
            self._load_index()

        if not self.chunks:
            return {"indexed": False, "chunks": 0, "files": 0}

        files = set(c.file_path for c in self.chunks)
        return {"indexed": True, "chunks": len(self.chunks), "files": len(files)}
