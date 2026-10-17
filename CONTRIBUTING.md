# Contributing to facebook-pages-mcp

Thank you for your interest in contributing to `facebook-pages-mcp`!

This repository is designed as an architecturally rigorous, security-first open-source MCP server. All contributions must adhere to the engineering standards detailed below.

---

## Code Quality & Architecture Standards

1. **Architecture First:** Before introducing new capabilities or tools, review [docs/architecture.md](docs/architecture.md) and submit an Architectural Decision Record (ADR) if proposing changes to system boundaries or dependencies.
2. **Official Meta APIs Only:** Only implement endpoints officially supported by Meta Graph API v21.0+. Scraping, browser automation, or deprecated Group APIs will be rejected.
3. **Type Annotations & Validation:** All Python code must have full type hints and validate external inputs via Pydantic v2 schemas.
4. **Security by Design:** Every new tool must be classified as `READ`, `STAGING`, or `SENSITIVE WRITE`. Direct write tools without two-stage approval will not be accepted.
5. **Zero Token Leakage:** Never log credentials or pass tokens in error messages.

---

## Local Development Workflow

```bash
# 1. Clone and enter repo
git clone https://github.com/mht0648/fastmcp-facebook.git
cd fastmcp-facebook

# 2. Setup virtual environment
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# 3. Run linting & tests
ruff check .
pytest tests/ -v
```
