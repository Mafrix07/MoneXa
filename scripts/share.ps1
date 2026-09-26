#Requires -Version 5.1
param([switch]$Start)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Get-LanIps {
    Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -ne 'WellKnown' } |
        Select-Object -ExpandProperty IPAddress
}

Write-Host "Django doit ecouter 0.0.0.0:8000  (runserver 0.0.0.0:8000)"

$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($docker) {
    Write-Host "Nginx : docker compose -f docker-compose.gateway.yml up"
} else {
    Write-Host "Docker absent : Nginx portable Windows (tools/nginx) via ce script."
}

$addrs = Get-LanIps
Write-Host ""
if ($addrs) {
    foreach ($ip in $addrs) {
        Write-Host "Lien equipe (meme Wi-Fi) : http://$ip/"
        Write-Host "Sans Nginx (port Django) : http://${ip}:8000/"
    }
} else {
    Write-Host "Aucune IPv4 LAN detectee."
}

Write-Host ""
Write-Host "Lien Internet : docker compose -f docker-compose.gateway.yml --profile share up"
Write-Host "ou cloudflared tunnel --url http://127.0.0.1/"
Write-Host "Puis lis l'URL https://*.trycloudflare.com dans les logs."

$installNginx = $Start
if (-not $installNginx) { exit 0 }

$tools = Join-Path $Root "tools"
$nginxDir = Join-Path $tools "nginx"
$nginxExe = Join-Path $nginxDir "nginx.exe"
if (-not (Test-Path $nginxExe)) {
    New-Item -ItemType Directory -Force -Path $tools | Out-Null
    $zip = Join-Path $tools "nginx.zip"
    Write-Host "Telechargement de Nginx Windows..."
    curl.exe -L --connect-timeout 20 --max-time 120 -o $zip "https://nginx.org/download/nginx-1.26.3.zip"
    Expand-Archive -Path $zip -DestinationPath $tools -Force
    $extracted = Get-ChildItem $tools -Directory | Where-Object { $_.Name -like "nginx-*" } | Select-Object -First 1
    if (-not $extracted) { throw "Archive Nginx inattendue." }
    if (Test-Path $nginxDir) { Remove-Item $nginxDir -Recurse -Force }
    Rename-Item $extracted.FullName $nginxDir
    Remove-Item $zip -Force
}

Copy-Item (Join-Path $Root "infra\nginx\nginx-windows.conf") (Join-Path $nginxDir "conf\nginx.conf") -Force
New-Item -ItemType Directory -Force -Path (Join-Path $nginxDir "logs") | Out-Null

Push-Location $nginxDir
try {
    & .\nginx.exe -s quit 2>$null
    Start-Sleep -Seconds 1
} catch { }
& .\nginx.exe
Pop-Location
Write-Host "Nginx demarre. Teste http://127.0.0.1/"
