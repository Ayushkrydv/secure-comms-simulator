# ============================================================
#  publish_to_github.ps1
#  Run from:  C:\Users\HP\001\secure_comms\
# ============================================================

$repoName    = "secure-comms-simulator"
$repoDesc    = "Secure Tactical Communication Simulation System - College Project"
$repoPrivate = $false
$branch      = "main"

Write-Host ""
Write-Host "============================================" -ForegroundColor Yellow
Write-Host "  Secure Comms Simulator - GitHub Publisher" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Create a token at: https://github.com/settings/tokens" -ForegroundColor Cyan
Write-Host "Required scope  : repo (full control)" -ForegroundColor Cyan
Write-Host ""

$tokenSecure = Read-Host "Paste your GitHub token" -AsSecureString
$tokenPlain  = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($tokenSecure))

$headers = @{ Authorization = "token $tokenPlain"; Accept = "application/vnd.github+json" }

# Verify token
Write-Host "`n>> Verifying token..." -ForegroundColor Cyan
$userResp = Invoke-RestMethod -Uri "https://api.github.com/user" -Headers $headers
$githubUser = $userResp.login
Write-Host "   [OK] Logged in as: $githubUser" -ForegroundColor Green

# Create repo (skip if exists)
Write-Host "`n>> Creating repository '$repoName'..." -ForegroundColor Cyan
$checkUri = "https://api.github.com/repos/$githubUser/$repoName"
$exists = $false
try { Invoke-RestMethod -Uri $checkUri -Headers $headers | Out-Null; $exists = $true } catch { $exists = $false }

if ($exists) {
    Write-Host "   [OK] Repository already exists - skipping creation." -ForegroundColor Green
} else {
    $body = "{`"name`":`"$repoName`",`"description`":`"$repoDesc`",`"private`":$($repoPrivate.ToString().ToLower()),`"auto_init`":false}"
    Invoke-RestMethod -Uri "https://api.github.com/user/repos" -Method POST -Headers $headers -ContentType "application/json" -Body $body | Out-Null
    Write-Host "   [OK] Repository created." -ForegroundColor Green
}

# Git init
Write-Host "`n>> Initialising git..." -ForegroundColor Cyan
if (-not (Test-Path ".git")) { git init | Out-Null }
Write-Host "   [OK] Git ready." -ForegroundColor Green

# Branch
git checkout -b $branch 2>$null
if ($LASTEXITCODE -ne 0) { git checkout $branch 2>$null }
Write-Host "   [OK] Branch: $branch" -ForegroundColor Green

# Stage
Write-Host "`n>> Staging files..." -ForegroundColor Cyan
git add .
Write-Host "   [OK] Files staged." -ForegroundColor Green

# Commit
Write-Host "`n>> Committing..." -ForegroundColor Cyan
$st = git status --porcelain
if ($st) {
    git commit -m "Initial commit: Secure Tactical Communication Simulator"
    Write-Host "   [OK] Commit created." -ForegroundColor Green
} else {
    Write-Host "   [OK] Nothing new to commit." -ForegroundColor Green
}

# Remote
Write-Host "`n>> Setting remote origin..." -ForegroundColor Cyan
$remoteUrl = "https://$tokenPlain@github.com/$githubUser/$repoName.git"
$remotes = git remote
if ($remotes -contains "origin") {
    git remote set-url origin $remoteUrl
} else {
    git remote add origin $remoteUrl
}
Write-Host "   [OK] Remote set." -ForegroundColor Green

# Push
Write-Host "`n>> Pushing to GitHub..." -ForegroundColor Cyan
git push -u origin $branch --force
if ($LASTEXITCODE -eq 0) {
    Write-Host "   [OK] Push successful!" -ForegroundColor Green
} else {
    Write-Host "   [FAIL] Push failed. Check token permissions." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Done! View your repo at:" -ForegroundColor Green
Write-Host "  https://github.com/$githubUser/$repoName" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
