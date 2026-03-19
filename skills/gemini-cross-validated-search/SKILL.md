---
name: gemini-cross-validated-search
description: Use this skill when integrating cross-validated web search with Gemini models. Provides hallucination-free web search by cross-validating facts across multiple sources. Covers search integration, confidence scoring, and MCP protocol support.
---

# Gemini Cross-Validated Search Skill

## Overview

This skill enables Gemini to perform **hallucination-free web search** using cross-validated-search. Every fact is verified against multiple independent sources before being presented.

Key capabilities:
- **Cross-validation** - Facts verified across DuckDuckGo, Bing, and Google
- **Confidence scoring** - Verified / Likely True / Uncertain / Likely False
- **Zero API keys** - Completely free, no configuration needed
- **MCP protocol** - Works with Gemini API function calling

## Installation

```bash
pip install cross-validated-search
```

## Integration with Gemini

### Method 1: Function Calling

```python
from google import genai
from cross_validated_search import CrossValidatedSearcher

# Initialize
client = genai.Client()
searcher = CrossValidatedSearcher()

# Define function for Gemini
def web_search(query: str, search_type: str = "text") -> dict:
    """
    Search the web with cross-validation for hallucination-free results.
    
    Args:
        query: The search query
        search_type: Type of search (text, news, images)
    
    Returns:
        dict with 'answer', 'confidence', and 'sources'
    """
    results = searcher.search(query, search_type=search_type)
    return {
        "answer": results.answer,
        "confidence": results.confidence,
        "sources": [{"title": r.title, "url": r.url} for r in results.sources[:5]]
    }

# Use with Gemini
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="What is the latest version of Python?",
    tools=[{"function_declarations": [{
        "name": "web_search",
        "description": "Search the web with cross-validation for accurate facts",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "search_type": {"type": "string", "enum": ["text", "news", "images"]}
            },
            "required": ["query"]
        }
    }]}]
)
```

### Method 2: MCP Server

```json
// In your Gemini MCP configuration
{
  "mcpServers": {
    "cross-validated-search": {
      "command": "cross-validated-mcp",
      "args": []
    }
  }
}
```

### Method 3: Direct Integration

```python
from google import genai
from cross_validated_search import CrossValidatedSearcher

client = genai.Client()
searcher = CrossValidatedSearcher()

# Get cross-validated results
def get_verified_answer(query: str) -> str:
    # Search with cross-validation
    results = searcher.search(query)
    
    # Check confidence
    if results.confidence == "verified":
        return f"✅ Verified: {results.answer}"
    elif results.confidence == "likely_true":
        return f"🟢 Likely True: {results.answer}"
    else:
        return f"🟡 Uncertain: {results.answer}"

# Use in Gemini prompt
prompt = f"""
Based on the following verified information, answer the question.

{get_verified_answer("What is Gemini 3?")}

Question: What are the key features of Gemini 3?
"""

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=prompt
)
```

## Confidence Levels

| Level | Meaning | When to Use |
|-------|---------|-------------|
| ✅ Verified | 3+ sources agree | Cite as fact |
| 🟢 Likely True | 2 sources agree | Cite with confidence note |
| 🟡 Uncertain | Single source | Flag as unverified |
| 🔴 Likely False | Major contradictions | Do not use |

## Examples

### Example 1: Fact-Checking

```python
# Check if a claim is verified
results = searcher.search("Is Gemini 3 released?")

if results.confidence == "verified":
    print(f"✅ Confirmed: {results.answer}")
else:
    print(f"⚠️ Needs verification: {results.answer}")
```

### Example 2: News Search

```python
# Get latest news with confidence
results = searcher.search("Gemini 3 announcements", search_type="news")

for article in results.sources[:5]:
    print(f"[{results.confidence}] {article.title}")
    print(f"  Source: {article.url}")
```

### Example 3: Multi-Query Research

```python
queries = [
    "What is Gemini 3?",
    "What are Gemini 3's capabilities?",
    "When was Gemini 3 released?",
]

for query in queries:
    results = searcher.search(query)
    print(f"\n{query}")
    print(f"Confidence: {results.confidence}")
    print(f"Answer: {results.answer[:200]}...")
```

## Best Practices

1. **Always check confidence** before using results
2. **Cite sources** when presenting verified facts
3. **Combine with Gemini's knowledge** for comprehensive answers
4. **Use news search** for time-sensitive queries
5. **Filter by confidence** when only verified facts matter

## API Reference

```python
from cross_validated_search import CrossValidatedSearcher

searcher = CrossValidatedSearcher(
    engines=["duckduckgo", "bing", "google"],  # Search engines
    min_sources=2,                              # Minimum sources for verification
    max_results=10,                             # Maximum results
)

results = searcher.search(
    query="Your search query",
    search_type="text",  # "text", "news", "images"
    timelimit=None,      # "d", "w", "m" for day/week/month
    region="wt-wt",      # Region code
)

# Results structure
results.answer       # Summary answer
results.confidence   # "verified", "likely_true", "uncertain", "likely_false"
results.sources      # List of Source objects
results.sources[0].title
results.sources[0].url
results.sources[0].snippet
results.sources[0].engine
```

## Links

- GitHub: https://github.com/wd041216-bit/cross-validated-search
- PyPI: https://pypi.org/project/cross-validated-search/
- Documentation: https://github.com/wd041216-bit/cross-validated-search/blob/main/README.md

## License

MIT-0 License - Free to use with or without attribution.