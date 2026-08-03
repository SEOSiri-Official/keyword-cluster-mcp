# seosiri-keyword-cluster-mcp

> 📖 **Official Architecture & Documentation:** [SEOSiri Keyword Clustering Guide](https://www.seosiri.com/2026/08/keyword-cluster-mcp.html) | [Central MCP Directory](https://www.seosiri.com/2026/07/seosiri-mcp-servers.html)

An open-source, local-first Model Context Protocol (MCP) server for **Semantic Keyword Clustering, Search Intent Classification, Cannibalization Detection, and Topical Authority Mapping**.

## 💖 Sponsorship, B2B Custom Solutions & Attribution

### 👨‍💻 Lead Architect & Attribution
Designed and engineered by **[Momenul Ahmad](https://github.com/MOBILEPHONE)**, Lead Architect and Founder of **[SEOSiri](https://seosiri.com)**.

### 🚀 Capabilities & Tools (10 Production Tools)
- **`cluster_keywords_by_similarity`**: Groups keyword lists into semantic clusters using token overlap.
- **`classify_search_intent`**: Categorizes queries into Informational, Navigational, Commercial, or Transactional intent.
- **`detect_keyword_cannibalization`**: Identifies conflicting URLs targeting the same search query.
- **`generate_topical_authority_map`**: Compiles pillar-cluster content hierarchy trees.
- **`calculate_keyword_difficulty_score`**: Computes algorithmic query difficulty scores ($0\text{--}100$).
- **`extract_lsi_semantic_variants`**: Identifies Latent Semantic Indexing terms and entity phrases.
- **`export_cluster_parquet_buffer`**: Formats keyword clusters into columnar Parquet buffers for DuckDB/S3.
- **`sanitize_keyword_payload`**: Strips scripts and malformed tags from inputs.
- **`get_live_keyword_throughput_metrics`**: Monitors system health and processing latency.
- **`get_keyword_server_specifications`**: Returns protocol specs and capability matrices.

## Quickstart

```bash
pip install -e .
pytest tests/test_keyword_cluster.py
```

### 🔌 Claude Desktop / Cursor Configuration

Add this block to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "seosiri-keyword-cluster": {
      "command": "uv",
      "args": [
        "run",
        "--github",
        "SEOSiri-Official/keyword-cluster-mcp",
        "src/main_server.py"
      ]
    }
  }
}
```

## License

Distributed under the [MIT License](https://github.com/SEOSiri-Official/keyword-cluster-mcp/blob/main/LICENSE).
