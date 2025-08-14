@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Dossier du script
set SCRIPT_DIR=%~dp0
pushd "%SCRIPT_DIR%"

REM Vérifier Python et PyInstaller
where python >nul 2>&1 || (
  echo Python introuvable. Installez Python 3.x et relancez.
  pause
  exit /b 1
)

pip show pyinstaller >nul 2>&1 || (
  echo Installation de PyInstaller...
  python -m pip install --upgrade pip >nul 2>&1
  python -m pip install pyinstaller >nul 2>&1
)

echo Installation des dependances...
python -m pip install -r requirements.txt

REM Option d'icone: si un PNG existe, on tente de le convertir en .ico temporaire
set ICON_PNG=
for %%F in (*.png) do (
  set ICON_PNG=%%F
  goto :have_png
)
:have_png

set ICON_ARG=
if not "%ICON_PNG%"=="" (
  echo Creation d'une icone temporaire a partir de %ICON_PNG% ...
  python -c "from PIL import Image; im=Image.open(r'%ICON_PNG%'); im.save(r'icon_tmp.ico', sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)])" >nul 2>&1
  if exist icon_tmp.ico (
    set ICON_ARG=--icon icon_tmp.ico
  )
)

echo Construction de l'executable...
pyinstaller --noconsole --onefile --name "YT-to-me" %ICON_ARG% app_win.py

if exist icon_tmp.ico del /f /q icon_tmp.ico >nul 2>&1

if exist dist\YT-to-me.exe (
  echo Copie de ffmpeg si present...
  if exist ffmpeg.exe copy /y ffmpeg.exe dist\ >nul 2>&1
  echo Fini. Executable: dist\YT-to-me.exe
) else (
  echo Echec de la construction. Verifiez les logs PyInstaller.
)

popd
endlocal
