$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectRoot

$env:MYSQL_HOST = Read-Host "MySQL host (Enter para 127.0.0.1)"
if ([string]::IsNullOrWhiteSpace($env:MYSQL_HOST)) {
    $env:MYSQL_HOST = "127.0.0.1"
}
$env:MYSQL_PORT = Read-Host "MySQL port (Enter para 3306)"
if ([string]::IsNullOrWhiteSpace($env:MYSQL_PORT)) {
    $env:MYSQL_PORT = "3306"
}
$env:MYSQL_DATABASE = Read-Host "Database (Enter para wprbench)"
if ([string]::IsNullOrWhiteSpace($env:MYSQL_DATABASE)) {
    $env:MYSQL_DATABASE = "wprbench"
}
$env:MYSQL_USER = Read-Host "MySQL user (Enter para root)"
if ([string]::IsNullOrWhiteSpace($env:MYSQL_USER)) {
    $env:MYSQL_USER = "root"
}
$securePassword = Read-Host "MySQL password" -AsSecureString
$passwordPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
try {
    $env:MYSQL_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPointer)
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPointer)
}

& "$projectRoot\.venv\Scripts\python.exe" -m uvicorn api_server:app --host 0.0.0.0 --port 8765
exit $LASTEXITCODE
