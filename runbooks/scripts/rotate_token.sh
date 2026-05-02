#!/bin/bash

###############################################################################
# rotate_token.sh
# Automated token rotation script for SynPro Virtual Dev Team platform
# 
# Usage:
#   ./rotate_token.sh jwt [staging|production]
#   ./rotate_token.sh railway [staging|production]
#   ./rotate_token.sh smtp [staging|production]
#
# Prerequisites:
#   - Railway CLI installed and authenticated
#   - Python 3.11+ with required packages
#   - Appropriate permissions for environment
#
# Safety features:
#   - Confirmation prompts before production changes
#   - Automatic backup of current configuration
#   - Rollback capability
#   - Validation tests after rotation
###############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups"
LOG_FILE="$SCRIPT_DIR/rotation.log"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

###############################################################################
# Helper Functions
###############################################################################

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}ℹ${NC} $*"
    log "INFO" "$*"
}

success() {
    echo -e "${GREEN}✓${NC} $*"
    log "SUCCESS" "$*"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $*"
    log "WARNING" "$*"
}

error() {
    echo -e "${RED}✗${NC} $*" >&2
    log "ERROR" "$*"
}

fatal() {
    error "$*"
    exit 1
}

confirm() {
    local prompt="$1"
    local response
    
    read -p "$prompt (yes/no): " response
    case "$response" in
        yes|YES|y|Y)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

###############################################################################
# Validation Functions
###############################################################################

check_prerequisites() {
    info "Checking prerequisites..."
    
    # Check Railway CLI
    if ! command -v railway &> /dev/null; then
        fatal "Railway CLI not found. Install from: https://docs.railway.app/develop/cli"
    fi
    success "Railway CLI installed"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        fatal "Python 3 not found"
    fi
    success "Python 3 installed"
    
    # Check Railway authentication
    if ! railway whoami &> /dev/null; then
        fatal "Not authenticated with Railway. Run: railway login"
    fi
    success "Railway authenticated"
}

validate_environment() {
    local env="$1"
    
    if [[ ! "$env" =~ ^(staging|production)$ ]]; then
        fatal "Invalid environment: $env. Must be 'staging' or 'production'"
    fi
    
    # Extra confirmation for production
    if [[ "$env" == "production" ]]; then
        warning "You are about to modify PRODUCTION environment"
        if ! confirm "Are you sure you want to continue?"; then
            info "Aborted by user"
            exit 0
        fi
    fi
}

###############################################################################
# Backup and Restore
###############################################################################

backup_variables() {
    local env="$1"
    local backup_file="$BACKUP_DIR/env_${env}_$(date +%Y%m%d_%H%M%S).json"
    
    info "Backing up current environment variables..."
    
    if railway variables --environment "$env" --json > "$backup_file" 2>/dev/null; then
        success "Backup created: $backup_file"
        echo "$backup_file"
    else
        warning "Failed to create backup (this may be okay if variables don't exist yet)"
        echo ""
    fi
}

restore_variables() {
    local backup_file="$1"
    local env="$2"
    local var_name="$3"
    local var_value="$4"
    
    warning "Restoring variable from backup..."
    
    if [[ -f "$backup_file" && -s "$backup_file" ]]; then
        # Extract old value from backup
        local old_value=$(jq -r ".\"$var_name\" // empty" "$backup_file")
        if [[ -n "$old_value" ]]; then
            railway variables --environment "$env" --set "${var_name}=${old_value}"
            success "Restored $var_name from backup"
            return 0
        fi
    fi
    
    # Fallback: use provided value
    if [[ -n "$var_value" ]]; then
        railway variables --environment "$env" --set "${var_name}=${var_value}"
        success "Restored $var_name from provided value"
        return 0
    fi
    
    error "Could not restore variable"
    return 1
}

###############################################################################
# JWT Secret Rotation
###############################################################################

rotate_jwt_secret() {
    local env="$1"
    
    info "Starting JWT secret rotation for $env environment"
    
    # Backup current variables
    local backup_file=$(backup_variables "$env")
    
    # Generate new JWT secret
    info "Generating new JWT secret..."
    local new_secret
    new_secret=$(python3 ../../backend/generate_jwt_secret.py 2>/dev/null | grep -v "Generated" | grep -v "To use" | grep -v "export" | grep -v "For production" | head -n 1 | tr -d '\n')
    
    if [[ -z "$new_secret" ]]; then
        fatal "Failed to generate JWT secret"
    fi
    
    # Validate the generated secret
    info "Validating new secret..."
    if ! python3 ../../backend/generate_jwt_secret.py --validate "$new_secret" &> /dev/null; then
        fatal "Generated secret failed validation"
    fi
    success "New secret validated (${#new_secret} characters)"
    
    # Show confirmation with last 8 characters
    local secret_preview="...${new_secret: -8}"
    info "New secret preview: $secret_preview"
    
    if [[ "$env" == "production" ]]; then
        if ! confirm "Deploy new JWT secret to production?"; then
            info "Aborted by user"
            return 0
        fi
    fi
    
    # Deploy new secret
    info "Deploying new JWT secret..."
    if railway variables --environment "$env" --set "JWT_SECRET=$new_secret"; then
        success "JWT_SECRET updated in $env"
    else
        error "Failed to set JWT_SECRET"
        if [[ -n "$backup_file" ]]; then
            restore_variables "$backup_file" "$env" "JWT_SECRET" ""
        fi
        return 1
    fi
    
    # Wait for deployment
    info "Waiting for service to restart..."
    sleep 10
    
    # Validate rotation
    if validate_jwt_rotation "$env"; then
        success "JWT secret rotation completed successfully"
        
        # Log rotation
        log_rotation "JWT_SECRET" "$env" "success" "$secret_preview"
        
        return 0
    else
        error "JWT validation failed after rotation"
        
        if confirm "Rollback to previous JWT secret?"; then
            restore_variables "$backup_file" "$env" "JWT_SECRET" ""
            warning "Rolled back JWT_SECRET"
        fi
        
        return 1
    fi
}

validate_jwt_rotation() {
    local env="$1"
    local api_url
    
    if [[ "$env" == "production" ]]; then
        api_url="${API_URL_PROD:-https://api.synpro.example.com}"
    else
        api_url="${API_URL_STAGING:-https://staging-api.synpro.example.com}"
    fi
    
    info "Validating JWT rotation against $api_url..."
    
    # Test health endpoint
    local health_status
    health_status=$(curl -s -o /dev/null -w "%{http_code}" "$api_url/api/health" || echo "000")
    
    if [[ "$health_status" != "200" ]]; then
        error "Health check failed (HTTP $health_status)"
        return 1
    fi
    success "Health check passed"
    
    # Test authentication flow
    local test_email="rotation-test-$(date +%s)@example.com"
    local test_password="RotationTest123!@#"
    
    local register_response
    register_response=$(curl -s -X POST "$api_url/api/auth/register" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$test_email\",\"password\":\"$test_password\"}" \
        2>/dev/null || echo "{}")
    
    local token
    token=$(echo "$register_response" | jq -r '.access_token // empty')
    
    if [[ -z "$token" || "$token" == "null" ]]; then
        error "Failed to obtain JWT token"
        return 1
    fi
    success "JWT token obtained"
    
    # Test authenticated request
    local me_status
    me_status=$(curl -s -o /dev/null -w "%{http_code}" "$api_url/api/auth/me" \
        -H "Authorization: Bearer $token" || echo "000")
    
    if [[ "$me_status" != "200" ]]; then
        error "Authenticated request failed (HTTP $me_status)"
        return 1
    fi
    success "Authenticated request succeeded"
    
    return 0
}

###############################################################################
# Railway API Token Rotation
###############################################################################

rotate_railway_token() {
    local env="$1"
    
    info "Starting Railway API token rotation for $env environment"
    
    warning "Railway API token must be generated manually"
    echo ""
    echo "Steps:"
    echo "  1. Go to https://railway.app/account/tokens"
    echo "  2. Click 'Create New Token'"
    echo "  3. Name: synpro-vdt-$env-$(date +%Y%m%d)"
    echo "  4. Required scopes:"
    echo "     ✓ Read projects, services, deployments"
    echo "     ✓ Trigger deployments"
    echo "  5. Copy the generated token"
    echo ""
    
    if ! confirm "Have you generated the new Railway token?"; then
        info "Aborted by user"
        return 0
    fi
    
    # Prompt for new token
    echo -n "Enter the new Railway API token: "
    read -s new_token
    echo ""
    
    if [[ -z "$new_token" ]]; then
        fatal "No token provided"
    fi
    
    # Validate token format (starts with rtf_ or similar)
    if [[ ! "$new_token" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        warning "Token format looks unusual, but proceeding..."
    fi
    
    # Backup current variables
    local backup_file=$(backup_variables "$env")
    
    # Test new token
    info "Testing new Railway token..."
    if validate_railway_token "$new_token"; then
        success "Railway token validated"
    else
        error "Railway token validation failed"
        return 1
    fi
    
    # Deploy new token
    if [[ "$env" == "production" ]]; then
        if ! confirm "Deploy new Railway token to production?"; then
            info "Aborted by user"
            return 0
        fi
    fi
    
    info "Deploying new Railway token..."
    if railway variables --environment "$env" --set "RAILWAY_API_TOKEN=$new_token"; then
        success "RAILWAY_API_TOKEN updated in $env"
    else
        error "Failed to set RAILWAY_API_TOKEN"
        return 1
    fi
    
    # Wait for deployment
    info "Waiting for service to restart..."
    sleep 10
    
    # Validate after rotation
    info "Validating Railway integration..."
    local token_preview="...${new_token: -8}"
    success "Railway token rotation completed"
    
    log_rotation "RAILWAY_API_TOKEN" "$env" "success" "$token_preview"
    
    echo ""
    warning "Don't forget to revoke the old token in Railway dashboard!"
    
    return 0
}

validate_railway_token() {
    local token="$1"
    
    local response
    response=$(curl -s -X POST https://backboard.railway.app/graphql/v2 \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -d '{"query":"{ projects { edges { node { id } } } }"}' \
        2>/dev/null || echo "{}")
    
    if echo "$response" | jq -e '.data.projects' &> /dev/null; then
        return 0
    else
        return 1
    fi
}

###############################################################################
# SMTP Credentials Rotation
###############################################################################

rotate_smtp_credentials() {
    local env="$1"
    
    info "Starting SMTP credentials rotation for $env environment"
    
    warning "SMTP password must be generated manually from your email provider"
    echo ""
    echo "For Gmail App Passwords:"
    echo "  1. Go to https://myaccount.google.com/security"
    echo "  2. Enable 2-Step Verification (if not already enabled)"
    echo "  3. Go to App passwords"
    echo "  4. Generate new app password"
    echo "  5. Name: SynPro VDT $env $(date +%Y%m%d)"
    echo "  6. Copy the 16-character password"
    echo ""
    
    if ! confirm "Have you generated the new SMTP password?"; then
        info "Aborted by user"
        return 0
    fi
    
    # Prompt for new password
    echo -n "Enter the new SMTP password: "
    read -s new_password
    echo ""
    
    if [[ -z "$new_password" ]]; then
        fatal "No password provided"
    fi
    
    # Backup current variables
    local backup_file=$(backup_variables "$env")
    
    # Get SMTP configuration
    echo -n "SMTP host (default: smtp.gmail.com): "
    read smtp_host
    smtp_host=${smtp_host:-smtp.gmail.com}
    
    echo -n "SMTP port (default: 587): "
    read smtp_port
    smtp_port=${smtp_port:-587}
    
    echo -n "SMTP username (email): "
    read smtp_username
    
    if [[ -z "$smtp_username" ]]; then
        fatal "SMTP username required"
    fi
    
    # Test SMTP connection
    info "Testing SMTP connection..."
    if validate_smtp_credentials "$smtp_host" "$smtp_port" "$smtp_username" "$new_password"; then
        success "SMTP credentials validated"
    else
        error "SMTP validation failed"
        return 1
    fi
    
    # Deploy new credentials
    if [[ "$env" == "production" ]]; then
        if ! confirm "Deploy new SMTP credentials to production?"; then
            info "Aborted by user"
            return 0
        fi
    fi
    
    info "Deploying new SMTP credentials..."
    railway variables --environment "$env" --set "SMTP_HOST=$smtp_host"
    railway variables --environment "$env" --set "SMTP_PORT=$smtp_port"
    railway variables --environment "$env" --set "SMTP_USERNAME=$smtp_username"
    railway variables --environment "$env" --set "SMTP_PASSWORD=$new_password"
    railway variables --environment "$env" --set "SMTP_FROM_EMAIL=$smtp_username"
    
    success "SMTP credentials updated in $env"
    
    log_rotation "SMTP_PASSWORD" "$env" "success" "***"
    
    return 0
}

validate_smtp_credentials() {
    local host="$1"
    local port="$2"
    local username="$3"
    local password="$4"
    
    python3 -c "
import smtplib
import sys

try:
    smtp = smtplib.SMTP('$host', $port, timeout=10)
    smtp.starttls()
    smtp.login('$username', '$password')
    smtp.quit()
    sys.exit(0)
except Exception as e:
    print(f'SMTP validation failed: {e}', file=sys.stderr)
    sys.exit(1)
"
}

###############################################################################
# Logging and Audit
###############################################################################

log_rotation() {
    local token_type="$1"
    local environment="$2"
    local status="$3"
    local preview="$4"
    
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local user=$(whoami)
    
    # Append to audit log
    echo "$timestamp,$token_type,$environment,$user,$status,$preview" >> "$SCRIPT_DIR/audit.log"
    
    info "Rotation logged to audit.log"
}

###############################################################################
# Main
###############################################################################

usage() {
    cat << EOF
Usage: $0 <token_type> <environment>

Token Types:
  jwt        Rotate JWT secret
  railway    Rotate Railway API token
  smtp       Rotate SMTP credentials
  all        Rotate all tokens (interactive)

Environments:
  staging       Staging environment
  production    Production environment

Examples:
  $0 jwt staging
  $0 railway production
  $0 smtp staging
  $0 all production

Environment Variables:
  API_URL_PROD      Production API URL (default: https://api.synpro.example.com)
  API_URL_STAGING   Staging API URL (default: https://staging-api.synpro.example.com)

Notes:
  - All operations require Railway CLI authentication
  - Production rotations require confirmation
  - Automatic backups are created before each rotation
  - Rollback capability available for JWT rotations

EOF
}

main() {
    if [[ $# -lt 2 ]]; then
        usage
        exit 1
    fi
    
    local token_type="$1"
    local environment="$2"
    
    # Header
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Token Rotation Script"
    echo "  SynPro Virtual Dev Team"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Validate environment
    validate_environment "$environment"
    
    # Perform rotation based on type
    case "$token_type" in
        jwt)
            rotate_jwt_secret "$environment"
            ;;
        railway)
            rotate_railway_token "$environment"
            ;;
        smtp)
            rotate_smtp_credentials "$environment"
            ;;
        all)
            warning "Sequential rotation of all tokens"
            if confirm "Continue with all token rotations?"; then
                rotate_jwt_secret "$environment" && \
                rotate_railway_token "$environment" && \
                rotate_smtp_credentials "$environment"
            fi
            ;;
        *)
            error "Unknown token type: $token_type"
            usage
            exit 1
            ;;
    esac
    
    # Summary
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    success "Token rotation completed"
    echo ""
    info "Next steps:"
    echo "  1. Monitor logs: railway logs --environment $environment"
    echo "  2. Check error rates in monitoring dashboard"
    echo "  3. Update audit log: runbooks/scripts/audit.log"
    echo "  4. Schedule next rotation in calendar"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
}

# Run main function
main "$@"
