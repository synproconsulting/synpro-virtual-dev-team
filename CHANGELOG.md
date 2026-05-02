# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **[SDT1-65] PM Agent validation for missing execution_order**
  - Added `PMValidator` class with comprehensive validation logic
  - Added `validate_story` tool to PM Agent for pre-creation validation
  - Added `validate_backlog` tool to audit entire backlog health
  - Critical validation: Warns when `execution_order` is missing (ERROR level)
  - Best practice warnings: Missing epic, story points, oversized stories, etc.
  - Integrated validation warnings into `create_story` tool output
  - Updated PM Agent backstory to emphasize validation workflow
  - Created comprehensive test suite with pytest (25+ test cases)
  - Added documentation in `docs/pm-agent-validation.md`
  - Added usage examples in `examples/pm_validation_example.py`

### Changed
- Enhanced `CreateStoryTool` to automatically validate and include warnings in output
- Updated PM Agent goal to emphasize execution_order requirement
- Improved PM Agent backstory with validation best practices

### Technical Details
- New module: `tools/pm_validation.py` - Core validation logic
- New tests: `tools/test_pm_validation.py` - 100% coverage of validation logic
- Validation severity levels: ERROR (critical), WARNING (best practice), INFO (minor)
- Global validator singleton for easy access across tools
- Integration with existing PM tools (no breaking changes)

### Migration Notes
- No breaking changes - all existing code continues to work
- PM Agent will now receive validation warnings when creating stories
- Existing stories without execution_order should be audited with `validate_backlog`
- Use `update_issue` to add execution_order to existing stories (requires future enhancement)

## [Previous Releases]
<!-- Add previous release notes here -->
