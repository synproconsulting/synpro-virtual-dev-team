#!/bin/bash
# emergency_rotation.sh
# Emergency token rotation script for compromised credentials
#
# Usage:
#   ./emergency_rotation.sh production jira
#   ./emergency_rotation.sh staging openai

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/../logs"
AUDIT_LOG="${LOG_DIR}/emergency-rotation-audit.log"

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Function to log messages
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
    echo -e "${timestamp} [${level}] ${message}" | tee -a "${AUDIT_LOG}"
}

# Function to log errors
error() {
    log "ERROR" "${RED}$@${NC}"
}

# Function to log warnings
warn() {
    log "WARN" "${YELLOW}$@${NC}"
}

# Function to log success
success() {
    log "INFO" "${GREEN}$@${NC}"
}

# Function to log info
info() {
    log "INFO" "$@"
}

# Function to check prerequisites
check_prerequisites() {
    local missing_tools=()
    
    for tool in aws kubectl jq; do
        if ! command -v $tool &> /dev/null; then
            missing_tools+=($tool)
        fi
    done
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        error "Missing required tools: ${missing_tools[*]}"
        echo "Install missing tools and try again."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured or expired"
        exit 1
    fi
    
    # Check kubectl access
    if ! kubectl cluster-info &> /dev/null; then
        error "kubectl not configured or no cluster access"
        exit 1
    fi
    
    success "All prerequisites met"
}

# Function to backup current secret
backup_secret() {
    local environment=$1
    local secret_name=$2
    local backup_file="${LOG_DIR}/backup-${environment}-${secret_name}-$(date +%Y%m%d-%H%M%S).enc"
    
    info "Backing up current secret: ${secret_name}"
    
    aws secretsmanager get-secret-value \
        --secret-id "pm-agent/${environment}/${secret_name}" \
        --query 'SecretString' \
        --output text > "${backup_file}"
    
    if [ $? -eq 0 ]; then
        success "Backup saved to: ${backup_file}"
        echo "${backup_file}"
    else
        error "Failed to backup secret"
        return 1
    fi
}

# Function to rotate Jira token
rotate_jira() {
    local environment=$1
    
    warn "🚨 EMERGENCY JIRA TOKEN ROTATION"
    info "Environment: ${environment}"
    
    # Backup current token
    backup_file=$(backup_secret "${environment}" "jira-token")
    
    # Prompt for new token
    echo ""
    echo "Create a new Jira API token:"
    echo "1. Go to https://id.atlassian.com/manage-profile/security/api-tokens"
    echo "2. Click 'Create API token'"
    echo "3. Name it: pm-agent-emergency-$(date +%Y-%m-%d-%H%M)"
    echo ""
    
    read -sp "Paste the new Jira API token: " new_token
    echo ""
    
    if [ -z "$new_token" ]; then
        error "No token provided, aborting"
        exit 1
    fi
    
    # Update in AWS Secrets Manager
    info "Updating Jira token in AWS Secrets Manager..."
    aws secretsmanager update-secret \
        --secret-id "pm-agent/${environment}/jira-token" \
        --secret-string "${new_token}"
    
    if [ $? -ne 0 ]; then
        error "Failed to update secret in AWS Secrets Manager"
        exit 1
    fi
    
    # Update in Kubernetes
    info "Updating Jira token in Kubernetes..."
    kubectl set env deployment/pm-agent-backend \
        JIRA_API_TOKEN="${new_token}" \
        -n "${environment}"
    
    if [ $? -ne 0 ]; then
        error "Failed to update Kubernetes deployment"
        exit 1
    fi
    
    # Wait for rollout
    info "Waiting for deployment rollout..."
    kubectl rollout status deployment/pm-agent-backend -n "${environment}" --timeout=300s
    
    success "✅ Jira token rotation complete"
    warn "IMPORTANT: Manually revoke the old token in Atlassian account!"
}

# Function to rotate OpenAI key
rotate_openai() {
    local environment=$1
    
    warn "🚨 EMERGENCY OPENAI KEY ROTATION"
    info "Environment: ${environment}"
    
    # Backup current key
    backup_file=$(backup_secret "${environment}" "openai-key")
    
    # Prompt for new key
    echo ""
    echo "Create a new OpenAI API key:"
    echo "1. Go to https://platform.openai.com/api-keys"
    echo "2. Click 'Create new secret key'"
    echo "3. Name it: pm-agent-emergency-$(date +%Y-%m-%d-%H%M)"
    echo ""
    
    read -sp "Paste the new OpenAI API key: " new_key
    echo ""
    
    if [ -z "$new_key" ]; then
        error "No key provided, aborting"
        exit 1
    fi
    
    # Update in AWS Secrets Manager
    info "Updating OpenAI key in AWS Secrets Manager..."
    aws secretsmanager update-secret \
        --secret-id "pm-agent/${environment}/openai-key" \
        --secret-string "${new_key}"
    
    # Update in Kubernetes
    info "Updating OpenAI key in Kubernetes..."
    kubectl set env deployment/pm-agent-backend \
        OPENAI_API_KEY="${new_key}" \
        -n "${environment}"
    
    # Wait for rollout
    info "Waiting for deployment rollout..."
    kubectl rollout status deployment/pm-agent-backend -n "${environment}" --timeout=300s
    
    success "✅ OpenAI key rotation complete"
    warn "IMPORTANT: Manually revoke the old key in OpenAI platform!"
}

# Function to rotate GitHub token
rotate_github() {
    local environment=$1
    
    warn "🚨 EMERGENCY GITHUB TOKEN ROTATION"
    info "Environment: ${environment}"
    
    # Backup current token
    backup_file=$(backup_secret "${environment}" "github-token")
    
    # Prompt for new token
    echo ""
    echo "Create a new GitHub Personal Access Token:"
    echo "1. Go to https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Name it: pm-agent-emergency-$(date +%Y-%m-%d-%H%M)"
    echo "4. Select scopes: repo, workflow"
    echo ""
    
    read -sp "Paste the new GitHub token: " new_token
    echo ""
    
    if [ -z "$new_token" ]; then
        error "No token provided, aborting"
        exit 1
    fi
    
    # Update in AWS Secrets Manager
    info "Updating GitHub token in AWS Secrets Manager..."
    aws secretsmanager update-secret \
        --secret-id "pm-agent/${environment}/github-token" \
        --secret-string "${new_token}"
    
    # Update in Kubernetes
    info "Updating GitHub token in Kubernetes..."
    kubectl set env deployment/pm-agent-backend \
        GITHUB_TOKEN="${new_token}" \
        -n "${environment}"
    
    # Wait for rollout
    info "Waiting for deployment rollout..."
    kubectl rollout status deployment/pm-agent-backend -n "${environment}" --timeout=300s
    
    success "✅ GitHub token rotation complete"
    warn "IMPORTANT: Manually revoke the old token in GitHub settings!"
}

# Function to rotate JWT secret
rotate_jwt() {
    local environment=$1
    
    warn "🚨 EMERGENCY JWT SECRET ROTATION"
    warn "This will INVALIDATE ALL USER SESSIONS!"
    info "Environment: ${environment}"
    
    read -p "Continue? (type 'YES' to confirm): " confirm
    if [ "$confirm" != "YES" ]; then
        error "Rotation cancelled"
        exit 1
    fi
    
    # Backup current secret
    backup_file=$(backup_secret "${environment}" "jwt-secret")
    
    # Generate new secret
    info "Generating new JWT secret..."
    new_secret=$(openssl rand -base64 32)
    
    # Get old secret for dual-verification
    old_secret=$(aws secretsmanager get-secret-value \
        --secret-id "pm-agent/${environment}/jwt-secret" \
        --query 'SecretString' \
        --output text)
    
    # Update in AWS Secrets Manager
    info "Updating JWT secret in AWS Secrets Manager..."
    aws secretsmanager update-secret \
        --secret-id "pm-agent/${environment}/jwt-secret" \
        --secret-string "${new_secret}"
    
    aws secretsmanager update-secret \
        --secret-id "pm-agent/${environment}/jwt-secret-previous" \
        --secret-string "${old_secret}" || true
    
    # Update in Kubernetes
    info "Updating JWT secret in Kubernetes..."
    kubectl set env deployment/pm-agent-backend \
        JWT_SECRET_KEY="${new_secret}" \
        JWT_SECRET_KEY_PREVIOUS="${old_secret}" \
        -n "${environment}"
    
    # Wait for rollout
    info "Waiting for deployment rollout..."
    kubectl rollout status deployment/pm-agent-backend -n "${environment}" --timeout=300s
    
    success "✅ JWT secret rotation complete"
    warn "All users have been logged out"
    warn "Remove JWT_SECRET_KEY_PREVIOUS after 24 hours"
}

# Function to rotate database password
rotate_database() {
    local environment=$1
    
    warn "🚨 EMERGENCY DATABASE PASSWORD ROTATION"
    warn "This requires database admin access!"
    info "Environment: ${environment}"
    
    read -p "Continue? (type 'YES' to confirm): " confirm
    if [ "$confirm" != "YES" ]; then
        error "Rotation cancelled"
        exit 1
    fi
    
    # Backup current DATABASE_URL
    backup_file=$(backup_secret "${environment}" "database-url")
    
    # Get current DATABASE_URL
    old_db_url=$(aws secretsmanager get-secret-value \
        --secret-id "pm-agent/${environment}/database-url" \
        --query 'SecretString' \
        --output text)
    
    # Parse DATABASE_URL
    if [[ $old_db_url =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
        db_user="${BASH_REMATCH[1]}"
        old_password="${BASH_REMATCH[2]}"
        db_host="${BASH_REMATCH[3]}"
        db_port="${BASH_REMATCH[4]}"
        db_name="${BASH_REMATCH[5]}"
    else
        error "Failed to parse DATABASE_URL"
        exit 1
    fi
    
    # Generate new password
    info "Generating new database password..."
    new_password=$(openssl rand -base64 32)
    
    # Display SQL command
    echo ""
    warn "Run this SQL command as database admin:"
    echo "ALTER USER ${db_user} WITH PASSWORD '${new_password}';"
    echo ""
    
    read -p "Have you executed the SQL command? (type 'YES' to confirm): " confirm
    if [ "$confirm" != "YES" ]; then
        error "Database password not updated, aborting"
        exit 1
    fi
    
    # Build new DATABASE_URL
    new_db_url="postgresql://${db_user}:${new_password}@${db_host}:${db_port}/${db_name}"
    
    # Update in AWS Secrets Manager
    info "Updating DATABASE_URL in AWS Secrets Manager..."
    aws secretsmanager update-secret \
        --secret-id "pm-agent/${environment}/database-url" \
        --secret-string "${new_db_url}"
    
    # Update in Kubernetes
    info "Updating DATABASE_URL in Kubernetes..."
    kubectl set env deployment/pm-agent-backend \
        DATABASE_URL="${new_db_url}" \
        -n "${environment}"
    
    # Wait for rollout
    info "Waiting for deployment rollout..."
    kubectl rollout status deployment/pm-agent-backend -n "${environment}" --timeout=300s
    
    success "✅ Database password rotation complete"
}

# Main script
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║       🚨 EMERGENCY TOKEN ROTATION SCRIPT 🚨                ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Check arguments
    if [ $# -ne 2 ]; then
        error "Usage: $0 <environment> <token_type>"
        echo ""
        echo "Arguments:"
        echo "  environment: staging | production"
        echo "  token_type:  jira | openai | github | jwt | database"
        echo ""
        echo "Example:"
        echo "  $0 production jira"
        exit 1
    fi
    
    local environment=$1
    local token_type=$2
    
    # Validate environment
    if [[ ! "$environment" =~ ^(staging|production)$ ]]; then
        error "Invalid environment: $environment"
        exit 1
    fi
    
    # Validate token type
    if [[ ! "$token_type" =~ ^(jira|openai|github|jwt|database)$ ]]; then
        error "Invalid token type: $token_type"
        exit 1
    fi
    
    # Check prerequisites
    info "Checking prerequisites..."
    check_prerequisites
    
    # Log rotation start
    info "Starting emergency rotation: ${token_type} in ${environment}"
    info "Initiated by: $(whoami)"
    info "Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
    
    # Confirmation
    warn "You are about to perform an EMERGENCY rotation"
    warn "Environment: ${environment}"
    warn "Token type: ${token_type}"
    echo ""
    read -p "Type 'EMERGENCY' to proceed: " confirm
    
    if [ "$confirm" != "EMERGENCY" ]; then
        error "Confirmation failed, aborting"
        exit 1
    fi
    
    # Perform rotation based on token type
    case $token_type in
        jira)
            rotate_jira "$environment"
            ;;
        openai)
            rotate_openai "$environment"
            ;;
        github)
            rotate_github "$environment"
            ;;
        jwt)
            rotate_jwt "$environment"
            ;;
        database)
            rotate_database "$environment"
            ;;
    esac
    
    # Final verification
    echo ""
    info "Performing post-rotation health check..."
    
    if kubectl get pods -n "${environment}" | grep -q "Running"; then
        success "✅ Pods are running"
    else
        error "❌ Pods are not running properly"
    fi
    
    # Log completion
    success "Emergency rotation completed successfully"
    info "Audit log: ${AUDIT_LOG}"
    
    echo ""
    warn "POST-ROTATION TASKS:"
    echo "1. Monitor logs: kubectl logs -f deployment/pm-agent-backend -n ${environment}"
    echo "2. Revoke the old ${token_type} token/key in the respective platform"
    echo "3. Update incident response documentation"
    echo "4. Notify security team"
    echo "5. Document what led to this emergency rotation"
    echo ""
}

# Run main function
main "$@"
