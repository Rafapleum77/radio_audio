@echo off
REM ==========================================================
REM BIT ADICT - SETUP MINIMO (sem SSH, foco Python + Bot + Scan)
REM ==========================================================
title BIT ADICT - SETUP

mkdir C:\BIT_ADICT 2>nul
mkdir C:\BIT_ADICT\SCAN 2>nul
mkdir C:\BIT_ADICT\SCAN\imagens 2>nul
mkdir C:\BIT_ADICT\SCAN\textos_suspeitos 2>nul
mkdir C:\BIT_ADICT\SCAN\wallets 2>nul
cd /d C:\BIT_ADICT

echo. > C:\BIT_ADICT\setup.log
set "LOG=C:\BIT_ADICT\setup.log"
echo BIT ADICT setup %DATE% %TIME% >> "%LOG%"

echo.
echo ==========================================================
echo   BIT ADICT - SETUP (sem SSH, soh o essencial)
echo ==========================================================
echo.
echo Vai instalar: Python 3.11 + Recovery Kit + Bot + Scanner
echo Tempo total: 8-12 minutos
echo NAO FECHA a janela. Eu pauso a cada passo pra tu acompanhar.
echo.
pause

echo.
echo [1/5] Verificando Python...
echo [1/5] Python check >> "%LOG%"
where python >nul 2>&1
if not errorlevel 1 (
  python --version
  echo [OK] Python ja instalado.
  goto :py_pronto
)

echo Python nao tem. Baixando 3.11.9 (25 MB)...
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\py311.exe' -UseBasicParsing"
if not exist "%TEMP%\py311.exe" (
  echo [X] Download falhou. Tenta de novo ou verifica internet.
  pause
  exit /b 1
)
echo Baixado. Instalando (3-5 min, NAO FECHA)...
start /wait "" "%TEMP%\py311.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1
set "PATH=%PATH%;C:\Program Files\Python311;C:\Program Files\Python311\Scripts"
where python >nul 2>&1
if errorlevel 1 (
  echo [X] Python nao foi instalado. Roda manualmente: %TEMP%\py311.exe
  pause
  exit /b 1
)
python --version
echo [OK] Python instalado.

:py_pronto
echo.
echo --- Pause: pressiona ENTER pra instalar bibliotecas ---
pause >nul

echo.
echo [2/5] Instalando bibliotecas (3-5 min)...
echo [2/5] Libs >> "%LOG%"
python -m pip install --upgrade pip --quiet >> "%LOG%" 2>&1
python -m pip install --quiet bip-utils web3 python-dotenv requests pandas numpy pillow >> "%LOG%" 2>&1
python -m pip install --quiet py_clob_client_v2 >> "%LOG%" 2>&1
echo [OK] Libs instaladas.
echo.
echo --- Pause: pressiona ENTER pra baixar Recovery Kit e Bot ---
pause >nul

echo.
echo [3/5] Baixando Recovery Kit + Bot + Scanner...
echo [3/5] Downloads >> "%LOG%"
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://radiobitcoin.org/scripts/recovery_kit.py' -OutFile 'C:\BIT_ADICT\recovery_kit.py' -UseBasicParsing"
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://radiobitcoin.org/scripts/bip39_en.txt' -OutFile 'C:\BIT_ADICT\bip39_en.txt' -UseBasicParsing"
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://radiobitcoin.org/scripts/scan_seeds_imagens.ps1' -OutFile 'C:\BIT_ADICT\scan_seeds_imagens.ps1' -UseBasicParsing"
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://radiobitcoin.org/scripts/bot_direcional_v2.py' -OutFile 'C:\BIT_ADICT\bot_direcional_v2.py' -UseBasicParsing"
dir C:\BIT_ADICT\*.py C:\BIT_ADICT\*.txt C:\BIT_ADICT\*.ps1
echo [OK] Arquivos baixados.
echo.
echo --- Pause: pressiona ENTER pra rodar o Scanner de seeds e imagens ---
pause >nul

echo.
echo [4/5] Escaneando PC (3-5 min). NAO FECHA.
echo [4/5] Scan >> "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -File C:\BIT_ADICT\scan_seeds_imagens.ps1
echo [OK] Scan completo.
echo.

echo [5/5] Criando atalhos na area de trabalho...
echo [5/5] Atalhos >> "%LOG%"
for /f "delims=" %%i in ('where python.exe') do set PYEXE=%%i
powershell -NoProfile -Command "$s = New-Object -ComObject WScript.Shell; $sc = $s.CreateShortcut('%PUBLIC%\Desktop\BOT DO PAPAI.lnk'); $sc.TargetPath = '%PYEXE%'; $sc.Arguments = 'C:\BIT_ADICT\bot_direcional_v2.py'; $sc.WorkingDirectory = 'C:\BIT_ADICT'; $sc.Save()"
powershell -NoProfile -Command "$s = New-Object -ComObject WScript.Shell; $sc = $s.CreateShortcut('%PUBLIC%\Desktop\RECOVERY KIT.lnk'); $sc.TargetPath = '%PYEXE%'; $sc.Arguments = 'C:\BIT_ADICT\recovery_kit.py'; $sc.WorkingDirectory = 'C:\BIT_ADICT'; $sc.Save()"
powershell -NoProfile -Command "$s = New-Object -ComObject WScript.Shell; $sc = $s.CreateShortcut('%PUBLIC%\Desktop\SCAN SEEDS.lnk'); $sc.TargetPath = 'C:\BIT_ADICT\SCAN'; $sc.Save()"
echo [OK] Atalhos criados.

echo.
echo ==========================================================
echo   SETUP COMPLETO!
echo ==========================================================
echo.
echo Pasta:    C:\BIT_ADICT\
echo Scan:     C:\BIT_ADICT\SCAN\
echo Atalhos:  Desktop (BOT DO PAPAI, RECOVERY KIT, SCAN SEEDS)
echo.
echo PROXIMO: copia C:\BIT_ADICT\SCAN no pen drive (drag-drop).
echo Avisa Rafael: WhatsApp +55 61 99811-0979
echo.
pause
