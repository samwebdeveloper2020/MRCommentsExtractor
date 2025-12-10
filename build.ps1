# Build script for GitLab MR Viewer executable

Write-Host "Building GitLab MR Viewer executable..." -ForegroundColor Green

# Clean previous builds
if (Test-Path "build") {
    Write-Host "Cleaning build folder..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force build
}
if (Test-Path "dist") {
    Write-Host "Cleaning dist folder..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force dist
}

# Build executable
Write-Host "`nBuilding executable with PyInstaller..." -ForegroundColor Green
C:/ProgramData/anaconda3/Scripts/conda.exe run -p c:\Satish\AI\MRComments_Extractor\.conda pyinstaller GitLabMRViewer.spec

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Build successful!" -ForegroundColor Green
    Write-Host "`nExecutable location: dist\GitLabMRViewer.exe" -ForegroundColor Cyan
    
    # Create distribution package
    Write-Host "`nCreating distribution package..." -ForegroundColor Green
    
    $distFolder = "dist\GitLabMRViewer-Package"
    New-Item -ItemType Directory -Force -Path $distFolder | Out-Null
    
    # Copy executable
    Copy-Item "dist\GitLabMRViewer.exe" "$distFolder\"
    
    # Create token template files
    @{} | ConvertTo-Json | Out-File "$distFolder\token.json.template" -Encoding UTF8
    @{} | ConvertTo-Json | Out-File "$distFolder\llm_token.json.template" -Encoding UTF8
    
    # Copy README
    if (Test-Path "DISTRIBUTION_README.md") {
        Copy-Item "DISTRIBUTION_README.md" "$distFolder\README.md"
    }
    
    Write-Host "`n✓ Distribution package created in: $distFolder" -ForegroundColor Green
    Write-Host "`nYou can now zip this folder and distribute it!" -ForegroundColor Cyan
} else {
    Write-Host "`n✗ Build failed!" -ForegroundColor Red
    exit 1
}
