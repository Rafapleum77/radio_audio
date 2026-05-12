# Autoriza chave SSH do Claude (Mac) e mostra info pra conectar.
# Rodar com PowerShell em modo Administrador.
$k = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILrk7w6ZtXgd3k1YinwCW9/6ba5hlr+Zn96X5VtssHBU claude-mac'

# Caminhos: admin usa administrators_authorized_keys, user normal usa $HOME\.ssh\authorized_keys
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]"Administrator")

if ($isAdmin) {
    $path = "$env:ProgramData\ssh\administrators_authorized_keys"
    New-Item -ItemType Directory -Force -Path (Split-Path $path) | Out-Null
    if (-not (Get-Content $path -ErrorAction SilentlyContinue | Select-String -SimpleMatch $k)) {
        Add-Content -Path $path -Value $k
    }
    icacls $path /inheritance:r /grant "Administrators:F" /grant "SYSTEM:F" | Out-Null
} else {
    $path = "$env:USERPROFILE\.ssh\authorized_keys"
    New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh" | Out-Null
    if (-not (Get-Content $path -ErrorAction SilentlyContinue | Select-String -SimpleMatch $k)) {
        Add-Content -Path $path -Value $k
    }
    icacls $path /inheritance:r /grant "$($env:USERNAME):F" | Out-Null
}

# Garante OpenSSH Server instalado e rodando
$ssh = Get-Service sshd -ErrorAction SilentlyContinue
if ($ssh) {
    Set-Service sshd -StartupType Automatic
    Restart-Service sshd
    Write-Host "OpenSSH Server: OK"
} else {
    Write-Host "OpenSSH Server NAO instalado. Instalando..." -ForegroundColor Yellow
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 | Out-Null
    Start-Service sshd
    Set-Service sshd -StartupType Automatic
    Write-Host "OpenSSH instalado e iniciado."
}

# Mostra info pra conectar
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*"} | Select-Object -First 1).IPAddress
Write-Host ""
Write-Host "=== CONECTE AQUI ===" -ForegroundColor Cyan
Write-Host "Usuario : $env:USERNAME"
Write-Host "Hostname: $env:COMPUTERNAME"
Write-Host "IP local: $ip"
Write-Host "Admin   : $isAdmin"
Write-Host "Chave em: $path"
