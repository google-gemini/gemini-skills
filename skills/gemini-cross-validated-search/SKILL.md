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
import os
import google.generativeai as genai
from cross_validated_search import CrossValidatedSearcher

# Initialize Gemini
# Make sure to set your GEMINI_API_KEY environment variable
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
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
model = genai.GenerativeModel("gemini-1.5-flash-latest")
response = model.generate_content(
    "What is the latest version of Python?",
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
import os
import google.generativeai as genai
from cross_validated_search import CrossValidatedSearcher

# Initialize Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
searcher = CrossValidatedSearcher()

# Get cross-validated results
def get_verified_answer(query: str) -> str:
    # Search with cross-validation
    results = searcher.search(query)
    
    # Check confidence - handle all four levels
    if results.confidence == "verified":
        return f"✅ Verified: {results.answer}"
    elif results.confidence == "likely_true":
        return f"🟢 Likely True: {results.answer}"
    elif results.confidence == "likely_false":
        return f"🔴 Likely False: {results.answer}"
    else:  # uncertain
        return f"🟡 Uncertain: {results.answer}"

# Use in Gemini prompt
prompt = f"""
Based on the following verified information, answer the question.

{get_verified_answer("What is Gemini 1.5?")}

Question: What are the key features of Gemini 1.5?
"""

model = genai.GenerativeModel("gemini-1.5-flash-latest")
response = model.generate_content(prompt)
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
from cross_validated_search import CrossValidatedSearcher

searcher = CrossValidatedSearcher()

# Check if a claim is verified
results = searcher.search("Is Gemini 1.5 released?")

if results.confidence == "verified":
    print(f"✅ Confirmed: {results.answer}")
else:
    print(f"⚠️ Needs verification: {results.answer}")
```

### Example 2: News Search

```python
from cross_validated_search import CrossValidatedSearcher

searcher = CrossValidatedSearcher()

# Get latest news with confidence
results = searcher.search("Gemini 1.5 announcements", search_type="news")

# Print overall confidence first
print(f"Overall confidence: {results.confidence}")

for article in results.sources[:5]:
    print(f"- {article.title}")
    print(f"  Source: {article.url}")
```

### Example 3: Multi-Query Research

```python
from cross_validated_search import CrossValidatedSearcher

searcher = CrossValidatedSearcher()

queries = [
    "What is Gemini 1.5?",
    "What are Gemini 1.5's capabilities?",
    "When was Gemini 1.5 released?",
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
    timelimit="d",      # Time limit: "d" (day), "w" (week), "m" (month), or None for no limit.
    region="wt-wt",     # Region for the search (e.g., "us-en"). "wt-wt" means Worldwide.
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