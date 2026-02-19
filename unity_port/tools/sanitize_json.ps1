param(
    [string]$InputPath = "c:/workspace/data.json",
    [string]$OutputPath = "c:/workspace/unity_port/Assets/StreamingAssets/data.unity.json"
)

if (!(Test-Path $InputPath)) {
    throw "Input JSON not found: $InputPath"
}

$text = Get-Content -Raw -Encoding UTF8 $InputPath
$sb = New-Object System.Text.StringBuilder

foreach ($ch in $text.ToCharArray()) {
    $code = [int][char]$ch
    if ($code -le 127) {
        [void]$sb.Append($ch)
    }
    else {
        [void]$sb.AppendFormat('\\u{0:x4}', $code)
    }
}

$targetDir = Split-Path -Parent $OutputPath
if (!(Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($OutputPath, $sb.ToString(), $utf8NoBom)

$decoded = [System.Text.Encoding]::UTF8.GetString([System.IO.File]::ReadAllBytes($OutputPath))
$null = $decoded | ConvertFrom-Json

Write-Host "Sanitized JSON generated: $OutputPath"
