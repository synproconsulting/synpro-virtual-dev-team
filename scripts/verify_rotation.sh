#!/bin/bash
# verify_rotation.sh
# Post-rotation verification script
#
# Usage:
#   ./verify_rotation.sh production
#   ./verify_rotation.sh staging

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/../logs/verification-$(date +%Y%m%d-%H%M%S).log"

# Ensure log directory exists
mkdir -p "$(dirname "${LOG_FILE}")"

# Test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to log and display
log() {
    local message="$@"
    echo -e "$message" | tee -a "$LOG_FILE"
}

# Function to run a test
run_test() {
    local test_name=$1
    local test_command=$2
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -ne "${BLUE}[TEST]${NC} ${test_name}... " | tee -a "$LOG_FILE"
    
    if eval "$test_command" >> "$LOG_FILE" 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}" | tee -a "$LOG_FILE"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}" | tee -a "$LOG_FILE"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Function to check API health
check_api_health() {
    local environment=$1
    local api_url="https://api-${environment}.yourdomain.com"
    
    log "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    log "${BLUE}  API Health Checks${NC}"
    log "${BLUE}═══════════════════════════════════════════════════════${NC}"
    
    # Health endpoint
    run_test "API Health Endpoint" \
        "curl -f -s ${api_url}/health -o /dev/null"
    
    # Check response time
    run_test "API Response Time (<2s)" \
        "[ \$(curl -w '%{time_total}' -o /dev/null -s ${api_url}/health | cut -d. -f1) -lt 2 ]"
    
    # Check if API is returning valid JSON
    run_test "API Returns Valid JSON" \
        "curl -s ${api_url}/health | jq empty"
}

# Function to check Kubernetes deployments
check_kubernetes() {
    local environment=$1
    
    log "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    log "${BLUE}  Kubernetes Deployment Checks${NC}"
    log "${BLUE}═══════════════════════════════════════════════════════${NC}"
    
    # Check deployment exists
    run_test "Deployment Exists" \
        "kubectl get deployment pm-agent-backend -n ${environment} -o name"
    
    # Check deployment is ready
    run_test "Deployment Ready" \
        "kubectl get deployment pm-agent-backend -n ${environment} -o jsonpath='{.status.readyReplicas}' | grep -E '^[1-9][0-9]*$'"
    
    # Check pods are running
    run_test "All Pods Running" \
        "kubectl get pods -n ${environment} -l app=pm-agent-backend -o jsonpath='{.items[*].status.phase}' | grep -v -q 'Failed\|Pending\|Unknown'"
    
    # Check no recent restarts
    run_test "No Recent Restarts" \
        "[ \$(kubectl get pods -n ${environment} -l app=pm-agent-backend -o jsonpath='{.items[*].status.containerStatuses[0].restartCount}' | awk '{s+=\$1} END {print s}') -lt 3 ]"
    
    # Check pod logs for errors (last 5 minutes)
    run_test "No Critical Errors in Logs" \
        "! kubectl logs -n ${environment} -l app=pm-agent-backend --since=5m | grep -i 'CRITICAL\|FATAL'"
}

# Function to check secrets
check_secrets() {
    local environment=$1
    
    log "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    log "${BLUE}  Secrets Validation${NC}"
    log "${BLUE}═══════════════════════════════════════════════════════${NC}"
    
    # Check AWS Secrets Manager connectivity
    run_test "AWS Secrets Manager Access" \
        "aws secretsmanager list-secrets --max-results 1 -o json | jq -e '.SecretList'"
    
    # Verify secrets exist
    for secret in jira-token openai-key github-token database-url jwt-secret; do
        run_test "Secret Exists: ${secret}" \
            "aws secretsmanager describe-secret --secret-id pm-agent/${environment}/${secret} --query 'Name' --output text"
    done
    
    # Check secret versions
    run_test "Secrets Have Recent Version" \
        "aws secretsmanager list-secrets --filters Key=name,Values=pm-agent/${environment} | jq -e '.SecretList[].LastChangedDate' | head -1"
}

# Function to test Jira integration
test_jira_integration() {
    local environment=$1
    
    log "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    log "${BLUE}  Jira Integration Tests${NC}"
    log "${BLUE}═══════════════════════════════════════════════════════${NC}"
    
    # Get Jira credentials from environment
    local jira_email="${JIRA_EMAIL:-}"
    local jira_domain="${JIRA_DOMAIN:-}"
    
    if [ -z "$jira_email" ] || [ -z "$jira_domain" ]; then
        log "${YELLOW}⚠ Skipping Jira tests - JIRA_EMAIL or JIRA_DOMAIN not set${NC}"
        return
    fi
    
    # Get token from AWS Secrets Manager
    local jira_token=$(aws secretsmanager get-secret-value \
        --secret-id "pm-agent/${environment}/jira-token" \
        --query 'SecretString' \
        --output text)
    
    # Test Jira API connectivity
    run_test "Jira API Connectivity" \
        "curl -f -s -u '${jira_email}:${jira_token}' 'https://${jira_domain}/rest/api/3/myself' -o /dev/null"
    
    # Test reading issues
    run_test "Jira Read Issues" \
        "curl -f -s -u '${jira_email}:${jira_token}' 'https://${jira_domain}/rest/api/3/search?maxResults=1' | jq -e '.issues'"
}

# Function to test OpenAI integration
test_openai_integration() {
    local environment=$1
    
    log "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    log "${BLUE}  OpenAI Integration Tests${NC}"
    log "${BLUE}═══════════════════════════════════════════════════════${NC}"
    
    # Get token from AWS Secrets Manager
    local openai_key=$(aws secretsmanager get-secret-value \
        --secret-id "pm-agent/${environment}/openai-key" \
        --query 'SecretString' \
        --output text)
    
    # Test OpenAI API connectivity
    run_test "OpenAI API Connectivity" \
        "curl -f -s -H 'Authorization: Bearer ${openai_key}' 'https://api.openai.com/v1/models' -o /dev/null"
    
    # Test listing models
    run_test "OpenAI List Models" \
        "curl -f -s -H 'Authorization: Bearer ${openai_key}' 'https://api.openai.com/v1/models' | jq -e '.data'"
    
    # Test rate limits are OK
    run_test "OpenAI Rate Limits OK" \
        "curl -s -H 'Authorization: Bearer ${openai_key}' 'https://api.openai.com/v1/models' -I | grep -q 'x-ratelimit-remaining'"
}

# Function to test GitHub integration
test_github_integration() {
    local environment=$1
    
    log "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    log "${BLUE}  GitHub Integration Tests${NC}"
    log "${BLUE}═══════════════════════════════════════════════════════${NC}"
    
    # Get token from AWS Secrets Manager
    local github_token=$(aws secretsmanager get-secret-value \
        --secret-id "pm-agent/${environment}/github-token" \
        --query 'SecretString' \
        --output text)
    
    # Test GitHub API connectivity
    run_test "GitHub API Connectivity" \
        "curl -f -s -H 'Authorization: token ${github_token}' 'https://api.github.com/user' -o /dev/null"
    
    # Check token scopes
    run_test "GitHub Token Has Required Scopes" \
        "curl -s -I -H 'Authorization: token ${github_token}' 'https://api.github.com/user' | grep -i 'X-OAuth-Scopes' | grep -q 'repo'"
    
    # Test rate limits
    run_test "GitHub Rate Limits OK" \
        "[ \$(curl -s -H 'Authorization: token ${github_token}' 'https://api.github.com/rate_limit' | jq -r '.rate.remaining') -gt 100 ]"
}

# Function to test database connectivity
test_database_connectivity() {
    local environment=$1
    
    log "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    log "${BLUE}  Database Connectivity Tests${NC}"
    log "${BLUE}═══════════════════════════════════════════════════════${NC}"
    
    # Get database URL from secrets
    local db_url=$(aws secretsmanager get-secret-value \
        --secret-id "pm-agent/${environment}/database-url" \
        --query 'SecretString' \
        --output text)
    
    # Extract database connection info
    if [[ $db_url =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
        local db_user="${BASH_REMATCH[1]}"
        local db_pass="${BASH_REMATCH[2]}"
        local db_host="${BASH_REMATCH[3]}"
        local db_port="${BASH_REMATCH[4]}"
        local db_name="${BASH_REMATCH[5]}"
        
        # Test database connection
        run_test "Database Connection" \
            "PGPASSWORD='${db_pass}' psql -h ${db_host} -p ${db_port} -U ${db_user} -d ${db_name} -c 'SELECT 1;' -t | grep -q 1"
        
        # Test query execution
        run_test "Database Query Execution" \
            "PGPASSWORD='${db_pass}' psql -h ${db_host} -p ${db_port} -U ${db_user} -d ${db_name} -c 'SELECT COUNT(*) FROM conversations;' -t"
        
        # Check connection pool
        run_test "Database Connection Pool OK" \
            "[ \$(PGPASSWORD='${db_pass}' psql -h ${db_host} -p ${db_port} -U ${db_user} -d ${db_name} -c \"SELECT count(*) FROM pg_stat_activity WHERE usename='${db_user}';\" -t | tr -d ' ') -lt 50 ]"
    else
        log "${YELLOW}⚠ Could not parse DATABASE_URL${NC}"
    fi
}

# Function to check error rates
check_error_rates() {
    local environment=$1
    
    log "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    log "${BLUE}  Error Rate Checks${NC}"
    log "${BLUE}═══════════════════════════════════════════════════════${NC}"
    
    # Check recent error count (last 10 minutes)
    run_test "Low Error Rate (Last 10min)" \
        "[ \$(kubectl logs -n ${environment} -l app=pm-agent-backend --since=10m | grep -i ERROR | wc -l) -lt 10 ]"
    
    # Check no authentication errors
    run_test "No Auth Errors" \
        "! kubectl logs -n ${environment} -l app=pm-agent-backend --since=5m | grep -i 'authentication.*fail\|unauthorized\|invalid.*token'"
    
    # Check no database errors
    run_test "No Database Errors" \
        "! kubectl logs -n ${environment} -l app=pm-agent-backend --since=5m | grep -i 'database.*error\|connection.*refused'"
}

# Function to generate summary report
generate_summary() {
    log "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    log "${BLUE}  Verification Summary${NC}"
    log "${BLUE}═══════════════════════════════════════════════════════${NC}"
    
    log "Total Tests:  ${TOTAL_TESTS}"
    log "${GREEN}Passed:       ${PASSED_TESTS}${NC}"
    
    if [ $FAILED_TESTS -gt 0 ]; then
        log "${RED}Failed:       ${FAILED_TESTS}${NC}"
    else
        log "Failed:       ${FAILED_TESTS}"
    fi
    
    local success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    log "Success Rate: ${success_rate}%"
    
    log "\nLog file: ${LOG_FILE}"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        log "\n${GREEN}✓ All verification tests passed!${NC}"
        return 0
    else
        log "\n${RED}✗ Some verification tests failed. Please review.${NC}"
        return 1
    fi
}

# Main script
main() {
    log "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
    log "${BLUE}║     Post-Rotation Verification Script                ║${NC}"
    log "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
    log ""
    
    # Check arguments
    if [ $# -ne 1 ]; then
        log "${RED}Usage: $0 <environment>${NC}"
        log ""
        log "Arguments:"
        log "  environment: staging | production"
        exit 1
    fi
    
    local environment=$1
    
    # Validate environment
    if [[ ! "$environment" =~ ^(staging|production)$ ]]; then
        log "${RED}Invalid environment: ${environment}${NC}"
        exit 1
    fi
    
    log "Environment: ${environment}"
    log "Started: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    log ""
    
    # Run verification checks
    check_api_health "$environment"
    check_kubernetes "$environment"
    check_secrets "$environment"
    test_jira_integration "$environment"
    test_openai_integration "$environment"
    test_github_integration "$environment"
    test_database_connectivity "$environment"
    check_error_rates "$environment"
    
    # Generate summary
    generate_summary
    
    exit $?
}

# Run main function
main "$@"
