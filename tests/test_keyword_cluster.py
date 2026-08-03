# tests/test_keyword_cluster.py
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main_server import (
    cluster_keywords_by_similarity,
    classify_search_intent,
    detect_keyword_cannibalization,
    generate_topical_authority_map,
    calculate_keyword_difficulty_score,
    extract_lsi_semantic_variants,
    generate_text_embeddings,
    index_content_chunks_for_rag,
    retrieve_semantic_rag_context,
    export_cluster_parquet_buffer,
    sanitize_keyword_payload,
    get_live_keyword_throughput_metrics,
    get_keyword_server_specifications
)


def test_1_cluster_similarity():
    kw_list = "buy mcp server, mcp server tutorial, buy mcp server online, python mcp"
    res = json.loads(cluster_keywords_by_similarity(kw_list, 2))
    assert res["status"] == "CLUSTERED"
    assert res["total_keywords_processed"] == 4


def test_2_classify_intent():
    res = json.loads(classify_search_intent("buy etl pipeline mcp"))
    assert res["status"] == "CLASSIFIED"
    assert res["primary_intent"] == "TRANSACTIONAL"


def test_3_cannibalization_detection():
    data = json.dumps([
        {"url": "https://seosiri.com/p1.html", "target_keyword": "mcp server"},
        {"url": "https://seosiri.com/p2.html", "target_keyword": "mcp server"}
    ])
    res = json.loads(detect_keyword_cannibalization(data))
    assert res["status"] == "RISKS_DETECTED"
    assert res["conflicting_keywords_count"] == 1


def test_4_topical_map():
    res = json.loads(generate_topical_authority_map("Model Context Protocol", "mcp tutorial, mcp server python"))
    assert res["status"] == "MAP_GENERATED"
    assert res["total_clusters"] == 2


def test_5_keyword_difficulty():
    res = json.loads(calculate_keyword_difficulty_score("how to deploy mcp server on cloudflare", 7))
    assert res["status"] == "CALCULATED"
    assert res["difficulty_score"] < 50.0


def test_6_lsi_variants():
    res = json.loads(extract_lsi_semantic_variants("bioassay mcp"))
    assert res["status"] == "EXTRACTED"
    assert len(res["lsi_variants"]) == 5


def test_7_rag_embeddings():
    res = json.loads(generate_text_embeddings("SEOSiri MCP Server Architecture"))
    assert res["status"] == "EMBEDDING_GENERATED"
    assert res["vector_dimensions"] == 384


def test_8_rag_index_chunk():
    res = json.loads(index_content_chunks_for_rag("https://seosiri.com/page1", "Model Context Protocol servers enable AI agent automation."))
    assert res["status"] == "INDEXED_FOR_RAG"


def test_9_rag_retrieve_context():
    index_content_chunks_for_rag("https://seosiri.com/page1", "Model Context Protocol servers enable AI agent automation.")
    res = json.loads(retrieve_semantic_rag_context("What is Model Context Protocol?", top_k=1))
    assert res["status"] == "CONTEXT_RETRIEVED"
    assert res["matches_found"] == 1


def test_10_parquet_export():
    data = json.dumps([{"cluster": "mcp", "count": 5}])
    res = json.loads(export_cluster_parquet_buffer(data))
    assert res["status"] == "PARQUET_BUFFER_GENERATED"


def test_11_sanitize_payload():
    res = json.loads(sanitize_keyword_payload("keyword <script>alert('xss')</script>"))
    assert res["status"] == "SANITIZED"
    assert "<script>" not in res["clean_input"]


def test_12_throughput_metrics():
    res = json.loads(get_live_keyword_throughput_metrics())
    assert res["status"] == "HEALTHY"


def test_13_server_specifications():
    res = json.loads(get_keyword_server_specifications())
    assert res["status"] != ""
    assert res["total_tools"] == 13