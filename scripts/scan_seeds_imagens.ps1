# scan_seeds_imagens.ps1 — varre PC procurando seeds, imagens e wallets
# Roda automaticamente pelo setup_pc_filho.bat — não rodar diretamente.

$OUT = "C:\BIT_ADICT\SCAN"
New-Item -ItemType Directory -Path "$OUT\imagens" -Force | Out-Null
New-Item -ItemType Directory -Path "$OUT\textos_suspeitos" -Force | Out-Null
New-Item -ItemType Directory -Path "$OUT\wallets" -Force | Out-Null

# Pastas a varrer
$searchPaths = @(
    "$env:USERPROFILE\Desktop",
    "$env:USERPROFILE\Downloads",
    "$env:USERPROFILE\Documents",
    "$env:USERPROFILE\Pictures",
    "$env:USERPROFILE\OneDrive",
    "$env:USERPROFILE\Dropbox",
    "C:\Backup",
    "C:\BIT_ADICT_OLD"
)

# Lista de 50 palavras BIP39 mais comuns (sample — wordlist completo seria 2048)
$bip39Sample = @(
    'abandon','ability','able','about','above','absent','absorb','abstract','abuse','access',
    'accident','account','accuse','achieve','acid','acoustic','acquire','across','act','action',
    'wallet','wallet','seed','seed','phrase','recovery','backup','mnemonic','bitcoin','ethereum',
    'private','public','key','address','coin','metamask','exodus','electrum','ledger','trezor',
    'master','secret','passphrase','24','12','word','words','keystore','signing','hardware'
)

Write-Host ""
Write-Host "===============================================================" -ForegroundColor Yellow
Write-Host "  SCAN BIT ADICT - procurando seeds/imagens/wallets" -ForegroundColor Yellow
Write-Host "===============================================================" -ForegroundColor Yellow

# ============== 1. IMAGENS ==============
Write-Host ""
Write-Host "[1/3] Coletando imagens (jpg/jpeg/png/heic/bmp/gif/webp)..." -ForegroundColor Cyan
$imgCount = 0
foreach ($p in $searchPaths) {
    if (Test-Path $p) {
        Get-ChildItem -Path $p -Recurse -Include *.jpg,*.jpeg,*.png,*.heic,*.bmp,*.gif,*.webp,*.tiff -ErrorAction SilentlyContinue |
        Where-Object { $_.Length -gt 10KB -and $_.Length -lt 50MB } |
        ForEach-Object {
            $newName = "$($_.Directory.Name)_$($_.Name)"
            $dst = Join-Path "$OUT\imagens" $newName
            if (-not (Test-Path $dst)) {
                Copy-Item $_.FullName -Destination $dst -ErrorAction SilentlyContinue
                $imgCount++
            }
        }
    }
}
Write-Host "  -> $imgCount imagens copiadas em $OUT\imagens\" -ForegroundColor Green

# ============== 2. TEXTOS COM PADRAO DE SEED ==============
Write-Host ""
Write-Host "[2/3] Procurando textos com palavras BIP39 (txt/docx/rtf/md/csv)..." -ForegroundColor Cyan
$txtCount = 0
foreach ($p in $searchPaths) {
    if (Test-Path $p) {
        Get-ChildItem -Path $p -Recurse -Include *.txt,*.docx,*.rtf,*.md,*.csv,*.log,*.html,*.xml,*.json -ErrorAction SilentlyContinue |
        Where-Object { $_.Length -gt 0 -and $_.Length -lt 5MB } |
        ForEach-Object {
            try {
                $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
                if ($content) {
                    $contentLower = $content.ToLower()
                    $matchCount = 0
                    foreach ($word in $bip39Sample) {
                        if ($contentLower -match "\b$word\b") { $matchCount++ }
                    }
                    # 3+ palavras suspeitas no mesmo arquivo = copia
                    if ($matchCount -ge 3) {
                        $newName = "[$matchCount-matches]_$($_.Directory.Name)_$($_.Name)"
                        $dst = Join-Path "$OUT\textos_suspeitos" $newName
                        Copy-Item $_.FullName -Destination $dst -ErrorAction SilentlyContinue
                        $txtCount++
                        Write-Host "    [$matchCount matches] $($_.FullName)" -ForegroundColor DarkYellow
                    }
                }
            } catch { }
        }
    }
}
Write-Host "  -> $txtCount textos suspeitos em $OUT\textos_suspeitos\" -ForegroundColor Green

# ============== 3. WALLETS INSTALADAS ==============
Write-Host ""
Write-Host "[3/3] Procurando wallets instaladas..." -ForegroundColor Cyan
$walletPaths = @{
    "Bitcoin Core"        = "$env:APPDATA\Bitcoin"
    "Electrum"            = "$env:APPDATA\Electrum"
    "Exodus"              = "$env:APPDATA\Exodus"
    "Atomic"              = "$env:APPDATA\atomic"
    "Wasabi"              = "$env:APPDATA\WalletWasabi"
    "Sparrow"             = "$env:APPDATA\Sparrow"
    "Monero GUI"          = "$env:USERPROFILE\Documents\Monero"
    "Daedalus (ADA)"      = "$env:APPDATA\Daedalus Mainnet"
    "MetaMask (Chrome)"   = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Local Extension Settings\nkbihfbeogaeaoehlefnkodbefgpgknn"
    "MetaMask (Brave)"    = "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\User Data\Default\Local Extension Settings\nkbihfbeogaeaoehlefnkodbefgpgknn"
    "MetaMask (Edge)"     = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Local Extension Settings\ejbalbakoplchlghecdalmeeeajnimhm"
    "Phantom (Chrome)"    = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Local Extension Settings\bfnaelmomeimhlpmgjnjophhpkkoljpa"
    "Coinbase (Chrome)"   = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Local Extension Settings\hnfanknocfeofbddgcijnmhnfnkdnaad"
    "Trust Wallet"        = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Local Extension Settings\egjidjbpglichdcondbcbdnbeeppgdph"
    "Mycelium"            = "$env:APPDATA\mycelium"
    "Bitcoin Knots"       = "$env:APPDATA\Bitcoin"
    "Litecoin"            = "$env:APPDATA\Litecoin"
    "Dash"                = "$env:APPDATA\Dash"
}

$walletCount = 0
foreach ($w in $walletPaths.GetEnumerator()) {
    if (Test-Path $w.Value) {
        Write-Host "    ✓ ENCONTRADA: $($w.Name) em $($w.Value)" -ForegroundColor Yellow
        $safeName = $w.Name -replace '[^a-zA-Z0-9_-]','_'
        try {
            Copy-Item -Path $w.Value -Destination "$OUT\wallets\$safeName" -Recurse -ErrorAction Stop
            $walletCount++
        } catch {
            Write-Host "      (erro ao copiar: $($_.Exception.Message))" -ForegroundColor Red
        }
    }
}
Write-Host "  -> $walletCount wallets copiadas em $OUT\wallets\" -ForegroundColor Green

# ============== 4. RELATORIO ==============
$relatorio = @"
==============================================================
  RELATORIO SCAN BIT ADICT
  Data: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
  PC: $env:COMPUTERNAME ($env:USERNAME)
==============================================================

Pastas varridas:
$($searchPaths -join "`n")

Resultado:
- Imagens coletadas:     $imgCount    (em \imagens\)
- Textos suspeitos:      $txtCount    (em \textos_suspeitos\)
- Wallets instaladas:    $walletCount (em \wallets\)

ATENCAO:
- A pasta \textos_suspeitos\ pode conter seed phrases, senhas, chaves privadas
- A pasta \wallets\ contem databases de wallets que podem ter chaves nao criptografadas
- COPIA A PASTA INTEIRA $OUT NO PEN DRIVE AGORA e mantem off-line
- Depois de copiada, considere apagar do disco principal (procuradores podem
  acessar arquivos deletados se nao for wipe seguro)

Pasta scan: $OUT
"@

$relatorio | Out-File -FilePath "$OUT\RELATORIO.txt" -Encoding UTF8
Write-Host ""
Write-Host "===============================================================" -ForegroundColor Yellow
Write-Host "  SCAN COMPLETO" -ForegroundColor Green
Write-Host "===============================================================" -ForegroundColor Yellow
Write-Host "  Pasta com tudo: $OUT" -ForegroundColor White
Write-Host "  Relatorio:      $OUT\RELATORIO.txt" -ForegroundColor White
Write-Host ""
Write-Host "PRoXIMO PASSO: copia toda a pasta C:\BIT_ADICT\SCAN no pen drive." -ForegroundColor Cyan
Write-Host ""

# Abre Explorer pra facilitar drag-and-drop pro pen drive
Start-Process explorer.exe "$OUT"
