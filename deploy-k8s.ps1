#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy StockRipper v2 to local Kubernetes cluster

.DESCRIPTION
    This script builds Docker images for all agents and deploys them to the local Kubernetes cluster.
    It handles the complete deployment process including secrets, configmaps, and health checks.
#>

param(
    [switch]$Build = $true,
    [switch]$Deploy = $true,
    [switch]$Test = $true,
    [string]$Namespace = "stockripper"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 StockRipper v2 - Kubernetes Deployment Script" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Configuration
$ImageTag = "latest"
$Images = @{
    "stockripper/market-analyst" = @{
        "context" = "."
        "dockerfile" = "agents/market_analyst/Dockerfile"
        "command" = "python run_market_analyst.py"
    }
    "stockripper/planner" = @{
        "context" = "."
        "dockerfile" = "agents/planner/Dockerfile"
        "command" = "python run_planner.py"
    }
    "stockripper/mailer" = @{
        "context" = "."
        "dockerfile" = "agents/mailer/Dockerfile"
        "command" = "python run_mailer.py"
    }
}

function Write-Step {
    param([string]$Message)
    Write-Host "📋 $Message" -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

# Step 1: Build Docker Images
if ($Build) {
    Write-Step "Building Docker images..."
    
    foreach ($image in $Images.Keys) {
        Write-Host "🔨 Building $image..."
        
        $config = $Images[$image]
        $dockerCommand = "docker build -t ${image}:${ImageTag} -f $($config.dockerfile) $($config.context)"
        
        try {
            Invoke-Expression $dockerCommand
            Write-Success "Built $image successfully"
        }
        catch {
            Write-Error "Failed to build $image`: $_"
            exit 1
        }
    }
}

# Step 2: Create namespace and secrets
if ($Deploy) {
    Write-Step "Setting up Kubernetes namespace and secrets..."
    
    # Create namespace
    kubectl create namespace $Namespace --dry-run=client -o yaml | kubectl apply -f -
    
    # Check if secrets exist
    $secretsExist = $true
    try {
        kubectl get secret stockripper-secrets -n $Namespace | Out-Null
    }
    catch {
        $secretsExist = $false
    }
    
    if (-not $secretsExist) {
        Write-Host "⚠️  Creating secrets from environment variables. Update environment for real deployment!"
        
        # Create secrets from environment or placeholders
        $openaiKey = $env:OPENAI_API_KEY
        if (-not $openaiKey) {
            $openaiKey = "your-openai-api-key-here"
            Write-Host "⚠️  Using placeholder OPENAI_API_KEY. Set environment variable for real deployment."
        }
        
        $alpacaApiKey = $env:ALPACA_API_KEY
        if (-not $alpacaApiKey) {
            $alpacaApiKey = "your-alpaca-api-key-here"
            Write-Host "⚠️  Using placeholder ALPACA_API_KEY. Set environment variable for real deployment."
        }
        
        $alpacaSecretKey = $env:ALPACA_SECRET_KEY
        if (-not $alpacaSecretKey) {
            $alpacaSecretKey = "your-alpaca-secret-key-here"
            Write-Host "⚠️  Using placeholder ALPACA_SECRET_KEY. Set environment variable for real deployment."
        }
        
        kubectl create secret generic stockripper-secrets -n $Namespace `
            --from-literal=openai-api-key=$openaiKey `
            --from-literal=alpaca-api-key=$alpacaApiKey `
            --from-literal=alpaca-secret-key=$alpacaSecretKey `
            --from-literal=default-email-recipient="randyt@outlook.com"
        
        Write-Success "Created secrets"
    }
    
    # Step 3: Deploy Helm chart
    Write-Step "Deploying with Helm..."
    
    try {
        helm upgrade --install stockripper ./helm `
            --namespace $Namespace `
            --set global.imageRegistry="" `
            --set marketAnalyst.image.repository="stockripper/market-analyst" `
            --set marketAnalyst.image.tag=$ImageTag `
            --set planner.image.repository="stockripper/planner" `
            --set planner.image.tag=$ImageTag `
            --set mailer.image.repository="stockripper/mailer" `
            --set mailer.image.tag=$ImageTag `
            --wait --timeout=300s
        
        Write-Success "Helm deployment completed"
    }
    catch {
        Write-Error "Helm deployment failed: $_"
        exit 1
    }
    
    # Step 4: Wait for pods to be ready
    Write-Step "Waiting for pods to be ready..."
    
    $timeout = 300  # 5 minutes
    $elapsed = 0
    $checkInterval = 10
    
    while ($elapsed -lt $timeout) {
        $readyPods = kubectl get pods -n $Namespace -o jsonpath='{.items[*].status.phase}' | ForEach-Object { $_.Split(' ') | Where-Object { $_ -eq 'Running' } }
        $totalPods = kubectl get pods -n $Namespace --no-headers | Measure-Object | Select-Object -ExpandProperty Count
        
        if ($readyPods.Count -eq $totalPods -and $totalPods -gt 0) {
            Write-Success "All pods are ready!"
            break
        }
        
        Write-Host "⏳ Waiting for pods... ($($readyPods.Count)/$totalPods ready)"
        Start-Sleep $checkInterval
        $elapsed += $checkInterval
    }
    
    if ($elapsed -ge $timeout) {
        Write-Error "Timeout waiting for pods to be ready"
        kubectl get pods -n $Namespace
        exit 1
    }
    
    # Show deployment status
    Write-Step "Deployment Status:"
    kubectl get all -n $Namespace
}

# Step 5: Run end-to-end tests
if ($Test) {
    Write-Step "Setting up port forwarding and running tests..."
    
    # Port forward to access services
    Write-Host "🔗 Setting up port forwarding..."
    
    $portForwards = @()
    
    try {
        # Market Analyst
        $pf1 = Start-Process kubectl -ArgumentList "port-forward -n $Namespace svc/market-analyst 8001:8001" -PassThru -WindowStyle Hidden
        $portForwards += $pf1
        
        # Planner
        $pf2 = Start-Process kubectl -ArgumentList "port-forward -n $Namespace svc/planner 8002:8002" -PassThru -WindowStyle Hidden
        $portForwards += $pf2
        
        # Mailer
        $pf3 = Start-Process kubectl -ArgumentList "port-forward -n $Namespace svc/mailer 8003:8003" -PassThru -WindowStyle Hidden
        $portForwards += $pf3
        
        Write-Success "Port forwarding established"
        Write-Host "⏳ Waiting 15 seconds for services to be accessible..."
        Start-Sleep 15
        
        # Run tests
        Write-Step "Running end-to-end tests against Kubernetes deployment..."
        
        $testResult = python tests/e2e/test_complete_workflow.py
        $testExitCode = $LASTEXITCODE
        
        if ($testExitCode -eq 0) {
            Write-Success "🎉 End-to-end tests PASSED! StockRipper v2 is working in Kubernetes!"
        }
        else {
            Write-Error "❌ End-to-end tests FAILED!"
            exit 1
        }
    }
    finally {
        # Clean up port forwards
        Write-Host "🧹 Cleaning up port forwards..."
        foreach ($pf in $portForwards) {
            if ($pf -and -not $pf.HasExited) {
                Stop-Process -Id $pf.Id -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

Write-Host ""
Write-Success "🎊 StockRipper v2 deployment completed successfully!"
Write-Host "Access your services using kubectl port-forward:"
Write-Host "  kubectl port-forward -n $Namespace svc/market-analyst 8001:8001"
Write-Host "  kubectl port-forward -n $Namespace svc/planner 8002:8002"  
Write-Host "  kubectl port-forward -n $Namespace svc/mailer 8003:8003"
Write-Host ""
Write-Host "To run tests: python tests/e2e/test_complete_workflow.py"
Write-Host "To check status: kubectl get all -n $Namespace"
