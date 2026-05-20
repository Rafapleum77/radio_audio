@echo off
REM ===========================================================================
REM BIT ADICT - SETUP PC DO FILHO v2 (com log e pause defensivo)
REM Tudo logado em C:\BIT_ADICT\setup.log
REM ===========================================================================
title BIT ADICT - SETUP PC DO FILHO v2

REM === 0. Cria pasta base e abre log ===
mkdir C:\BIT_ADICT 2>nul
set "LOG=C:\BIT_ADICT\setup.log"
echo. > "%LOG%"
echo ============================================== >> "%LOG%"
echo BIT ADICT SETUP v2 - %DATE% %TIME% >> "%LOG%"
echo ============================================== >> "%LOG%"

echo.
echo ===============================================================
echo   BIT ADICT - SETUP PC DO FILHO (v2)
echo ===============================================================
echo.
echo Log completo: %LOG%
echo.

REM === 1. Verifica admin ===
net session >nul 2>&1
if errorlevel 1 (
  echo [X] Esse arquivo precisa ser rodado como ADMINISTRADOR.
  echo Fecha essa janela, clica com BOTAO DIREITO no .bat
  echo e escolhe "Executar como administrador".
  echo.
  echo Erro: nao eh admin >> "%LOG%"
  pause
  exit /b 1
)
echo [OK] Rodando como Administrador. >> "%LOG%"
echo [OK] Rodando como Administrador.
echo.

REM === 2. Cria estrutura ===
echo [1/7] Criando pasta C:\BIT_ADICT...
echo [1/7] Criando pasta >> "%LOG%"
mkdir C:\BIT_ADICT\SCAN 2>nul
mkdir C:\BIT_ADICT\SCAN\imagens 2>nul
mkdir C:\BIT_ADICT\SCAN\textos_suspeitos 2>nul
mkdir C:\BIT_ADICT\SCAN\wallets 2>nul
mkdir C:\BIT_ADICT\logs 2>nul
cd /d C:\BIT_ADICT
echo [OK] Pasta criada.
echo.

REM === 3. Ativa SSH ===
echo [2/7] Ativando SSH Server...
echo [2/7] SSH >> "%LOG%"
powershell -NoProfile -Command "Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0" >> "%LOG%" 2>&1
powershell -NoProfile -Command "Start-Service sshd" >> "%LOG%" 2>&1
powershell -NoProfile -Command "Set-Service -Name sshd -StartupType Automatic" >> "%LOG%" 2>&1
powershell -NoProfile -Command "if (-not (Get-NetFirewallRule -Name 'sshd' -ErrorAction SilentlyContinue)) { New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 }" >> "%LOG%" 2>&1
net user Lenovo "BotPapai2026!" >> "%LOG%" 2>&1
echo [OK] SSH ativado. User: Lenovo / Senha: BotPapai2026!
echo.
echo --- PAUSA pra tu confirmar que esta tudo certo ate aqui ---
echo Pressiona qualquer tecla pra continuar com Python...
pause >nul

REM === 4. Python 3.11 ===
echo.
echo [3/7] Verificando Python 3.11...
echo [3/7] Python >> "%LOG%"
where python 2>nul >> "%LOG%"
where python >nul 2>&1
if not errorlevel 1 (
  echo [OK] Python ja instalado:
  python --version
  goto :py_pronto
)

echo Python NAO encontrado. Baixando Python 3.11.9 (~25 MB)...
echo Baixando python311.exe >> "%LOG%"
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python311.exe' -UseBasicParsing" >> "%LOG%" 2>&1

if not exist "%TEMP%\python311.exe" (
  echo [X] Falha no download do Python. Verifica internet e tenta de novo.
  echo Download falhou >> "%LOG%"
  pause
  exit /b 1
)

echo Instalando Python silenciosamente (3-5 min, NAO FECHA A JANELA)...
echo Iniciando install Python >> "%LOG%"
start /wait "" "%TEMP%\python311.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1
echo Install Python terminou com errorlevel %errorlevel% >> "%LOG%"

REM Refresh PATH pra essa sessao
set "PATH=%PATH%;C:\Program Files\Python311;C:\Program Files\Python311\Scripts"

where python >nul 2>&1
if errorlevel 1 (
  echo [X] Python nao foi instalado corretamente. Verifica %LOG%
  echo Python apos install nao foi achado >> "%LOG%"
  echo Tenta abrir manualmente: %TEMP%\python311.exe
  pause
  exit /b 1
)

:py_pronto
python --version >> "%LOG%" 2>&1
python --version
echo [OK] Python pronto.
echo.
pause

REM === 5. Libs Python ===
echo.
echo [4/7] Instalando bibliotecas Python (3-5 min)...
echo [4/7] Libs >> "%LOG%"
python -m pip install --upgrade pip --quiet >> "%LOG%" 2>&1
python -m pip install --quiet bip-utils web3 python-dotenv requests pandas numpy pillow >> "%LOG%" 2>&1
echo Tentando py_clob_client_v2... >> "%LOG%"
python -m pip install --quiet py_clob_client_v2 >> "%LOG%" 2>&1
if errorlevel 1 (
  echo (py_clob_client_v2 fallback git)
  python -m pip install --quiet git+https://github.com/Polymarket/py-clob-client-v2.git >> "%LOG%" 2>&1
)
echo [OK] Libs instaladas.
echo.

REM === 6. Baixa arquivos do BIT ADICT ===
echo [5/7] Baixando Recovery Kit + Scanner + Bot...
echo [5/7] Downloads >> "%LOG%"
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://radiobitcoin.org/scripts/recovery_kit.py' -OutFile 'C:\BIT_ADICT\recovery_kit.py' -UseBasicParsing" >> "%LOG%" 2>&1
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://radiobitcoin.org/scripts/bip39_en.txt' -OutFile 'C:\BIT_ADICT\bip39_en.txt' -UseBasicParsing" >> "%LOG%" 2>&1
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://radiobitcoin.org/scripts/scan_seeds_imagens.ps1' -OutFile 'C:\BIT_ADICT\scan_seeds_imagens.ps1' -UseBasicParsing" >> "%LOG%" 2>&1
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://radiobitcoin.org/scripts/bot_direcional_v2.py' -OutFile 'C:\BIT_ADICT\bot_direcional_v2.py' -UseBasicParsing" >> "%LOG%" 2>&1
echo Arquivos baixados: >> "%LOG%"
dir C:\BIT_ADICT\*.* >> "%LOG%" 2>&1
echo [OK] Arquivos em C:\BIT_ADICT\
echo.

REM === 7. Scan ===
echo [6/7] Escaneando PC (3-5 min). NAO FECHA A JANELA.
echo [6/7] Scan >> "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -File C:\BIT_ADICT\scan_seeds_imagens.ps1
echo [OK] Scan terminado.
echo.

REM === 8. Atalhos ===
echo [7/7] Criando atalhos na area de trabalho...
echo [7/7] Atalhos >> "%LOG%"
powershell -NoProfile -Command "$s = New-Object -ComObject WScript.Shell; $sc = $s.CreateShortcut('%PUBLIC%\Desktop\BOT DO PAPAI.lnk'); $sc.TargetPath = (Get-Command python.exe).Source; $sc.Arguments = 'C:\BIT_ADICT\bot_direcional_v2.py'; $sc.WorkingDirectory = 'C:\BIT_ADICT'; $sc.Save()" >> "%LOG%" 2>&1
powershell -NoProfile -Command "$s = New-Object -ComObject WScript.Shell; $sc = $s.CreateShortcut('%PUBLIC%\Desktop\RECOVERY KIT.lnk'); $sc.TargetPath = (Get-Command python.exe).Source; $sc.Arguments = 'C:\BIT_ADICT\recovery_kit.py'; $sc.WorkingDirectory = 'C:\BIT_ADICT'; $sc.Save()" >> "%LOG%" 2>&1
powershell -NoProfile -Command "$s = New-Object -ComObject WScript.Shell; $sc = $s.CreateShortcut('%PUBLIC%\Desktop\SCAN SEEDS.lnk'); $sc.TargetPath = 'C:\BIT_ADICT\SCAN'; $sc.Save()" >> "%LOG%" 2>&1
echo [OK] Atalhos criados.
echo.

echo ===============================================================
echo   SETUP COMPLETO!
echo ===============================================================
echo.
echo Log: %LOG%
echo Scan: C:\BIT_ADICT\SCAN
echo.
echo Avisa Rafael: WhatsApp +55 61 99811-0979
echo.
pause
