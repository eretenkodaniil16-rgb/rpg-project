[CmdletBinding()]
param(
    [string]$BlenderExe = "",
    [ValidateSet("all", "build")]
    [string]$Mode = "all",
    [ValidateSet("walk_v16", "attack_down_keyposes_v17", "attack_down_keyposes_v18", "attack_down_keyposes_v19", "attack_down_cycle_v20")]
    [string]$Stage = "walk_v16",
    [string]$RunId = ""
)

# Windows PowerShell 5.1 decodes UTF-8 files without a BOM through the active
# system code page. Keep this launcher ASCII-only so parsing never depends on
# the Windows locale. Paths passed in variables can still contain Unicode.
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ToolRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ToolRoot "..\..")).Path
# Historical rejected adapter: blender_sprite_factory_combat_idle_down_weapon_variants_v05.py
# Previous mixed candidate: blender_sprite_factory_combat_idle_down_weapon_variants_v06.py
# Rejected occluded one-hand candidate: blender_sprite_factory_combat_idle_down_weapon_variants_v07.py
# Rejected cross-torso one-hand candidate: blender_sprite_factory_combat_idle_down_weapon_variants_v08.py
# Selected static source adapter: blender_sprite_factory_combat_idle_down_weapon_variants_v09.py
# Artist-approved down cycles: blender_sprite_factory_combat_idle_down_cycles_v10.py
# Rejected raw directional rotation: blender_sprite_factory_combat_idle_directional_v11.py
# Artist-approved directional source: blender_sprite_factory_combat_idle_directional_weapon_v12.py
# Rejected boundary-touch experiment: blender_sprite_factory_combat_idle_directional_weapon_v13.py
# Artist-approved directional combat idle cycles: blender_sprite_factory_combat_idle_directional_cycles_v14.py
# Armed walk animation actions: blender_sprite_factory_walk_directional_weapon_v15.py
$FactoryScript = Join-Path $ToolRoot "blender_sprite_factory_walk_directional_weapon_render_v16.py"
$ReviewFile = "walk_directional_weapon_v15.png"
if ($Stage -eq "attack_down_keyposes_v17") {
    $FactoryScript = Join-Path $ToolRoot "blender_sprite_factory_attack_sword_down_keyposes_v17.py"
    $ReviewFile = "attack_sword_01_down_keyposes_v17.png"
}
if ($Stage -eq "attack_down_keyposes_v18") {
    $FactoryScript = Join-Path $ToolRoot "blender_sprite_factory_attack_sword_down_keyposes_v18.py"
    $ReviewFile = "attack_sword_01_down_keyposes_v18.png"
}
if ($Stage -eq "attack_down_keyposes_v19") {
    $FactoryScript = Join-Path $ToolRoot "blender_sprite_factory_attack_sword_down_keyposes_v19_pass07.py"
    $ReviewFile = "attack_sword_01_down_keyposes_v19.png"
}
if ($Stage -eq "attack_down_cycle_v20") {
    $FactoryScript = Join-Path $ToolRoot "blender_sprite_factory_attack_sword_down_cycle_v20_pass03.py"
    $ReviewFile = "attack_sword_01_down_cycle_v20.png"
}
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
Write-Host "Stage: $Stage"
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
Write-Host "Review $ReviewFile and the generated .blend file in source."
