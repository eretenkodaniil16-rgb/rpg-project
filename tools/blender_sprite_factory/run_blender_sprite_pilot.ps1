[CmdletBinding()]
param(
    [string]$BlenderExe = "",
    [ValidateSet("all", "build")]
    [string]$Mode = "all",
    [string]$RunId = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ToolRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ToolRoot "..\..")).Path
$FactoryScript = Join-Path $ToolRoot "blender_sprite_factory.py"
$FactoryConfig = Join-Path $ToolRoot "configs\human_warrior_m01.json"

function Resolve-BlenderExecutable {
    param([string]$ExplicitPath)

    if ($ExplicitPath) {
        if (-not (Test-Path -LiteralPath $ExplicitPath -PathType Leaf)) {
            throw "Blender не найден по указанному пути: $ExplicitPath"
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
Blender не найден.
Установите Blender 5.2 LTS с https://www.blender.org/download/lts/
или запустите:
  .\tools\blender_sprite_factory\run_blender_sprite_pilot.ps1 -BlenderExe "C:\путь\к\blender.exe"
"@
}

$ResolvedBlender = Resolve-BlenderExecutable -ExplicitPath $BlenderExe
if (-not $RunId) {
    $RunId = Get-Date -Format "yyyyMMddTHHmmss"
}

Write-Host "Blender: $ResolvedBlender"
Write-Host "Режим: $Mode"
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
    throw "Blender sprite factory завершился с кодом $LASTEXITCODE."
}

$ResultRoot = Join-Path $RepoRoot "art\blender_pipeline_runs\human_warrior_m01\$RunId"
Write-Host ""
Write-Host "Готово: $ResultRoot"
Write-Host "Для проверки откройте contact_sheet.png и source\human_warrior_m01_proxy_v01.blend."
