param(
    [string]$BlenderExe = "",
    [string]$OutputRoot = "",
    [switch]$RenderPreview,
    [switch]$RenderAnimation,
    [int]$Resolution = 720,
    [int]$AnimationResolution = 360,
    [int]$SampleStep = 2,
    [int]$VideoBitrate = 4500
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
    "--python-exit-code", "1",
    "--python", (Join-Path $ToolRoot "heart_cycle_animation_export_v07.py"),
    "--",
    "--output-root", $OutputRoot,
    "--resolution", $Resolution,
    "--animation-resolution", $AnimationResolution,
    "--sample-step", $SampleStep,
    "--video-bitrate", $VideoBitrate
)
if ($RenderPreview) { $Arguments += "--render-preview" }
if ($RenderAnimation) { $Arguments += "--render-animation" }

Write-Host "Blender:     $BlenderExe"
Write-Host "Output:      $OutputRoot"
Write-Host "Stage:       heart_cycle_animation_export_v07"
Write-Host "Preview:     ${Resolution}p"
Write-Host "Animation:   ${AnimationResolution}p, sample step $SampleStep"
& $BlenderExe @Arguments
if ($LASTEXITCODE -ne 0) {
    throw "Blender heart-cycle frame render failed with exit code $LASTEXITCODE"
}

if ($RenderAnimation) {
    $FrameRoot = Join-Path $OutputRoot "review_frames"
    $Frames = @(Get-ChildItem -Path $FrameRoot -Filter "heart_cycle_review_*.png" | Sort-Object Name)
    $ExpectedFrames = [int](450 / $SampleStep)
    if ($Frames.Count -ne $ExpectedFrames) {
        throw "Expected $ExpectedFrames rendered frames, found $($Frames.Count)."
    }

    $FfmpegCommand = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if (-not $FfmpegCommand) {
        Write-Warning "FFmpeg is not installed. The complete PNG sequence is available at $FrameRoot."
        Write-Warning "The GitHub animation workflow will encode the MP4 and GIF automatically."
        exit 0
    }

    $OutputFps = [int](30 / $SampleStep)
    $EncodeRoot = Join-Path $OutputRoot "review_frames_encode"
    if (Test-Path $EncodeRoot) { Remove-Item $EncodeRoot -Recurse -Force }
    New-Item -ItemType Directory -Path $EncodeRoot | Out-Null

    try {
        for ($Index = 0; $Index -lt $Frames.Count; $Index++) {
            $Target = Join-Path $EncodeRoot ("frame_{0:D4}.png" -f ($Index + 1))
            Copy-Item $Frames[$Index].FullName $Target
        }

        $VideoPath = Join-Path $OutputRoot "heart_cycle_review_v07.mp4"
        & $FfmpegCommand.Source -y `
            -framerate $OutputFps `
            -i (Join-Path $EncodeRoot "frame_%04d.png") `
            -c:v libx264 `
            -pix_fmt yuv420p `
            -b:v ("{0}k" -f $VideoBitrate) `
            -movflags +faststart `
            $VideoPath
        if ($LASTEXITCODE -ne 0) {
            throw "FFmpeg MP4 encoding failed with exit code $LASTEXITCODE"
        }
        Write-Host "MP4:         $VideoPath"
    }
    finally {
        if (Test-Path $EncodeRoot) { Remove-Item $EncodeRoot -Recurse -Force }
    }
}
