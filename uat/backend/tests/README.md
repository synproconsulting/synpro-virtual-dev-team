# Backend Integration Tests

This directory contains integration tests for the UAT backend API.

## Running Tests

### Run all tests
```bash
cd uat/backend
pytest
```

### Run specific test file
```bash
pytest tests/test_railway_router.py
```

### Run tests with coverage
```bash
pytest --cov=. --cov-report=html
```

### Run only integration tests
```bash
pytest -m integration
```

### Run with verbose output
```bash
pytest -v
```

## Test Structure

- `conftest.py` - Shared fixtures and test configuration
- `test_railway_router.py` - Integration tests for Railway deployment API endpoints (SDT1-68)

## Writing New Tests

1. Create a new file with the prefix `test_` (e.g., `test_my_feature.py`)
2. Import necessary modules and fixtures from `conftest.py`
3. Write test functions with the prefix `test_`
4. Use markers to categorize tests:
   - `@pytest.mark.integration` - For integration tests
   - `@pytest.mark.unit` - For unit tests
   - `@pytest.mark.slow` - For slow-running tests

## Test Coverage

The tests cover:

- Railway API endpoints
  - Health check
  - Project management (list projects)
  - Service management (list services per project)
  - Environment management (list environments)
  - Deployment operations (trigger deployment/redeploy)
  - Deployment status queries
  - Service variables retrieval

- Error scenarios
  - Unauthorized access
  - Missing required fields
  - Railway API errors
  - Unexpected errors

- Integration workflows
  - Full deployment workflow from project selection to deployment status

## SDT1-68: Railway Redeploy Endpoint

The primary focus of these tests is the `/api/railway/deployments/trigger` endpoint, which performs redeploy operations. The comprehensive test suite includes:

- Success scenarios for deployment triggering
- Authentication and authorization tests
- Input validation
- Error handling
- Full end-to-end deployment workflow

## Environment Variables

Tests automatically set up required environment variables via `conftest.py`. The following are configured for testing:

- `JWT_SECRET` - Test JWT secret key
- `JWT_EXPIRY_HOURS` - Token expiry time
- `RAILWAY_API_TOKEN` - Mock Railway API token
- `CORS_ALLOWED_ORIGINS` - Allowed CORS origins
- `ENVIRONMENT` - Set to "test"
- `LOG_LEVEL` - Logging level

## Mocking

Tests use `unittest.mock` to mock external dependencies:

- Railway API client (`RailwayClient`)
- Authentication (`get_current_user`)
- Database connections (when needed)

This ensures tests run quickly and don't depend on external services.
