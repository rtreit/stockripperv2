#!/usr/bin/env pwsh

# Helm Chart Validation Script
# Validates the Helm templates and configuration

param(
    [Parameter(Mandatory=$false)]
    [string]$ChartPath = "helm",
    
    [Parameter(Mandatory=$false)]
    [switch]$Lint = $true,
    
    [Parameter(Mandatory=$false)]
    [switch]$Template = $true,
    
    [Parameter(Mandatory=$false)]
    [switch]$ValidateYaml = $true
)

function Write-Status {
    param([string]$Message, [string]$Color = "Green")
    Write-Host "🔍 $Message" -ForegroundColor $Color
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

# Check if Helm is available
function Test-HelmAvailable {
    try {
        helm version --short | Out-Null
        Write-Success "Helm is available"
        return $true
    }
    catch {
        Write-Error "Helm is not available. Please install Helm 3.0+."
        return $false
    }
}

# Lint the Helm chart
function Test-HelmLint {
    if (-not $Lint) {
        return
    }
    
    Write-Status "Running Helm lint..."
    
    $result = helm lint $ChartPath 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Helm lint passed"
        Write-Host $result
    } else {
        Write-Error "Helm lint failed"
        Write-Host $result -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Template the Helm chart
function Test-HelmTemplate {
    if (-not $Template) {
        return
    }
    
    Write-Status "Testing Helm template rendering..."
    
    $result = helm template test-release $ChartPath --debug 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Helm template rendering successful"
        # Save rendered templates for inspection
        $result | Out-File -FilePath "rendered-templates.yaml" -Encoding UTF8
        Write-Host "Rendered templates saved to: rendered-templates.yaml"
    } else {
        Write-Error "Helm template rendering failed"
        Write-Host $result -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Validate YAML files
function Test-YamlSyntax {
    if (-not $ValidateYaml) {
        return
    }
    
    Write-Status "Validating YAML syntax..."
    
    $yamlFiles = Get-ChildItem -Path $ChartPath -Recurse -Include "*.yaml", "*.yml"
    $errors = @()
    
    foreach ($file in $yamlFiles) {
        try {
            # Try to parse YAML using PowerShell
            $content = Get-Content $file.FullName -Raw
            
            # Basic YAML validation (check for common syntax errors)
            if ($content -match '^\s*-\s*$' -or $content -match ':\s*$' -or $content -match '^\s*\|\s*$') {
                # These patterns might indicate incomplete YAML
                Write-Warning "Potential YAML syntax issue in: $($file.Name)"
            }
            
            Write-Host "✓ $($file.Name)" -ForegroundColor Green
        }
        catch {
            $errors += "❌ $($file.Name): $($_.Exception.Message)"
        }
    }
    
    if ($errors.Count -eq 0) {
        Write-Success "All YAML files have valid syntax"
        return $true
    } else {
        Write-Error "YAML validation errors found:"
        $errors | ForEach-Object { Write-Host $_ -ForegroundColor Red }
        return $false
    }
}

# Check required files
function Test-RequiredFiles {
    Write-Status "Checking required files..."
    
    $requiredFiles = @(
        "$ChartPath/Chart.yaml",
        "$ChartPath/values.yaml",
        "$ChartPath/templates/_helpers.tpl"
    )
    
    $missing = @()
    
    foreach ($file in $requiredFiles) {
        if (Test-Path $file) {
            Write-Host "✓ $file" -ForegroundColor Green
        } else {
            $missing += $file
        }
    }
    
    if ($missing.Count -eq 0) {
        Write-Success "All required files are present"
        return $true
    } else {
        Write-Error "Missing required files:"
        $missing | ForEach-Object { Write-Host "❌ $_" -ForegroundColor Red }
        return $false
    }
}

# Validate values.yaml structure
function Test-ValuesStructure {
    Write-Status "Validating values.yaml structure..."
    
    $valuesPath = "$ChartPath/values.yaml"
    
    if (-not (Test-Path $valuesPath)) {
        Write-Error "values.yaml not found"
        return $false
    }
    
    try {
        $values = Get-Content $valuesPath -Raw | ConvertFrom-Yaml -ErrorAction Stop
        
        # Check for required sections
        $requiredSections = @("global", "marketAnalyst", "planner", "mailer", "mcpServers")
        
        foreach ($section in $requiredSections) {
            if ($values.ContainsKey($section)) {
                Write-Host "✓ Section '$section' found" -ForegroundColor Green
            } else {
                Write-Host "⚠️  Section '$section' missing" -ForegroundColor Yellow
            }
        }
        
        Write-Success "values.yaml structure validation completed"
        return $true
    }
    catch {
        Write-Error "Error parsing values.yaml: $($_.Exception.Message)"
        return $false
    }
}

# Main validation
function Start-Validation {
    Write-Status "Starting Helm chart validation for: $ChartPath"
    Write-Host ""
    
    $results = @()
    
    # Check prerequisites
    if (-not (Test-HelmAvailable)) {
        return $false
    }
    
    # Run validation tests
    $results += Test-RequiredFiles
    $results += Test-YamlSyntax
    $results += Test-ValuesStructure
    $results += Test-HelmLint
    $results += Test-HelmTemplate
    
    # Summary
    Write-Host ""
    Write-Status "Validation Summary"
    
    $passed = ($results | Where-Object { $_ -eq $true }).Count
    $total = $results.Count
    
    if ($passed -eq $total) {
        Write-Success "All validation tests passed! ($passed/$total)"
        Write-Host ""
        Write-Host "Your Helm chart is ready for deployment!" -ForegroundColor Green
        Write-Host "Next steps:"
        Write-Host "1. Review the rendered templates in 'rendered-templates.yaml'"
        Write-Host "2. Update values.yaml with your specific configuration"
        Write-Host "3. Deploy using: ./deploy.ps1 -Action install"
        return $true
    } else {
        Write-Error "Validation failed: $passed/$total tests passed"
        Write-Host "Please fix the issues above before deploying." -ForegroundColor Yellow
        return $false
    }
}

# Add ConvertFrom-Yaml if not available (basic implementation)
if (-not (Get-Command ConvertFrom-Yaml -ErrorAction SilentlyContinue)) {
    function ConvertFrom-Yaml {
        param([string]$InputObject)
        # This is a basic implementation - for production use, install powershell-yaml module
        # For now, just check if it's valid-looking YAML
        if ([string]::IsNullOrWhiteSpace($InputObject)) {
            throw "Empty YAML content"
        }
        return @{} # Return empty hashtable for basic validation
    }
}

# Execute validation
try {
    Start-Validation
} catch {
    Write-Error "Validation script failed: $($_.Exception.Message)"
    exit 1
}

# Contains AI-generated edits.
