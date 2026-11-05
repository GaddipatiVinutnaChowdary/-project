$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$environmentFile = Join-Path $PSScriptRoot '.env'
if (Test-Path -LiteralPath $environmentFile) {
    foreach ($configLine in Get-Content -LiteralPath $environmentFile) {
        $configLine = $configLine.Trim()
        if ([string]::IsNullOrWhiteSpace($configLine) -or $configLine.StartsWith('#')) { continue }
        $configParts = $configLine -split '=', 2
        if ($configParts.Length -ne 2) { continue }
        $environmentName = $configParts[0].Trim()
        $environmentValue = $configParts[1].Trim()
        if ($environmentValue.Length -ge 2 -and (($environmentValue.StartsWith('"') -and $environmentValue.EndsWith('"')) -or ($environmentValue.StartsWith("'") -and $environmentValue.EndsWith("'")))) {
            $environmentValue = $environmentValue.Substring(1, $environmentValue.Length - 2)
        }
        if ($environmentName -match '^[A-Za-z_][A-Za-z0-9_]*$') {
            Set-Item -Path "Env:$environmentName" -Value $environmentValue
        }
    }
}
if (-not $env:APP_ENV) { $env:APP_ENV = 'development' }
$bindHost = if ($env:HOST) { $env:HOST } else { '127.0.0.1' }
$bindPort = if ($env:PORT) { $env:PORT } else { '8000' }
python -m uvicorn server:app --host $bindHost --port $bindPort
