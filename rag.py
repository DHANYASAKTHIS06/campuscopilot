"""
CampusCopilot — RAG pipeline
PDF extraction → chunking → ChromaDB indexing → hybrid search → security scan
"""
import os, math, pymupdf as fitz, chromadb, difflib, re, json
from collections import Counter
from pathlib import Path

CHROMA_PATH  = os.getenv("CHROMA_PERSIST_DIRECTORY", "data/chroma")
UPLOAD_PATH  = os.getenv("DOCUMENT_STORAGE_PATH",    "data/uploads")
os.makedirs(CHROMA_PATH, exist_ok=True)
os.makedirs(UPLOAD_PATH, exist_ok=True)

_client = None
_col    = None
_bm25_cache = None   # {"docs": [...], "metas": [...], "idf": {...}, "tf": [...], "dl": [...], "avgdl": float}

def _invalidate_bm25():
    global _bm25_cache
    _bm25_cache = None

def _get_collection():
    global _client, _col
    if _col is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _col    = _client.get_or_create_collection(
            "campus", metadata={"hnsw:space": "cosine"}
        )
    return _col

# ─── PDF extraction ──────────────────────────────────────────────────────────────
def extract_pdf(data: bytes) -> list[tuple[int, str]]:
    """Return [(page_no, text), …]. Skips blank pages."""
    doc = fitz.open(stream=data, filetype="pdf")
    pages = []
    for i, page in enumerate(doc):
        txt = page.get_text().strip()
        if txt:
            pages.append((i + 1, txt))
    return pages

def extract_pdf_full(data: bytes, filename: str = "") -> dict:
    """Rich extraction: pages, page_count, has_tables, metadata."""
    doc   = fitz.open(stream=data, filetype="pdf")
    pages = []
    has_tables = False
    for i, page in enumerate(doc):
        txt = page.get_text().strip()
        # basic table heuristic: multiple tab-separated columns
        if "\t" in txt or "  |  " in txt:
            has_tables = True
        if txt:
            pages.append({"page": i + 1, "text": txt})
    return {
        "filename":   filename,
        "page_count": len(doc),
        "has_tables": has_tables,
        "pages":      pages,
        "metadata":   doc.metadata or {},
    }

def save_pdf(data: bytes, filename: str) -> str:
    """Save uploaded PDF bytes to UPLOAD_PATH. Returns absolute file path."""
    safe = re.sub(r"[^\w\-. ]", "_", filename)
    path = os.path.join(UPLOAD_PATH, safe)
    with open(path, "wb") as f:
        f.write(data)
    return path

# ─── chunking ───────────────────────────────────────────────────────────────────
def chunk(text: str, size: int = 800, overlap: int = 120) -> list[str]:
    out, i = [], 0
    while i < len(text):
        out.append(text[i : i + size])
        i += size - overlap
    return out

# ─── indexing ───────────────────────────────────────────────────────────────────
def ingest(name: str, pages: list[tuple[int, str]]) -> int:
    """Index pages from (page_no, text) list. Returns chunk count."""
    col = _get_collection()
    # remove old chunks for this document
    try:
        col.delete(where={"source": name})
    except Exception:
        pass
    ids, docs, metas = [], [], []
    for pno, txt in pages:
        for j, ch in enumerate(chunk(txt)):
            ids.append(f"{name}||{pno}||{j}")
            docs.append(ch)
            metas.append({"source": name, "page": pno})
    if docs:
        col.add(ids=ids, documents=docs, metadatas=metas)
    _invalidate_bm25()
    return len(docs)

# ─── BM25 + Hybrid Search (RRF + Lexical Reranking) ────────────────────────────
def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())

def _get_bm25_index():
    global _bm25_cache
    if _bm25_cache is not None:
        return _bm25_cache
    col = _get_collection()
    if col.count() == 0:
        return None
    data = col.get(include=["documents", "metadatas"])
    docs = data.get("documents") or []
    metas = data.get("metadatas") or []
    ids = data.get("ids") or []
    if not docs:
        return None

    tokenized = [_tokenize(d) for d in docs]
    n_docs = len(tokenized)
    dl = [len(t) for t in tokenized]
    avgdl = sum(dl) / n_docs if n_docs else 1.0

    df = Counter()
    tf_list = []
    for tokens in tokenized:
        c = Counter(tokens)
        tf_list.append(c)
        for term in c:
            df[term] += 1

    idf = {
        term: math.log((n_docs - freq + 0.5) / (freq + 0.5) + 1.0)
        for term, freq in df.items()
    }
    _bm25_cache = {
        "ids": ids, "docs": docs, "metas": metas,
        "idf": idf, "tf": tf_list, "dl": dl, "avgdl": avgdl,
    }
    return _bm25_cache

def bm25_search(query: str, k: int = 15) -> list[dict]:
    """Keyword search using BM25Okapi over all indexed chunks."""
    idx = _get_bm25_index()
    if not idx:
        return []
    q_tokens = _tokenize(query)
    if not q_tokens:
        return []

    k1, b = 1.5, 0.75
    avgdl = idx["avgdl"] or 1.0
    scored = []
    for i, (doc_id, text, meta) in enumerate(zip(idx["ids"], idx["docs"], idx["metas"])):
        tf = idx["tf"][i]
        dl = idx["dl"][i]
        score = 0.0
        for term in q_tokens:
            if term not in tf:
                continue
            f = tf[term]
            idf = idx["idf"].get(term, 0.0)
            denom = f + k1 * (1.0 - b + b * dl / avgdl)
            score += idf * (f * (k1 + 1.0)) / (denom or 1.0)
        if score > 0:
            scored.append({
                "id": doc_id,
                "text": text,
                "source": meta.get("source", ""),
                "page": meta.get("page", 1),
                "bm25_score": score,
            })
    scored.sort(key=lambda x: x["bm25_score"], reverse=True)
    return scored[:k]

def search(query: str, k: int = 6) -> list[dict]:
    """
    Hybrid retrieval: ChromaDB vector search + BM25 keyword search,
    combined via Reciprocal Rank Fusion (RRF) and lexical reranking.
    """
    col = _get_collection()
    total = col.count()
    if total == 0:
        return []

    fetch_k = min(max(k * 3, 15), total)

    # 1. Vector search (ChromaDB)
    r = col.query(query_texts=[query], n_results=fetch_k,
                  include=["documents", "metadatas", "distances"])
    vec_ids = r.get("ids", [[]])[0]
    vec_docs = r.get("documents", [[]])[0]
    vec_metas = r.get("metadatas", [[]])[0]
    vec_dists = r.get("distances", [[0] * len(vec_docs)])[0]

    candidates = {}
    rrf_k = 60
    for rank, (doc_id, d, m, dist) in enumerate(zip(vec_ids, vec_docs, vec_metas, vec_dists), 1):
        candidates[doc_id] = {
            "text": d,
            "source": m["source"],
            "page": m["page"],
            "vec_sim": round(1 - dist, 4),
            "rrf": 1.0 / (rrf_k + rank),
        }

    # 2. BM25 keyword search
    bm25_hits = bm25_search(query, k=fetch_k)
    for rank, hit in enumerate(bm25_hits, 1):
        doc_id = hit["id"]
        if doc_id not in candidates:
            candidates[doc_id] = {
                "text": hit["text"],
                "source": hit["source"],
                "page": hit["page"],
                "vec_sim": 0.0,
                "rrf": 0.0,
            }
        candidates[doc_id]["rrf"] += 1.0 / (rrf_k + rank)

    # 3. Lexical reranking (term overlap + exact phrase boost)
    q_terms = set(_tokenize(query))
    q_lower = query.lower().strip()
    ranked = []
    for item in candidates.values():
        doc_terms = set(_tokenize(item["text"]))
        overlap = len(q_terms & doc_terms) / len(q_terms) if q_terms else 0.0
        phrase_boost = 0.02 if len(q_lower) > 3 and q_lower in item["text"].lower() else 0.0
        final_score = item["rrf"] + 0.015 * overlap + phrase_boost
        ranked.append({
            "text": item["text"],
            "source": item["source"],
            "page": item["page"],
            "score": round(final_score, 4),
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:k]

def search_by_source(source: str, query: str, k: int = 4) -> list[dict]:
    """Search within a specific document only."""
    col = _get_collection()
    if col.count() == 0:
        return []
    n   = min(k, col.count())
    r   = col.query(
        query_texts=[query], n_results=n,
        where={"source": source}
    )
    return [
        {"text": d, "source": m["source"], "page": m["page"]}
        for d, m in zip(r["documents"][0], r["metadatas"][0])
    ]

# ─── document management ─────────────────────────────────────────────────────────
def delete_document(name: str):
    """Remove all indexed chunks for a document."""
    col = _get_collection()
    try:
        col.delete(where={"source": name})
    except Exception:
        pass
    _invalidate_bm25()

def count() -> int:
    return _get_collection().count()

def get_sources() -> list[str]:
    col = _get_collection()
    if col.count() == 0:
        return []
    r = col.get(include=["metadatas"])
    seen = set()
    for m in r["metadatas"]:
        seen.add(m.get("source", ""))
    return sorted(seen - {""})

# ─── diff ────────────────────────────────────────────────────────────────────────
def diff_text(old: str, new: str) -> list[str]:
    d = difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0)
    return [line for line in d if line[:1] in "+-" and not line.startswith(("+++", "---"))]

# ─── security scan ───────────────────────────────────────────────────────────────
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"you\s+are\s+now\s+a",
    r"disregard\s+(all\s+)?",
    r"forget\s+(all\s+)?(your|previous)",
    r"new\s+instructions?:",
    r"act\s+as\s+(an?\s+)?(ai|assistant|bot|system)",
    r"system\s+prompt",
    r"reveal\s+(your\s+)?(instructions?|prompt|api\s+key)",
    r"print\s+(your\s+)?(instructions?|system|prompt)",
    r"<\s*script\b",
    r"<!--.*?-->",    # hidden HTML comments
    r"\[INST\]",      # Llama instruction injection
    r"<<SYS>>",
]

def security_scan(text: str) -> dict:
    """Scan document text for prompt-injection patterns."""
    issues = []
    lower  = text.lower()
    for pat in _INJECTION_PATTERNS:
        m = re.search(pat, lower)
        if m:
            issues.append(f"Suspicious pattern: '{m.group()}' at position {m.start()}")
    return {"safe": len(issues) == 0, "issues": issues}
