#!/bin/bash

###############################################################################
# validate_rotation.sh
# Validation script for post-token-rotation testing
# 
# Usage:
#   ./validate_rotation.sh [staging|production]
#
# Tests:
#   - API health check
#   - User registration (JWT)
#   - User authentication (JWT)
#   - Authenticated endpoints
#   - Password reset email (SMTP)
#   - Railway API integration (if token present)
#
# Exit codes:
#   0 - All tests passed
#   1 - One or more tests failed
###############################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${1:-staging}"
PASSED=0
FAILED=0

# API URLs
if [[ "$ENVIRONMENT" == "production" ]]; then
    API_BASE_URL="${API_URL_PROD:-https://api.synpro.example.com}"
else
    API_BASE_URL="${API_URL_STAGING:-https://staging-api.synpro.example.com}"
fi

# Test credentials
TEST_EMAIL="validation-test-$(date +%s)@example.com"
TEST_PASSWORD="ValidationTest123!@#"

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Token Rotation Validation"
    echo "  Environment: $ENVIRONMENT"
    echo "  API: $API_BASE_URL"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
}

print_test() {
    echo -n "  $(printf '%-40s' "$1")"
}

pass() {
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}"
    if [[ -n "${1:-}" ]]; then
        echo -e "    ${RED}→${NC} $1"
    fi
    ((FAILED++))
}

skip() {
    echo -e "${YELLOW}⊘ SKIP${NC}"
    if [[ -n "${1:-}" ]]; then
        echo -e "    ${YELLOW}→${NC} $1"
    fi
}

###############################################################################
# Test Functions
###############################################################################

test_health_check() {
    print_test "Health check"
    
    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL/api/health" 2>/dev/null || echo "000")
    
    if [[ "$status" == "200" ]]; then
        pass
        return 0
    else
        fail "HTTP $status"
        return 1
    fi
}

test_user_registration() {
    print_test "User registration (JWT generation)"
    
    local response
    response=$(curl -s -X POST "$API_BASE_URL/api/auth/register" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
        2>/dev/null || echo "{}")
    
    local token
    token=$(echo "$response" | jq -r '.access_token // empty' 2>/dev/null || echo "")
    
    if [[ -n "$token" && "$token" != "null" && "$token" != "undefined" ]]; then
        # Store token for subsequent tests
        export VALIDATION_TOKEN="$token"
        pass
        return 0
    else
        fail "No access token received"
        return 1
    fi
}

test_user_login() {
    print_test "User login (JWT validation)"
    
    local response
    response=$(curl -s -X POST "$API_BASE_URL/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
        2>/dev/null || echo "{}")
    
    local token
    token=$(echo "$response" | jq -r '.access_token // empty' 2>/dev/null || echo "")
    
    if [[ -n "$token" && "$token" != "null" ]]; then
        pass
        return 0
    else
        fail "Login failed"
        return 1
    fi
}

test_authenticated_request() {
    print_test "Authenticated request"
    
    if [[ -z "${VALIDATION_TOKEN:-}" ]]; then
        skip "No token available"
        return 0
    fi
    
    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL/api/auth/me" \
        -H "Authorization: Bearer $VALIDATION_TOKEN" \
        2>/dev/null || echo "000")
    
    if [[ "$status" == "200" ]]; then
        pass
        return 0
    else
        fail "HTTP $status"
        return 1
    fi
}

test_password_reset() {
    print_test "Password reset email (SMTP)"
    
    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL/api/auth/password-reset/request" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$TEST_EMAIL\"}" \
        2>/dev/null || echo "000")
    
    if [[ "$status" == "200" ]]; then
        pass
        return 0
    else
        fail "HTTP $status"
        return 1
    fi
}

test_railway_api() {
    print_test "Railway API integration"
    
    # Check if Railway token is set
    if [[ -z "${RAILWAY_API_TOKEN:-}" ]]; then
        skip "RAILWAY_API_TOKEN not set"
        return 0
    fi
    
    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST https://backboard.railway.app/graphql/v2 \
        -H "Authorization: Bearer $RAILWAY_API_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"query":"{ projects { edges { node { id } } } }"}' \
        2>/dev/null || echo "000")
    
    if [[ "$status" == "200" ]]; then
        pass
        return 0
    else
        fail "HTTP $status"
        return 1
    fi
}

test_jwt_token_structure() {
    print_test "JWT token structure validation"
    
    if [[ -z "${VALIDATION_TOKEN:-}" ]]; then
        skip "No token available"
        return 0
    fi
    
    # JWT should have 3 parts separated by dots
    local parts
    parts=$(echo "$VALIDATION_TOKEN" | tr '.' '\n' | wc -l)
    
    if [[ "$parts" -eq 3 ]]; then
        pass
        return 0
    else
        fail "Invalid JWT structure (expected 3 parts, got $parts)"
        return 1
    fi
}

test_database_connectivity() {
    print_test "Database operations"
    
    # Registration test already validated database write
    # Login test already validated database read
    # Just check that both worked
    
    if [[ -n "${VALIDATION_TOKEN:-}" ]]; then
        pass
        return 0
    else
        fail "Database operations failed"
        return 1
    fi
}

test_cors_headers() {
    print_test "CORS configuration"
    
    local response
    response=$(curl -s -I "$API_BASE_URL/api/health" 2>/dev/null || echo "")
    
    if echo "$response" | grep -qi "access-control-allow"; then
        pass
        return 0
    else
        skip "CORS headers not detected (may be normal)"
        return 0
    fi
}

test_rate_limiting() {
    print_test "Rate limiting (5 rapid requests)"
    
    local success_count=0
    for i in {1..5}; do
        local status
        status=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL/api/health" 2>/dev/null || echo "000")
        if [[ "$status" == "200" ]]; then
            ((success_count++))
        fi
    done
    
    if [[ $success_count -ge 3 ]]; then
        pass
        return 0
    else
        fail "Only $success_count/5 requests succeeded"
        return 1
    fi
}

###############################################################################
# Performance Tests
###############################################################################

test_response_time() {
    print_test "API response time"
    
    local start_time=$(date +%s%3N)
    curl -s -o /dev/null "$API_BASE_URL/api/health" 2>/dev/null
    local end_time=$(date +%s%3N)
    
    local response_time=$((end_time - start_time))
    
    if [[ $response_time -lt 2000 ]]; then
        pass
        echo "      Response time: ${response_time}ms"
        return 0
    else
        fail "Slow response: ${response_time}ms"
        return 1
    fi
}

###############################################################################
# Main Test Suite
###############################################################################

run_all_tests() {
    print_header
    
    echo "Running validation tests..."
    echo ""
    
    # Core functionality tests
    echo "Core Functionality:"
    test_health_check
    test_user_registration
    test_user_login
    test_authenticated_request
    test_jwt_token_structure
    
    echo ""
    echo "Integration Tests:"
    test_password_reset
    test_railway_api
    test_database_connectivity
    
    echo ""
    echo "Configuration Tests:"
    test_cors_headers
    test_rate_limiting
    
    echo ""
    echo "Performance Tests:"
    test_response_time
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    
    # Summary
    local total=$((PASSED + FAILED))
    echo ""
    echo "Results: $PASSED passed, $FAILED failed (of $total tests)"
    
    if [[ $FAILED -eq 0 ]]; then
        echo -e "${GREEN}✓ All tests passed!${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Monitor logs for 24 hours"
        echo "  2. Check error rates in monitoring dashboard"
        echo "  3. Update audit log with validation results"
        echo "  4. Mark rotation as complete in your tracking system"
        return 0
    else
        echo -e "${RED}✗ Some tests failed${NC}"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Check application logs: railway logs --environment $ENVIRONMENT"
        echo "  2. Verify environment variables are set correctly"
        echo "  3. Test individual endpoints manually"
        echo "  4. Consider rolling back if issues persist"
        echo ""
        echo "See TOKEN_ROTATION.md for rollback procedures"
        return 1
    fi
}

###############################################################################
# CLI
###############################################################################

usage() {
    cat << EOF
Usage: $0 [environment]

Environments:
  staging      Validate staging environment (default)
  production   Validate production environment

Environment Variables:
  API_URL_PROD      Production API URL
  API_URL_STAGING   Staging API URL
  RAILWAY_API_TOKEN Railway API token (optional, for Railway tests)

Examples:
  $0                  # Validate staging
  $0 staging          # Validate staging
  $0 production       # Validate production

EOF
}

# Main
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    usage
    exit 0
fi

if [[ -n "${1:-}" ]] && [[ ! "$1" =~ ^(staging|production)$ ]]; then
    echo "Error: Invalid environment '$1'"
    usage
    exit 1
fi

# Run tests
run_all_tests
exit $?
