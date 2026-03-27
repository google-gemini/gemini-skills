---
name: gemini-cross-validated-search
description: Use this skill when Gemini needs live web search, source-backed verification, or page-level reading. Covers search-web, browse-page, verify-claim, evidence-report, and the free dual-provider path for stronger evidence reports.
---

# Gemini Cross-Validated Search Skill

## Overview

Use `cross-validated-search` when Gemini needs current facts, explicit source handling, or a structured support/conflict read on a factual claim.

This skill is most useful when Gemini should:

- search the live web before answering a time-sensitive question
- verify a claim instead of trusting a single snippet
- read a full page when the search result preview is too thin
- produce a compact evidence report with sources and next steps

## Install

```bash
pip install cross-validated-search
```

Canonical names in the current release:

- package: `cross-validated-search`
- module: `cross_validated_search`
- MCP command: `cross-validated-search-mcp`

## Core commands

```bash
search-web "latest Python release" --type news --timelimit w
browse-page "https://docs.python.org/3/whatsnew/"
verify-claim "Python 3.13 is the latest stable release" --deep --max-pages 2 --json
evidence-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

## Recommended workflow for Gemini

1. Use `search-web` for current or factual questions.
2. Use `browse-page` when snippets are not enough to support an answer.
3. Use `verify-claim` when the question is really a factual claim that could be supported, contested, or weakly evidenced.
4. Use `evidence-report` when Gemini should return one citation-ready artifact instead of raw search output.

## MCP configuration

```json
{
  "mcpServers": {
    "cross-validated-search": {
      "command": "cross-validated-search-mcp",
      "args": []
    }
  }
}
```

## What Gemini should look for

Useful signals in the JSON output include:

- `verdict`: such as `supported`, `contested`, or `likely_false`
- `confidence`: evidence-weighted confidence for the current verdict
- `provider_diversity`: whether the evidence came from more than one provider path
- `page_aware`: whether fetched page content contributed to the analysis
- supporting and conflicting sources that can be cited directly

## Free path

The default path starts with `ddgs` and does not require an API key.

For stronger free evidence reports, pair it with self-hosted SearXNG:

```bash
export CROSS_VALIDATED_SEARCH_SEARXNG_URL="http://127.0.0.1:8080"
verify-claim "Python 3.13 is the latest stable release" --deep --json
```

## When to use it

- current events, versions, releases, and statistics
- factual questions that need citations
- claims that might be supported by some sources and contradicted by others
- workflows where Gemini should surface uncertainty instead of flattening it

## When not to over-trust it

- when only one provider is configured
- when snippets and fetched pages are both sparse
- when the claim requires deep domain expertise or full-document reasoning

## Limits

- `verify-claim` is evidence-aware and heuristic, not a proof engine
- page-aware verification is stronger than snippets alone, but still not full entailment
- the default path is useful, but the strongest free setup is `ddgs + self-hosted searxng`

## Project links

- GitHub: https://github.com/wd041216-bit/cross-validated-search
- PyPI: https://pypi.org/project/cross-validated-search/
- Documentation: https://github.com/wd041216-bit/cross-validated-search/blob/main/README.md
