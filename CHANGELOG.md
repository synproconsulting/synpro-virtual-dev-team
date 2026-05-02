# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security - 2025-01-XX
- **[SDT1-62] Password Reset Token Security** - Hardened password reset flow to prevent token exposure
  - Enhanced documentation in `auth.py` with explicit SECURITY comments on all password reset endpoints
  - Verified that reset tokens are NEVER returned in API response bodies (request or complete endpoints)
  - Verified that tokens are never logged directly (only user_id is logged for correlation)
  - Added comprehensive security test suite in `tests/test_auth_security.py`:
    - Tests verify no token in response body or headers
    - Tests verify generic responses to prevent email enumeration
    - Tests verify token only sent via email channel
    - Tests verify no token leakage in logs
  - Added integration tests in `tests/test_password_reset_flow.py`:
    - End-to-end password reset flow security validation
    - Error handling security (expired, used, invalid tokens)
    - Multi-request security validation
    - Timing attack prevention validation
  - Created comprehensive security documentation in `uat/backend/SECURITY.md`
  - Added test infrastructure:
    - `pytest.ini` configuration for clean test output
    - `tests/conftest.py` with shared fixtures
    - `tests/README.md` with testing guidelines
  - Added `pytest-asyncio==0.23.3` for async test support

#### Security Benefits
- **No Token Exposure**: Reset tokens never appear in API responses, preventing:
  - Browser developer tools exposure
  - Application log exposure
  - CDN/proxy cache exposure
  - Client-side code exposure
- **Email Enumeration Prevention**: Same response for valid/invalid emails prevents account discovery
- **Audit Trail**: All security measures documented and tested
- **Defense in Depth**: Multiple layers of protection at code, logging, and testing levels

### Added - 2025-01-XX
- **[SDT1-57] CreateOrGetFixVersionTool** - Deterministic fix version management for PM Agent
  - New `create_or_get_fix_version()` function in `jira_client.py` that ensures same version name always returns same ID
  - New `list_fix_versions()` function to retrieve all project versions
  - CrewAI tool wrappers: `CreateOrGetFixVersionTool` and `ListFixVersionsTool`
  - Comprehensive unit tests in `tests/test_fix_versions.py`
  - Integration tests in `tests/integration/test_fix_version_integration.py`
  - Documentation:
    - Full tool documentation: `docs/fix_version_tool.md`
    - Quick start guide: `docs/QUICKSTART_FIX_VERSIONS.md`
  - Example usage script: `examples/fix_version_example.py`
  - Updated PM Agent backstory to include release management responsibilities
  - Added `VERSION_TOOLS` group to `pm_tools.py`
  - pytest configuration with integration test markers

### Benefits
- **Deterministic behavior**: Calling with same version name always returns same ID, preventing duplicates
- **Safe automation**: PM Agent can safely create/reference versions without manual coordination
- **Release tracking**: Group related stories by release version for coordinated delivery
- **Thread-safe**: Multiple concurrent calls with same name won't create duplicates

### Technical Details
- Implementation follows existing codebase patterns
- Full type hints on all functions
- Comprehensive docstrings
- Test coverage: unit tests + integration tests
- Compatible with CrewAI >= 0.80.0
- Uses Jira Python library 3.5.2

## [Previous Releases]

<!-- Add previous releases here as they occur -->
