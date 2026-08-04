param(
    [string]$BlenderExe = "",
    [string]$OutputRoot = "",
    [switch]$RenderPreview,
    [switch]$RenderAnimation
)

$ErrorActionPreference = "Stop"
$ToolRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ToolRoot "..\..")

if (-not $BlenderExe) {
    $Candidates = @(
        "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
        "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
        "C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
    )
    $BlenderExe = $Candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $BlenderExe -or -not (Test-Path $BlenderExe)) {
    throw "Blender executable not found. Pass -BlenderExe explicitly."
}

if (-not $OutputRoot) {
    $OutputRoot = Join-Path $RepoRoot "artifacts\blender_heart_cycle"
}

$Arguments = @(
    "--background",
    "--factory-startup",
    "--python", (Join-Path $ToolRoot "heart_cycle_model.py"),
    "--",
    "--output-root", $OutputRoot
)
if ($RenderPreview) { $Arguments += "--render-preview" }
if ($RenderAnimation) { $Arguments += "--render-animation" }

Write-Host "Blender: $BlenderExe"
Write-Host "Output:  $OutputRoot"
& $BlenderExe @Arguments
if ($LASTEXITCODE -ne 0) {
    throw "Blender heart-cycle build failed with exit code $LASTEXITCODE"
}
