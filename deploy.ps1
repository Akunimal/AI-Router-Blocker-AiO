$ErrorActionPreference = "Stop"

.\.venv\Scripts\python.exe -m PyInstaller `
    --onefile `
    --windowed `
    --uac-admin `
    --add-data "translations.json;." `
    --add-data "icon.ico;." `
    --add-data "icon_green.ico;." `
    --add-data "icon_red.ico;." `
    --name "CodeGate" `
    --clean `
    ai_blocker.py

Copy-Item "dist\CodeGate.exe" "CodeGate.exe" -Force

Write-Host "Windows build complete: CodeGate.exe"
Write-Host "Publish cross-platform releases from GitHub by creating a versioned release tag, for example v1.2.1."
