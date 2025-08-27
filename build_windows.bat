@echo off
REM Limpieza de compilaciones anteriores
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
del /q *.spec

REM Compilación de app.py con icono y nombre Nexus
pyinstaller --onefile --noconsole --icon=gui/icon.ico --name Nexus gui/app.py

REM El ejecutable final quedará en: dist\Nexus.exe
REM Lo movemos a la carpeta dist\Nexus\ para que quede en dist\Nexus\Nexus.exe
mkdir dist\Nexus
move /Y dist\Nexus.exe dist\Nexus\Nexus.exe

pause