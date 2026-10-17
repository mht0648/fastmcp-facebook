# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-10-17

### Added
- **Phase 0 Architecture Discovery Deliverable:**
  - System Architecture specification (`docs/architecture.md`).
  - STRIDE Threat Model (`docs/threat-model.md`).
  - Security Architecture documentation (`docs/security-architecture.md`).
  - Meta Graph API v21.0 Permission Matrix (`docs/permission-matrix.md`).
  - Permanent Token Authentication guide (`docs/authentication.md`).
  - Complete MCP Tool Reference specification (`docs/tool-reference.md`).
  - Deployment and operations guide (`docs/deployment.md`).
  - Architecture Decision Records (ADR-001 through ADR-005).
  - Modern Python packaging configuration (`pyproject.toml`) supporting FastMCP and Pydantic v2.
  - Comprehensive open-source `README.md`, `SECURITY.md`, and `CONTRIBUTING.md`.
  - Comprehensive 60-test automated suite covering all 9 MCP tools, JSON-RPC protocol, Meta Graph API error parsing, and adversarial prompt injections (`tests/`).
  - Standalone automated test runner script (`run_tests.py`).
  - Detailed testing strategy and edge-case documentation (`docs/testing.md`).
