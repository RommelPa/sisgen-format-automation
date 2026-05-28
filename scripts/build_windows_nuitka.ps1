$ErrorActionPreference = "Stop"

Write-Host "Cleaning previous Nuitka build..."
Remove-Item dist-nuitka -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Building SISGEN desktop with Nuitka..."
python -m nuitka `
  --standalone `
  --mingw64 `
  --enable-plugin=pyside6 `
  --windows-console-mode=disable `
  --output-dir=dist-nuitka `
  --output-filename=SISGEN-Format-Automation.exe `
  run_desktop.py

Write-Host ""
Write-Host "Build completed:"
Write-Host "dist-nuitka\run_desktop.dist\SISGEN-Format-Automation.exe"
