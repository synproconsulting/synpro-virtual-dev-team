# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
