param(
    [ValidateSet("all", "build")]
    [string]$Mode = "all",
    [string]$RunId = "",
    [string]$BlenderExe = "",
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Config = Join-Path $RepoRoot "tools\blender_environment_factory\configs\cold_ancient_stone_v01.json"
$BlenderScript = Join-Path $RepoRoot "tools\blender_environment_factory\blender_environment_factory_v01.py"
$PostprocessScript = Join-Path $RepoRoot "tools\blender_environment_factory\postprocess_environment_run_v01.py"

if ([string]::IsNullOrWhiteSpace($RunId)) {
    $RunId = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
}
if ($RunId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$') {
    throw "RunId contains unsupported characters: $RunId"
}

function Resolve-BlenderExecutable {
    param([string]$Requested)
    if (-not [string]::IsNullOrWhiteSpace($Requested)) {
        if (-not (Test-Path -LiteralPath $Requested -PathType Leaf)) {
            throw "Blender executable was not found: $Requested"
        }
        return (Resolve-Path -LiteralPath $Requested).Path
    }
    $FromPath = Get-Command blender.exe -ErrorAction SilentlyContinue
    if ($null -eq $FromPath) {
        $FromPath = Get-Command blender -ErrorAction SilentlyContinue
    }
    if ($null -ne $FromPath) {
        return $FromPath.Source
    }
    $Candidates = @(
        "$env:ProgramFiles\Blender Foundation\Blender 5.2\blender.exe",
        "$env:ProgramFiles\Blender Foundation\Blender 5.1\blender.exe",
        "$env:ProgramFiles\Blender Foundation\Blender 5.0\blender.exe",
        "$env:ProgramFiles\Blender Foundation\Blender 4.5\blender.exe"
    )
    foreach ($Candidate in $Candidates) {
        if (Test-Path -LiteralPath $Candidate -PathType Leaf) {
            return $Candidate
        }
    }
    throw "Blender 5.2 LTS was not found. Pass -BlenderExe with an explicit path."
}

function Resolve-PythonExecutable {
    param([string]$Requested)
    if (-not [string]::IsNullOrWhiteSpace($Requested)) {
        return $Requested
    }
    $PyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($null -ne $PyLauncher) {
        return $PyLauncher.Source
    }
    $Python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($null -eq $Python) {
        $Python = Get-Command python -ErrorAction SilentlyContinue
    }
    if ($null -eq $Python) {
        throw "Python was not found for Pillow postprocessing."
    }
    return $Python.Source
}

$ResolvedBlender = Resolve-BlenderExecutable -Requested $BlenderExe
$RunDir = Join-Path $RepoRoot "art\blender_environment_runs\cold_ancient_stone_v01\$RunId"
if (Test-Path -LiteralPath $RunDir) {
    throw "Run directory already exists and will not be overwritten: $RunDir"
}

Write-Host "Blender Environment Factory v01"
Write-Host "Blender: $ResolvedBlender"
Write-Host "Run: $RunId"
Write-Host "Mode: $Mode"

& $ResolvedBlender `
    --background `
    --factory-startup `
    --python-exit-code 1 `
    --python $BlenderScript `
    -- `
    --repo-root $RepoRoot `
    --config $Config `
    --run-id $RunId `
    --mode $Mode
if ($LASTEXITCODE -ne 0) {
    throw "Blender Environment Factory failed with exit code $LASTEXITCODE"
}

if ($Mode -eq "all") {
    $ResolvedPython = Resolve-PythonExecutable -Requested $PythonExe
    & $ResolvedPython $PostprocessScript `
        --repo-root $RepoRoot `
        --config $Config `
        --run-dir $RunDir
    if ($LASTEXITCODE -ne 0) {
        throw "Environment postprocessing failed with exit code $LASTEXITCODE"
    }
}

Write-Host "Result: $RunDir"
