"""V5 tools/semantic_search.py — Block T v4 semantic_search tool.

PORT_LOG: #103. ADR-038.

Lightweight semantic-search via on-disk embedding index. v4 used
sentence-transformers; v5 falls back to a TF-IDF cosine-similarity
implementation when sklearn is available, else returns a clear error.

Two actions:
- "index": (re)build the index from files under `path`.
- "search": query the latest index for top-k matches.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .registry import build_tool, register


# Process-global index — keyed by index path. Tests can clear via
# _reset_for_tests.
_INDEX_CACHE: Dict[str, Any] = {}


def _reset_for_tests() -> None:
    _INDEX_CACHE.clear()


def _build_index(path: str) -> Dict[str, Any]:
    """Build a TF-IDF index over text files under `path`."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError:
        raise RuntimeError("sklearn not installed; install via `pip install scikit-learn`")

    files: List[str] = []
    docs: List[str] = []
    p = Path(path)
    if not p.is_dir() and not p.is_file():
        return {"files": [], "docs": [], "vectorizer": None, "matrix": None}
    if p.is_file():
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            files.append(str(p))
            docs.append(text)
        except OSError:
            pass
    else:
        for fp in p.rglob("*"):
            if not fp.is_file():
                continue
            if fp.suffix.lower() not in (".py", ".md", ".txt", ".rst", ".html"):
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
                files.append(str(fp))
                docs.append(text)
            except OSError:
                continue

    if not docs:
        return {"files": [], "docs": [], "vectorizer": None, "matrix": None}

    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    matrix = vectorizer.fit_transform(docs)
    return {"files": files, "docs": docs, "vectorizer": vectorizer, "matrix": matrix}


def _semantic_search_executor(args: Dict[str, Any], context: Optional[Dict] = None) -> str:
    action = (args.get("action") or "search").lower()
    path = args.get("path") or "."

    # Codex iter-1 MEDIUM: support v4 `status` action.
    if action == "status":
        if not _INDEX_CACHE:
            return "(no index built yet)"
        lines = []
        for ipath, idx in _INDEX_CACHE.items():
            lines.append(f"{ipath}\t{len(idx.get('files', []))} files")
        return "\n".join(lines)

    if action == "index":
        try:
            idx = _build_index(path)
        except RuntimeError as exc:
            return f"Error: {exc}"
        _INDEX_CACHE[str(path)] = idx
        return f"Indexed {len(idx['files'])} files from {path}."

    if action == "search":
        query = str(args.get("query") or "").strip()
        if not query:
            return "Error: query is required for search action"
        # Find the most recently indexed path that contains the query path
        # (or just use the last one if exact match doesn't exist).
        idx = _INDEX_CACHE.get(str(path))
        if idx is None and _INDEX_CACHE:
            # Fall back to any recent index.
            idx = list(_INDEX_CACHE.values())[-1]
        if idx is None:
            return "Error: no index built; call action='index' first."
        if not idx.get("vectorizer") or not idx.get("files"):
            return "(no results — index empty)"
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            qvec = idx["vectorizer"].transform([query])
            sims = cosine_similarity(qvec, idx["matrix"])[0]
            # Codex iter-1 MEDIUM: accept BOTH v4 `top_k` and v5 `k`.
            k = int(args.get("top_k") or args.get("k") or 5)
            ranked = sorted(
                zip(idx["files"], sims), key=lambda t: t[1], reverse=True,
            )[:k]
            lines = [f"{f}\t{s:.3f}" for f, s in ranked if s > 0.0]
            if not lines:
                return "(no matches)"
            return "\n".join(lines)
        except Exception as exc:  # noqa: BLE001
            return f"Error: {type(exc).__name__}: {exc}"

    return f"Error: unknown action '{action}'. Use 'index' or 'search'."


_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["index", "search", "status"]},
        "path": {"type": "string", "description": "Directory or file path."},
        "query": {"type": "string", "description": "Required for search action."},
        "k": {"type": "integer", "default": 5, "description": "Top-k results (v5 alias)."},
        "top_k": {"type": "integer", "description": "Top-k results (v4 advertised name)."},
    },
    "required": ["action"],
}


def _register():
    from .registry import find_tool_by_name, all_registered
    if find_tool_by_name(all_registered(), "semantic_search") is not None:
        return
    register(build_tool(
        name="semantic_search",
        description="Build / query a TF-IDF semantic-search index over a directory tree.",
        input_schema=_SCHEMA,
        execute=_semantic_search_executor,
        requires_approval=False,
        should_defer=True,
        max_result_size_chars=4000,
    ))
