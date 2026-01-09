#!/bin/bash

# Script to deploy/restart the Picture of the Day application in Kubernetes
# Usage:
#   ./deploy.sh              - Restart deployment (pull new image)
#   ./deploy.sh --apply      - Apply all k8s configs and restart deployment
#   ./deploy.sh --apply-only - Only apply k8s configs (no restart)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="pictureoftheday"
DEPLOYMENT_NAME="pictureoftheday"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
APPLY_CONFIGS=false
APPLY_ONLY=false

for arg in "$@"; do
    case $arg in
        --apply)
            APPLY_CONFIGS=true
            shift
            ;;
        --apply-only)
            APPLY_CONFIGS=true
            APPLY_ONLY=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --apply       Apply all k8s configs and restart deployment"
            echo "  --apply-only  Only apply k8s configs (no restart)"
            echo "  --help, -h    Show this help message"
            echo ""
            echo "Default: Restart deployment only (assumes configs are already applied)"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "Deploying Picture of the Day to Kubernetes..."
echo "Namespace: $NAMESPACE"
echo "Deployment: $DEPLOYMENT_NAME"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo -e "${YELLOW}Warning: Namespace '$NAMESPACE' does not exist${NC}"
    if [ "$APPLY_CONFIGS" = true ]; then
        echo "Will create namespace when applying configs..."
    else
        echo -e "${RED}Error: Cannot proceed without namespace. Use --apply to create it.${NC}"
        exit 1
    fi
fi

# Apply k8s configs if requested
if [ "$APPLY_CONFIGS" = true ]; then
    echo -e "${GREEN}Applying Kubernetes configurations...${NC}"
    echo ""
    
    # Apply in order
    echo "Applying namespace..."
    kubectl apply -f "$SCRIPT_DIR/namespace.yaml"
    
    echo "Applying configmap..."
    kubectl apply -f "$SCRIPT_DIR/configmap.yaml"
    
    echo "Applying secrets..."
    kubectl apply -f "$SCRIPT_DIR/secret.yaml"
    
    echo "Applying postgres deployment..."
    kubectl apply -f "$SCRIPT_DIR/postgres-deployment.yaml"
    
    echo "Applying deployment..."
    kubectl apply -f "$SCRIPT_DIR/deployment.yaml"
    
    echo "Applying service..."
    kubectl apply -f "$SCRIPT_DIR/service.yaml"
    
    echo "Applying ingress..."
    kubectl apply -f "$SCRIPT_DIR/ingress.yaml"
    
    echo "Applying cronjob..."
    kubectl apply -f "$SCRIPT_DIR/cronjob.yaml"
    
    echo "Applying cleanup cronjob..."
    kubectl apply -f "$SCRIPT_DIR/cleanup-cronjob.yaml"
    
    echo ""
    echo -e "${GREEN}All configurations applied successfully!${NC}"
    echo ""
fi

# Exit early if only applying configs
if [ "$APPLY_ONLY" = true ]; then
    echo "Configs applied. Exiting (no restart requested)."
    exit 0
fi

# Restart deployment to pull new image
echo -e "${GREEN}Restarting deployment to pull new image...${NC}"
echo ""

# Check if deployment exists
if ! kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" &> /dev/null; then
    echo -e "${RED}Error: Deployment '$DEPLOYMENT_NAME' does not exist in namespace '$NAMESPACE'${NC}"
    echo "Use --apply to create the deployment first."
    exit 1
fi

# Restart deployment by setting an annotation with current timestamp
# This forces Kubernetes to recreate the pods
TIMESTAMP=$(date +%s)
kubectl annotate deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" \
    "deployment.kubernetes.io/restartedAt=$TIMESTAMP" \
    --overwrite &> /dev/null || true

echo "Deployment restart triggered..."
echo ""

# Wait for rollout to start
echo "Waiting for rollout to start..."
sleep 2

# Show rollout status
echo ""
echo -e "${GREEN}Rollout status:${NC}"
kubectl rollout status deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE" --timeout=300s

echo ""
echo -e "${GREEN}Deployment restarted successfully!${NC}"
echo ""

# Show pod status
echo -e "${GREEN}Current pod status:${NC}"
kubectl get pods -n "$NAMESPACE" -l app="$DEPLOYMENT_NAME"

echo ""
echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "Useful commands:"
echo "  kubectl get pods -n $NAMESPACE"
echo "  kubectl logs -n $NAMESPACE -l app=$DEPLOYMENT_NAME --tail=50"
echo "  kubectl describe deployment $DEPLOYMENT_NAME -n $NAMESPACE"

