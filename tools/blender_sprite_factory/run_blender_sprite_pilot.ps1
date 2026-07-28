[CmdletBinding()]
param(
    [string]$BlenderExe = "",
    [ValidateSet("all", "build")]
    [string]$Mode = "all",
    [string]$RunId = ""
)

# Windows PowerShell 5.1 decodes UTF-8 files without a BOM through the active
# system code page. Keep this launcher ASCII-only so parsing never depends on
# the Windows locale. Paths passed in variables can still contain Unicode.
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ToolRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ToolRoot "..\..")).Path
$FactoryScript = Join-Path $ToolRoot "blender_sprite_factory_head_v18.py"
$FactoryConfig = Join-Path $ToolRoot "configs\human_warrior_m01.json"

function Resolve-BlenderExecutable {
    param([string]$ExplicitPath)

    if ($ExplicitPath) {
        if (-not (Test-Path -LiteralPath $ExplicitPath -PathType Leaf)) {
            throw "Blender was not found at the specified path: $ExplicitPath"
        }
        return (Resolve-Path -LiteralPath $ExplicitPath).Path
    }

    if ($env:BLENDER_EXE) {
        if (Test-Path -LiteralPath $env:BLENDER_EXE -PathType Leaf) {
            return (Resolve-Path -LiteralPath $env:BLENDER_EXE).Path
        }
    }

    $Command = Get-Command blender.exe -ErrorAction SilentlyContinue
    if ($Command) {
        return $Command.Source
    }

    $Candidates = @(
        "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
        "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe",
        "C:\Program Files\Blender Foundation\Blender 5.0\blender.exe",
        "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
    )
    $Candidates += Get-ChildItem `
        -Path "C:\Program Files\Blender Foundation" `
        -Filter "blender.exe" `
        -File `
        -Recurse `
        -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending |
        Select-Object -ExpandProperty FullName

    foreach ($Candidate in $Candidates) {
        if ($Candidate -and (Test-Path -LiteralPath $Candidate -PathType Leaf)) {
            return (Resolve-Path -LiteralPath $Candidate).Path
        }
    }

    throw @"
Blender was not found.
Install Blender 5.2 LTS from https://www.blender.org/download/lts/
or run:
  .\tools\blender_sprite_factory\run_blender_sprite_pilot.ps1 -BlenderExe "C:\path\to\blender.exe"
"@
}

$ResolvedBlender = Resolve-BlenderExecutable -ExplicitPath $BlenderExe
if (-not $RunId) {
    $RunId = Get-Date -Format "yyyyMMddTHHmmss"
}

Write-Host "Blender: $ResolvedBlender"
Write-Host "Mode: $Mode"
Write-Host "Run ID: $RunId"

& $ResolvedBlender `
    --background `
    --factory-startup `
    --python-exit-code 1 `
    --python $FactoryScript `
    -- `
    --repo-root $RepoRoot `
    --config $FactoryConfig `
    --run-id $RunId `
    --mode $Mode

if ($LASTEXITCODE -ne 0) {
    throw "Blender sprite factory exited with code $LASTEXITCODE."
}

$ResultRoot = Join-Path $RepoRoot "art\blender_pipeline_runs\human_warrior_m01\$RunId"
Write-Host ""
Write-Host "Completed: $ResultRoot"
Write-Host "Review contact_sheet.png and the generated .blend file in source\."
