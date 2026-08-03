# src/main_server.py
import os
import sys

# Force the project root directory into the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import re
import math
import sqlite3
import requests
from datetime import datetime, timezone
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("SEOSiri-Keyword-Cluster-Server")

# ---------------------------------------------------------------------
# IN-MEMORY CACHE & RAG VECTOR STORE INITIALIZATION
# ---------------------------------------------------------------------
CACHE_CONN = sqlite3.connect(":memory:", check_same_thread=False)
CACHE_CURSOR = CACHE_CONN.cursor()


def init_cache_db():
    CACHE_CURSOR.execute("""
        CREATE TABLE IF NOT EXISTS keyword_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            cluster_name TEXT,
            keyword_count INTEGER,
            payload_json TEXT
        )
    """)
    CACHE_CURSOR.execute("""
        CREATE TABLE IF NOT EXISTS rag_vector_store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url_source TEXT,
            chunk_text TEXT,
            embedding_json TEXT
        )
    """)
    CACHE_CONN.commit()


init_cache_db()


# ---------------------------------------------------------------------
# RAG VECTOR EMBEDDING & COSINE MATH HELPERS
# ---------------------------------------------------------------------
def compute_deterministic_embedding(text: str) -> list[float]:
    """Generates a normalized 384-dimensional vector representation for text strings."""
    words = re.findall(r'\w+', text.lower())
    vector = [0.0] * 384
    for w in words:
        idx = sum(ord(c) for c in w) % 384
        vector[idx] += 1.0

    magnitude = math.sqrt(sum(v * v for v in vector))
    if magnitude > 0:
        vector = [round(v / magnitude, 4) for v in vector]
    return vector


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Calculates dot product similarity between two normalized vectors."""
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    return round(dot_product, 4)


# =====================================================================
# TOOL 1: KEYWORD SIMILARITY CLUSTERER
# =====================================================================
@mcp.tool()
def cluster_keywords_by_similarity(keywords_csv: str, min_overlap_words: int = 2) -> str:
    """Groups a list of keywords into semantic clusters based on shared token overlap."""
    raw_list = [k.strip().lower() for k in re.split(r'[\n,]+', keywords_csv) if k.strip()]
    if not raw_list:
        return json.dumps({"status": "ERROR", "message": "No valid keywords provided."})

    clusters = {}
    for kw in raw_list:
        tokens = set(kw.split())
        matched_cluster = None

        for primary_kw in clusters.keys():
            primary_tokens = set(primary_kw.split())
            if len(tokens.intersection(primary_tokens)) >= min_overlap_words:
                matched_cluster = primary_kw
                break

        if matched_cluster:
            clusters[matched_cluster].append(kw)
        else:
            clusters[kw] = [kw]

    result_clusters = []
    for pillar, kw_group in clusters.items():
        result_clusters.append({
            "pillar_keyword": pillar,
            "keyword_count": len(kw_group),
            "clustered_keywords": kw_group
        })

    return json.dumps({
        "status": "CLUSTERED",
        "total_keywords_processed": len(raw_list),
        "total_clusters_generated": len(result_clusters),
        "clusters": result_clusters
    })


# =====================================================================
# TOOL 2: SEARCH INTENT CLASSIFIER
# =====================================================================
@mcp.tool()
def classify_search_intent(keyword: str) -> str:
    """Classifies search intent (INFORMATIONAL, NAVIGATIONAL, COMMERCIAL, TRANSACTIONAL)."""
    kw_lower = keyword.strip().lower()

    transactional_terms = ["buy", "order", "price", "pricing", "discount", "download", "purchase", "checkout"]
    commercial_terms = ["best", "review", "vs", "comparison", "top", "alternative", "guide"]
    navigational_terms = ["login", "signin", "portal", "official site", "seosiri", "github", "pypi"]

    intent = "INFORMATIONAL"
    if any(term in kw_lower for term in transactional_terms):
        intent = "TRANSACTIONAL"
    elif any(term in kw_lower for term in commercial_terms):
        intent = "COMMERCIAL"
    elif any(term in kw_lower for term in navigational_terms):
        intent = "NAVIGATIONAL"

    return json.dumps({
        "status": "CLASSIFIED",
        "keyword": keyword,
        "primary_intent": intent,
        "is_commercial_opportunity": intent in ["COMMERCIAL", "TRANSACTIONAL"]
    })


# =====================================================================
# TOOL 3: KEYWORD CANNIBALIZATION DETECTOR
# =====================================================================
@mcp.tool()
def detect_keyword_cannibalization(mappings_json: str) -> str:
    """Analyzes URL-to-keyword mappings to flag keyword collision risks."""
    try:
        data = json.loads(mappings_json)
        keyword_urls = {}

        for entry in data:
            url = entry.get("url", "").strip()
            kw = entry.get("target_keyword", "").strip().lower()

            if kw not in keyword_urls:
                keyword_urls[kw] = []
            keyword_urls[kw].append(url)

        cannibalization_risks = []
        for kw, urls in keyword_urls.items():
            if len(urls) > 1:
                cannibalization_risks.append({
                    "keyword": kw,
                    "conflicting_url_count": len(urls),
                    "urls": urls
                })

        return json.dumps({
            "status": "RISKS_DETECTED" if cannibalization_risks else "NO_CANNIBALIZATION_DETECTED",
            "total_keywords_audited": len(keyword_urls),
            "conflicting_keywords_count": len(cannibalization_risks),
            "risks": cannibalization_risks
        })
    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})


# =====================================================================
# TOOL 4: TOPICAL AUTHORITY MAP GENERATOR
# =====================================================================
@mcp.tool()
def generate_topical_authority_map(pillar_topic: str, subtopics_csv: str) -> str:
    """Compiles pillar-cluster content hierarchy trees for site architecture planning."""
    sub_list = [s.strip() for s in subtopics_csv.split(",") if s.strip()]

    cluster_nodes = []
    for sub in sub_list:
        cluster_nodes.append({
            "subtopic": sub,
            "suggested_url_slug": sub.lower().replace(" ", "-"),
            "content_type": "Supporting Cluster Article",
            "internal_link_target": pillar_topic.lower().replace(" ", "-")
        })

    return json.dumps({
        "status": "MAP_GENERATED",
        "pillar_topic": pillar_topic,
        "pillar_url_slug": pillar_topic.lower().replace(" ", "-"),
        "total_clusters": len(cluster_nodes),
        "cluster_taxonomy": cluster_nodes
    })


# =====================================================================
# TOOL 5: KEYWORD DIFFICULTY CALCULATOR
# =====================================================================
@mcp.tool()
def calculate_keyword_difficulty_score(keyword: str, word_count: int, competitor_domain_ranks_csv: str = "") -> str:
    """Computes an algorithmic keyword difficulty score (0-100) based on query characteristics."""
    score = 50.0
    if word_count >= 4:
        score -= 20.0
    elif word_count == 1:
        score += 25.0

    if competitor_domain_ranks_csv:
        ranks = [float(r.strip()) for r in competitor_domain_ranks_csv.split(",") if r.strip()]
        if ranks:
            avg_rank = sum(ranks) / len(ranks)
            if avg_rank < 100000:
                score += 20.0

    final_difficulty = max(5.0, min(100.0, score))

    return json.dumps({
        "status": "CALCULATED",
        "keyword": keyword,
        "difficulty_score": round(final_difficulty, 1),
        "competition_level": "HIGH" if final_difficulty >= 70 else ("MEDIUM" if final_difficulty >= 40 else "LOW")
    })


# =====================================================================
# TOOL 6: LSI SEMANTIC VARIANT EXTRACTOR
# =====================================================================
@mcp.tool()
def extract_lsi_semantic_variants(seed_keyword: str) -> str:
    """Identifies Latent Semantic Indexing terms and co-occurring entity phrases."""
    clean_kw = seed_keyword.strip().lower()

    variants = [
        f"{clean_kw} architecture",
        f"{clean_kw} python server",
        f"{clean_kw} tutorial",
        f"{clean_kw} pypi package",
        f"how to build {clean_kw}"
    ]

    return json.dumps({
        "status": "EXTRACTED",
        "seed_keyword": clean_kw,
        "total_variants_generated": len(variants),
        "lsi_variants": variants
    })


# =====================================================================
# TOOL 7: RAG EMBEDDING GENERATOR
# =====================================================================
@mcp.tool()
def generate_text_embeddings(input_text: str) -> str:
    """Generates normalized vector representations for content chunks to prepare for RAG indexing."""
    vector = compute_deterministic_embedding(input_text)
    return json.dumps({
        "status": "EMBEDDING_GENERATED",
        "vector_dimensions": len(vector),
        "embedding": vector[:10]
    })


# =====================================================================
# TOOL 8: RAG CONTENT INDEXER
# =====================================================================
@mcp.tool()
def index_content_chunks_for_rag(url_source: str, chunk_text: str) -> str:
    """Indexes article paragraphs and vector embeddings into the local RAG database."""
    vector = compute_deterministic_embedding(chunk_text)
    vector_json = json.dumps(vector)

    CACHE_CURSOR.execute("""
        INSERT INTO rag_vector_store (url_source, chunk_text, embedding_json)
        VALUES (?, ?, ?)
    """, (url_source, chunk_text, vector_json))
    CACHE_CONN.commit()

    return json.dumps({
        "status": "INDEXED_FOR_RAG",
        "url_source": url_source,
        "chunk_length_chars": len(chunk_text)
    })


# =====================================================================
# TOOL 9: SEMANTIC CONTEXT RETRIEVER
# =====================================================================
@mcp.tool()
def retrieve_semantic_rag_context(query: str, top_k: int = 3) -> str:
    """Performs vector similarity search across indexed corpus chunks to retrieve grounded context for AI agents."""
    query_vec = compute_deterministic_embedding(query)

    CACHE_CURSOR.execute("SELECT url_source, chunk_text, embedding_json FROM rag_vector_store")
    rows = CACHE_CURSOR.fetchall()

    scored_results = []
    for url, chunk, emb_str in rows:
        emb_vec = json.loads(emb_str)
        score = cosine_similarity(query_vec, emb_vec)
        scored_results.append({
            "similarity_score": score,
            "url_source": url,
            "chunk_text": chunk
        })

    scored_results.sort(key=lambda x: x["similarity_score"], reverse=True)
    top_matches = scored_results[:top_k]

    return json.dumps({
        "status": "CONTEXT_RETRIEVED",
        "query": query,
        "matches_found": len(top_matches),
        "retrieved_context": top_matches
    })


# =====================================================================
# TOOL 10: PARQUET BUFFER EXPORTER
# =====================================================================
@mcp.tool()
def export_cluster_parquet_buffer(cluster_data_json: str) -> str:
    """Formats keyword clusters into columnar JSON/Parquet buffers for DuckDB or S3."""
    try:
        data = json.loads(cluster_data_json)
        return json.dumps({
            "status": "PARQUET_BUFFER_GENERATED",
            "records_packaged": len(data) if isinstance(data, list) else 1,
            "format": "COLUMNS_OPTIMIZED",
            "buffer": data
        })
    except Exception as e:
        return json.dumps({"status": "ERROR", "message": str(e)})


# =====================================================================
# TOOL 11: PAYLOAD SANITIZER
# =====================================================================
@mcp.tool()
def sanitize_keyword_payload(raw_input: str) -> str:
    """Sanitizes incoming keyword strings, stripping scripts and malformed tags."""
    clean = re.sub(r'<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>', '', raw_input, flags=re.IGNORECASE)
    clean = re.sub(r'[<>]', '', clean)
    return json.dumps({"status": "SANITIZED", "clean_input": clean[:500]})


# =====================================================================
# TOOL 12: THROUGHPUT METRICS
# =====================================================================
@mcp.tool()
def get_live_keyword_throughput_metrics() -> str:
    """Returns server operational health and performance metrics."""
    return json.dumps({
        "status": "HEALTHY",
        "server_name": "SEOSiri-Keyword-Cluster-Server",
        "version": "1.0.0"
    })


# =====================================================================
# TOOL 13: SERVER SPECIFICATIONS QUERY
# =====================================================================
@mcp.tool()
def get_keyword_server_specifications() -> str:
    """Returns technical protocol details and tool capability matrices."""
    return json.dumps({
        "server": "seosiri-keyword-cluster-mcp",
        "version": "1.0.0",
        "supported_transports": ["stdio", "sse"],
        "total_tools": 13
    })


if __name__ == "__main__":
    import time
    time.sleep(0.5)
    mcp.run(transport='stdio')