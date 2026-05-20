@echo off
REM ===========================================================================
REM BIT ADICT - SETUP COMPLETO PC DO FILHO (rodar 1x como Administrador)
REM Faz: SSH + Python 3.11 + Recovery Kit + Scan seeds/imagens + Bot DIRECIONAL
REM ===========================================================================
chcp 65001 >nul
title BIT ADICT - SETUP PC DO FILHO

echo.
echo ===============================================================
echo   BIT ADICT - SETUP PC DO FILHO (Lenovo)
echo   Rafael Rios Crosara - 2026
echo ===============================================================
echo.

REM 1. Verifica admin
net session >nul 2>&1
if errorlevel 1 (
  echo ERRO: Esse arquivo precisa ser rodado como ADMINISTRADOR.
  echo Fecha essa janela, clica com BOTAO DIREITO no setup_pc_filho.bat
  echo e escolhe "Executar como administrador".
  echo.
  pause
  exit /b 1
)
echo [OK] Rodando como Administrador.
echo.

REM 2. Cria pasta base
echo [1/7] Criando pasta C:\BIT_ADICT...
mkdir C:\BIT_ADICT 2>nul
mkdir C:\BIT_ADICT\SCAN 2>nul
mkdir C:\BIT_ADICT\SCAN\imagens 2>nul
mkdir C:\BIT_ADICT\SCAN\textos_suspeitos 2>nul
mkdir C:\BIT_ADICT\SCAN\wallets 2>nul
cd /d C:\BIT_ADICT

REM 3. Ativa OpenSSH Server
echo.
echo [2/7] Ativando SSH Server (acesso remoto pro Rafael)...
powershell -Command "Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0" 2>&1 | findstr /v "^$"
powershell -Command "Start-Service sshd" 2>nul
powershell -Command "Set-Service -Name sshd -StartupType 'Automatic'" 2>nul
powershell -Command "New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22" 2>nul
net user Lenovo "BotPapai2026!" >nul 2>&1
echo [OK] SSH ativo na porta 22. User: Lenovo / Senha: BotPapai2026!

REM 4. Baixa Python 3.11 (se nao tem)
echo.
echo [3/7] Verificando Python 3.11...
where python >nul 2>&1
if errorlevel 1 (
  echo Python NAO encontrado. Baixando Python 3.11.9...
  powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python311.exe'"
  echo Instalando Python silenciosamente (PATH automatico)...
  "%TEMP%\python311.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
  echo Aguardando 30s pra finalizar instalacao...
  timeout /t 30 /nobreak >nul
  set "PATH=%PATH%;C:\Program Files\Python311;C:\Program Files\Python311\Scripts"
)
python --version
echo [OK] Python instalado.

REM 5. Instala libs Python necessarias
echo.
echo [4/7] Instalando bibliotecas Python (Recovery Kit + bot)...
python -m pip install --upgrade pip --quiet
python -m pip install --quiet bip-utils web3 ccxt python-dotenv requests pandas numpy py_clob_client_v2 pillow
echo [OK] Libs instaladas.

REM 6. Baixa Recovery Kit + Scanner
echo.
echo [5/7] Baixando Recovery Kit BIT ADICT + Scanner...
powershell -Command "Invoke-WebRequest -Uri 'https://radiobitcoin.org/scripts/recovery_kit.py' -OutFile 'C:\BIT_ADICT\recovery_kit.py'" 2>nul
powershell -Command "Invoke-WebRequest -Uri 'https://radiobitcoin.org/scripts/bip39_en.txt' -OutFile 'C:\BIT_ADICT\bip39_en.txt'" 2>nul
powershell -Command "Invoke-WebRequest -Uri 'https://radiobitcoin.org/scripts/scan_seeds_imagens.ps1' -OutFile 'C:\BIT_ADICT\scan_seeds_imagens.ps1'"
powershell -Command "Invoke-WebRequest -Uri 'https://radiobitcoin.org/scripts/bot_direcional_v2.py' -OutFile 'C:\BIT_ADICT\bot_direcional_v2.py'" 2>nul
echo [OK] Arquivos baixados.

REM 7. Roda scan de seeds e imagens
echo.
echo [6/7] Escaneando PC por imagens, textos com seeds, wallets instaladas...
echo Isso pode demorar 2-5 minutos. NAO fecha a janela.
powershell -ExecutionPolicy Bypass -File C:\BIT_ADICT\scan_seeds_imagens.ps1

REM 8. Cria atalho na area de trabalho
echo.
echo [7/7] Criando atalhos na area de trabalho...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%PUBLIC%\Desktop\BOT DO PAPAI.lnk'); $Shortcut.TargetPath = 'C:\Program Files\Python311\python.exe'; $Shortcut.Arguments = 'C:\BIT_ADICT\bot_direcional_v2.py'; $Shortcut.WorkingDirectory = 'C:\BIT_ADICT'; $Shortcut.IconLocation = 'C:\BIT_ADICT\bot_direcional_v2.py,0'; $Shortcut.Save()"
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%PUBLIC%\Desktop\RECOVERY KIT.lnk'); $Shortcut.TargetPath = 'C:\Program Files\Python311\python.exe'; $Shortcut.Arguments = 'C:\BIT_ADICT\recovery_kit.py'; $Shortcut.WorkingDirectory = 'C:\BIT_ADICT'; $Shortcut.Save()"
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%PUBLIC%\Desktop\SCAN SEEDS (pasta com tudo).lnk'); $Shortcut.TargetPath = 'C:\BIT_ADICT\SCAN'"
echo [OK] Atalhos criados.

echo.
echo ===============================================================
echo   SETUP COMPLETO!
echo ===============================================================
echo.
echo Resumo:
echo   - SSH ativo em 192.168.1.102:22 (user Lenovo / senha BotPapai2026!)
echo   - Python 3.11 + libs Recovery Kit + bot
echo   - Recovery Kit em C:\BIT_ADICT\recovery_kit.py
echo   - Bot DIRECIONAL em C:\BIT_ADICT\bot_direcional_v2.py
echo   - Atalhos na area de trabalho criados
echo   - Scan completo em C:\BIT_ADICT\SCAN\ (imagens + textos suspeitos + wallets)
echo.
echo IMPORTANTE: backup da pasta C:\BIT_ADICT\SCAN no pen drive AGORA.
echo Tem coisas potencialmente sensiveis ali.
echo.
echo Avisa o Rafael: "setup ok" no WhatsApp +55 61 99811-0979
echo.
pause
