#!/bin/bash
#
# Kubernetes Secret Rotation Helper Script
#
# This script helps rotate secrets in Kubernetes by:
# 1. Backing up the current secret
# 2. Creating a new secret with the updated value
# 3. Restarting deployments that use the secret
# 4. Monitoring the rollout
#
# Usage:
#   ./rotate-k8s-secret.sh --secret-name jira-api-token --key token --value "new_token_value" --deployments "pm-agent,orchestrator"
#   ./rotate-k8s-secret.sh --secret-name github-token --key token --value "new_token_value" --deployments "orchestrator"
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
NAMESPACE="default"
BACKUP_DIR="./secret-backups"
DRY_RUN=false
SKIP_BACKUP=false
WAIT_TIME=300  # 5 minutes default timeout for rollout

# Function to print colored messages
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Rotate a Kubernetes secret and restart affected deployments.

Required Options:
    --secret-name NAME      Name of the secret to rotate
    --key KEY              Key within the secret to update
    --value VALUE          New value for the secret key
    --deployments LIST     Comma-separated list of deployments to restart

Optional:
    --namespace NS         Kubernetes namespace (default: default)
    --backup-dir DIR       Directory for secret backups (default: ./secret-backups)
    --skip-backup          Skip backing up the current secret
    --dry-run              Print commands without executing
    --wait-time SECONDS    Timeout for rollout status (default: 300)
    --help                 Show this help message

Examples:
    # Rotate Jira API token
    $0 --secret-name jira-api-token --key token --value "new_token" \\
       --deployments "pm-agent,orchestrator,uat-backend"

    # Rotate OpenAI API key (dry run)
    $0 --secret-name openai-api-key --key key --value "sk-..." \\
       --deployments "pm-agent,orchestrator" --dry-run

    # Rotate GitHub token in specific namespace
    $0 --secret-name github-token --key token --value "ghp_..." \\
       --deployments "orchestrator" --namespace production

EOF
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --secret-name)
            SECRET_NAME="$2"
            shift 2
            ;;
        --key)
            SECRET_KEY="$2"
            shift 2
            ;;
        --value)
            SECRET_VALUE="$2"
            shift 2
            ;;
        --deployments)
            DEPLOYMENTS="$2"
            shift 2
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --wait-time)
            WAIT_TIME="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate required parameters
if [[ -z "$SECRET_NAME" ]] || [[ -z "$SECRET_KEY" ]] || [[ -z "$SECRET_VALUE" ]] || [[ -z "$DEPLOYMENTS" ]]; then
    log_error "Missing required parameters"
    usage
fi

# Function to execute or print command based on dry-run mode
execute() {
    local cmd="$1"
    if [[ "$DRY_RUN" == true ]]; then
        echo "[DRY RUN] Would execute: $cmd"
    else
        eval "$cmd"
    fi
}

# Main script
main() {
    log_info "Starting secret rotation for: $SECRET_NAME"
    log_info "Namespace: $NAMESPACE"
    log_info "Deployments to restart: $DEPLOYMENTS"
    echo ""

    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl command not found. Please install kubectl."
        exit 1
    fi

    # Check if we can connect to cluster
    if [[ "$DRY_RUN" == false ]]; then
        if ! kubectl cluster-info &> /dev/null; then
            log_error "Cannot connect to Kubernetes cluster. Check your kubeconfig."
            exit 1
        fi
    fi

    # Step 1: Backup existing secret
    if [[ "$SKIP_BACKUP" == false ]]; then
        log_info "Backing up current secret..."
        
        if [[ "$DRY_RUN" == false ]]; then
            # Create backup directory if it doesn't exist
            mkdir -p "$BACKUP_DIR"
            
            # Generate backup filename with timestamp
            TIMESTAMP=$(date +%Y%m%d_%H%M%S)
            BACKUP_FILE="$BACKUP_DIR/${SECRET_NAME}_${TIMESTAMP}.yaml"
            
            # Check if secret exists
            if kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" &> /dev/null; then
                kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o yaml > "$BACKUP_FILE"
                log_success "Secret backed up to: $BACKUP_FILE"
            else
                log_warning "Secret $SECRET_NAME does not exist yet. Will create new."
                BACKUP_FILE=""
            fi
        else
            log_info "[DRY RUN] Would backup secret to: $BACKUP_DIR/${SECRET_NAME}_[timestamp].yaml"
        fi
        echo ""
    else
        log_warning "Skipping backup as requested"
        echo ""
    fi

    # Step 2: Update or create secret
    log_info "Updating secret with new value..."
    
    # Encode the value in base64
    if [[ "$DRY_RUN" == false ]]; then
        ENCODED_VALUE=$(echo -n "$SECRET_VALUE" | base64)
    else
        ENCODED_VALUE="[base64_encoded_value]"
    fi
    
    # Check if secret exists to determine whether to create or patch
    if [[ "$DRY_RUN" == false ]]; then
        if kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" &> /dev/null; then
            # Secret exists, patch it
            kubectl patch secret "$SECRET_NAME" -n "$NAMESPACE" \
                -p "{\"data\":{\"$SECRET_KEY\":\"$ENCODED_VALUE\"}}"
            log_success "Secret patched successfully"
        else
            # Secret doesn't exist, create it
            kubectl create secret generic "$SECRET_NAME" -n "$NAMESPACE" \
                --from-literal="$SECRET_KEY=$SECRET_VALUE"
            log_success "Secret created successfully"
        fi
    else
        log_info "[DRY RUN] Would update/create secret: $SECRET_NAME"
    fi
    echo ""

    # Step 3: Restart deployments
    log_info "Restarting deployments..."
    
    IFS=',' read -ra DEPLOY_ARRAY <<< "$DEPLOYMENTS"
    for deployment in "${DEPLOY_ARRAY[@]}"; do
        # Trim whitespace
        deployment=$(echo "$deployment" | xargs)
        
        log_info "  Restarting deployment: $deployment"
        execute "kubectl rollout restart deployment/$deployment -n $NAMESPACE"
        
        if [[ "$DRY_RUN" == false ]]; then
            log_success "  Rollout initiated for $deployment"
        fi
    done
    echo ""

    # Step 4: Monitor rollout status
    if [[ "$DRY_RUN" == false ]]; then
        log_info "Monitoring rollout status (timeout: ${WAIT_TIME}s)..."
        echo ""
        
        FAILED_DEPLOYMENTS=()
        
        for deployment in "${DEPLOY_ARRAY[@]}"; do
            deployment=$(echo "$deployment" | xargs)
            
            log_info "  Checking $deployment..."
            
            if timeout "$WAIT_TIME" kubectl rollout status deployment/"$deployment" -n "$NAMESPACE"; then
                log_success "  ✓ $deployment rolled out successfully"
            else
                log_error "  ✗ $deployment rollout failed or timed out"
                FAILED_DEPLOYMENTS+=("$deployment")
            fi
            echo ""
        done
        
        # Check if any deployments failed
        if [ ${#FAILED_DEPLOYMENTS[@]} -gt 0 ]; then
            log_error "Some deployments failed to roll out: ${FAILED_DEPLOYMENTS[*]}"
            log_warning "You may need to investigate and potentially rollback."
            
            if [[ -n "$BACKUP_FILE" ]]; then
                echo ""
                log_info "To rollback, run:"
                echo "  kubectl apply -f $BACKUP_FILE"
                echo "  kubectl rollout restart deployment/${FAILED_DEPLOYMENTS[0]} -n $NAMESPACE"
            fi
            exit 1
        fi
    else
        log_info "[DRY RUN] Would monitor rollout status for deployments"
    fi

    # Step 5: Verify pods are running
    if [[ "$DRY_RUN" == false ]]; then
        log_info "Verifying pod status..."
        echo ""
        
        ALL_HEALTHY=true
        
        for deployment in "${DEPLOY_ARRAY[@]}"; do
            deployment=$(echo "$deployment" | xargs)
            
            # Get pod status
            POD_STATUS=$(kubectl get pods -n "$NAMESPACE" -l "app=$deployment" -o jsonpath='{.items[*].status.phase}')
            
            if [[ "$POD_STATUS" == *"Running"* ]]; then
                log_success "  ✓ $deployment pods are running"
            else
                log_error "  ✗ $deployment pods are not all running: $POD_STATUS"
                ALL_HEALTHY=false
            fi
        done
        echo ""
        
        if [[ "$ALL_HEALTHY" == false ]]; then
            log_warning "Some pods are not healthy. Check with: kubectl get pods -n $NAMESPACE"
        fi
    fi

    # Step 6: Show next steps
    echo ""
    log_success "Secret rotation completed!"
    echo ""
    log_info "Next steps:"
    echo "  1. Monitor application logs for any authentication errors:"
    for deployment in "${DEPLOY_ARRAY[@]}"; do
        deployment=$(echo "$deployment" | xargs)
        echo "     kubectl logs -f deployment/$deployment -n $NAMESPACE"
    done
    echo ""
    echo "  2. Verify the application is working correctly"
    echo "     Run: python scripts/verify-token-rotation.py --service all"
    echo ""
    echo "  3. If everything is working, revoke the old token from the provider"
    echo "     (Wait 24 hours for safety)"
    echo ""
    
    if [[ -n "$BACKUP_FILE" ]]; then
        echo "  4. Keep the backup file for 7 days: $BACKUP_FILE"
        echo ""
        log_info "To rollback if needed:"
        echo "  kubectl apply -f $BACKUP_FILE"
        for deployment in "${DEPLOY_ARRAY[@]}"; do
            deployment=$(echo "$deployment" | xargs)
            echo "  kubectl rollout restart deployment/$deployment -n $NAMESPACE"
        done
    fi
}

# Run main function
main

exit 0
