#!/usr/bin/env pwsh

# StockRipper v2 Helm Deployment Script
# This script helps deploy the StockRipper v2 system using Helm

param(
    [Parameter(Mandatory=$false)]
    [string]$Action = "install",
    
    [Parameter(Mandatory=$false)]
    [string]$Namespace = "stockripper",
    
    [Parameter(Mandatory=$false)]
    [string]$ReleaseName = "stockripper-v2",
    
    [Parameter(Mandatory=$false)]
    [string]$ValuesFile = "helm/values.yaml",
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false,

    [Parameter(Mandatory=$false)]
    [switch]$CreateSecrets = $false
)

function Write-Status {
    param([string]$Message, [string]$Color = "Green")
    Write-Host "🚀 $Message" -ForegroundColor $Color
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

# Check prerequisites
function Test-Prerequisites {
    Write-Status "Checking prerequisites..."
    
    # Check kubectl
    try {
        kubectl version --client | Out-Null
        Write-Status "✓ kubectl is available"
    }
    catch {
        Write-Error "kubectl is not available. Please install kubectl."
        exit 1
    }
    
    # Check helm
    try {
        helm version --short | Out-Null
        Write-Status "✓ Helm is available"
    }
    catch {
        Write-Error "Helm is not available. Please install Helm 3.0+."
        exit 1
    }
    
    # Check cluster connectivity
    try {
        kubectl cluster-info | Out-Null
        Write-Status "✓ Connected to Kubernetes cluster"
    }
    catch {
        Write-Error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    }
}

# Create secrets if requested
function New-Secrets {
    if (-not $CreateSecrets) {
        return
    }
    
    Write-Status "Creating secrets..."
    
    # Check if secrets already exist
    $existingSecrets = kubectl get secrets -n $Namespace 2>$null | Select-String "openai-secret|alpaca-secret|gmail-credentials"
    
    if ($existingSecrets) {
        Write-Warning "Some secrets already exist. Skipping secret creation."
        Write-Host "Existing secrets:"
        $existingSecrets | ForEach-Object { Write-Host "  - $_" }
        return
    }
    
    # Create namespace if it doesn't exist
    kubectl create namespace $Namespace --dry-run=client -o yaml | kubectl apply -f -
    
    # Prompt for secrets
    Write-Host "Please provide the following credentials:"
    
    $openAiKey = Read-Host "OpenAI API Key" -AsSecureString
    $alpacaApiKey = Read-Host "Alpaca API Key" -AsSecureString  
    $alpacaSecretKey = Read-Host "Alpaca Secret Key" -AsSecureString
    
    # Convert secure strings to plain text
    $openAiKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($openAiKey))
    $alpacaApiKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($alpacaApiKey))
    $alpacaSecretKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($alpacaSecretKey))
    
    # Create OpenAI secret
    kubectl create secret generic openai-secret `
        --from-literal=api-key="$openAiKeyPlain" `
        -n $Namespace
    
    # Create Alpaca secret
    kubectl create secret generic alpaca-secret `
        --from-literal=api-key="$alpacaApiKeyPlain" `
        --from-literal=secret-key="$alpacaSecretKeyPlain" `
        -n $Namespace
    
    # Gmail credentials (files must exist)
    $credentialsPath = "credentials/gmail-credentials.json"
    $tokenPath = "credentials/gmail-token.json"
    
    if ((Test-Path $credentialsPath) -and (Test-Path $tokenPath)) {
        kubectl create secret generic gmail-credentials `
            --from-file=credentials.json="$credentialsPath" `
            --from-file=token.json="$tokenPath" `
            -n $Namespace
        Write-Status "✓ Gmail credentials secret created"
    } else {
        Write-Warning "Gmail credential files not found. Please create them manually:"
        Write-Host "  kubectl create secret generic gmail-credentials --from-file=credentials.json=path/to/credentials.json --from-file=token.json=path/to/token.json -n $Namespace"
    }
    
    Write-Status "✓ Secrets created successfully"
}

# Deploy using Helm
function Start-Deployment {
    Write-Status "Starting Helm deployment..."
    
    $helmArgs = @()
    
    if ($DryRun) {
        $helmArgs += "--dry-run"
        $helmArgs += "--debug"
        Write-Status "Running in dry-run mode"
    }
    
    switch ($Action.ToLower()) {
        "install" {
            Write-Status "Installing $ReleaseName..."
            helm install $ReleaseName ./helm `
                --namespace $Namespace `
                --create-namespace `
                --values $ValuesFile `
                @helmArgs
        }
        
        "upgrade" {
            Write-Status "Upgrading $ReleaseName..."
            helm upgrade $ReleaseName ./helm `
                --namespace $Namespace `
                --values $ValuesFile `
                @helmArgs
        }
        
        "uninstall" {
            Write-Status "Uninstalling $ReleaseName..."
            helm uninstall $ReleaseName --namespace $Namespace
            return
        }
        
        "template" {
            Write-Status "Templating Helm chart..."
            helm template $ReleaseName ./helm `
                --namespace $Namespace `
                --values $ValuesFile `
                --debug
            return
        }
        
        default {
            Write-Error "Unknown action: $Action. Use: install, upgrade, uninstall, or template"
            exit 1
        }
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Helm command failed with exit code $LASTEXITCODE"
        exit 1
    }
}

# Check deployment status
function Get-DeploymentStatus {
    if ($Action -eq "uninstall" -or $Action -eq "template") {
        return
    }
    
    Write-Status "Checking deployment status..."
    
    # Wait for pods to be ready
    Write-Host "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=$ReleaseName -n $Namespace --timeout=300s
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "✓ All pods are ready"
        
        # Show pod status
        Write-Host "`nPod Status:"
        kubectl get pods -n $Namespace -l app.kubernetes.io/instance=$ReleaseName
        
        # Show services
        Write-Host "`nServices:"
        kubectl get svc -n $Namespace -l app.kubernetes.io/instance=$ReleaseName
        
        # Show ingress if available
        $ingress = kubectl get ingress -n $Namespace -l app.kubernetes.io/instance=$ReleaseName 2>$null
        if ($ingress) {
            Write-Host "`nIngress:"
            Write-Host $ingress
        }
        
        Write-Status "🎉 Deployment completed successfully!"
        Write-Host "`nNext steps:"
        Write-Host "1. Add entries to your hosts file for local development"
        Write-Host "2. Test the API endpoints"
        Write-Host "3. Check logs: kubectl logs -f deployment/<service-name> -n $Namespace"
        
    } else {
        Write-Error "Some pods failed to become ready. Check with: kubectl get pods -n $Namespace"
    }
}

# Main execution
try {
    Write-Status "StockRipper v2 Helm Deployment"
    Write-Host "Action: $Action | Namespace: $Namespace | Release: $ReleaseName"
    Write-Host ""
    
    Test-Prerequisites
    New-Secrets
    Start-Deployment
    Get-DeploymentStatus
    
} catch {
    Write-Error "Deployment failed: $($_.Exception.Message)"
    exit 1
}

# Contains AI-generated edits.
