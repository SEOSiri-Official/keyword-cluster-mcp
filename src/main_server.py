# Add to src/main_server.py

# Vector Store Initialization
CACHE_CURSOR.execute("""
    CREATE TABLE IF NOT EXISTS rag_vector_store (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url_source TEXT,
        chunk_text TEXT,
        embedding_json TEXT
    )
""")
CACHE_CONN.commit()


def compute_deterministic_embedding(text: str) -> list[float]:
    """Generates a normalized 384-dimensional vector representation for text strings."""
    # Deterministic term frequency hash vector fallback
    words = re.findall(r'\w+', text.lower())
    vector = [0.0] * 384
    for w in words:
        idx = sum(ord(c) for c in w) % 384
        vector[idx] += 1.0
    
    # L2 Normalization
    magnitude = math.sqrt(sum(v * v for v in vector))
    if magnitude > 0:
        vector = [round(v / magnitude, 4) for v in vector]
    return vector


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Calculates dot product similarity between two normalized vectors."""
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    return round(dot_product, 4)


# ---------------------------------------------------------------------
# TOOL 11: TEXT EMBEDDING GENERATOR
# ---------------------------------------------------------------------
@mcp.tool()
def generate_text_embeddings(input_text: str) -> str:
    """
    RAG Tool: Generates normalized vector representations for content chunks to prepare for RAG indexing.

    Args:
        input_text: Text snippet or article paragraph to embed.
    """
    vector = compute_deterministic_embedding(input_text)
    return json.dumps({
        "status": "EMBEDDING_GENERATED",
        "vector_dimensions": len(vector),
        "embedding": vector[:10]  # Returns preview of vector
    })


# ---------------------------------------------------------------------
# TOOL 12: RAG CONTENT INDEXER
# ---------------------------------------------------------------------
@mcp.tool()
def index_content_chunks_for_rag(url_source: str, chunk_text: str) -> str:
    """
    RAG Tool: Indexes article paragraphs and vector embeddings into the local RAG database.

    Args:
        url_source: Source URL (e.g., 'https://seosiri.com/2026/08/keyword-cluster-mcp.html').
        chunk_text: Paragraph or section content to index.
    """
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


# ---------------------------------------------------------------------
# TOOL 13: SEMANTIC CONTEXT RETRIEVER
# ---------------------------------------------------------------------
@mcp.tool()
def retrieve_semantic_rag_context(query: str, top_k: int = 3) -> str:
    """
    RAG Tool: Performs vector similarity search across indexed corpus chunks to retrieve grounded context for AI agents.

    Args:
        query: User search query or prompt to retrieve relevant context for.
        top_k: Number of most relevant content chunks to return (default: 3).
    """
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

    # Sort descending by similarity score
    scored_results.sort(key=lambda x: x["similarity_score"], reverse=True)
    top_matches = scored_results[:top_k]

    return json.dumps({
        "status": "CONTEXT_RETRIEVED",
        "query": query,
        "matches_found": len(top_matches),
        "retrieved_context": top_matches
    })