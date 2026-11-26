@echo off
setlocal EnableExtensions EnableDelayedExpansion
rem Coda di Volpe: builds the playable release in F:\OneDrive\TR_CodaDiVolpe and the zip F:\OneDrive\TR_CodaDiVolpe.zip
rem Compile the five levels in Tomb Editor first, and close the game.

set "DEV=C:\CodaDiVolpe"
set "PARENT=F:\OneDrive"
set "NAME=TR_CodaDiVolpe"
set "REL=%PARENT%\%NAME%"
set "ZIP=%PARENT%\%NAME%.zip"
set "TMPZIP=%PARENT%\%NAME%_new.zip"
set "LEVELS=Oliveri Marinello Tindari Sommersa Title"

if not exist "%DEV%\Engine\Data" (echo STOP: %DEV%\Engine\Data not found & goto :fail)
if not exist "%REL%\Engine\Bin\x64\TombEngine.exe" (echo STOP: %REL% is not a release folder & goto :fail)

tasklist /FI "IMAGENAME eq TombEngine.exe" 2>nul | find /I "TombEngine.exe" >nul
if not errorlevel 1 (echo STOP: TombEngine.exe is running. Close the game first. & goto :fail)

echo === 1. Checking the compiled levels
set "STALE="
for %%L in (%LEVELS%) do (
    if not exist "%DEV%\Engine\Data\%%L.ten" (echo STOP: %%L.ten is missing & goto :fail)
    if not exist "%DEV%\Engine\Scripts\Levels\%%L.lua" (echo STOP: %%L.lua is missing & goto :fail)
    xcopy /L /D /Y "%DEV%\Levels\%%L\%%L.prj2" "%DEV%\Engine\Data\%%L.ten" 2>nul | findstr /B /C:"1 " >nul
    if not errorlevel 1 (echo WARNING: %%L.prj2 is newer than %%L.ten: not recompiled? & set "STALE=1")
)
if defined STALE (
    choice /C YN /M "Go on anyway"
    if errorlevel 2 goto :fail
)

echo === 2. Levels
for %%L in (%LEVELS%) do (
    copy /Y /B "%DEV%\Engine\Data\%%L.ten" "%REL%\Engine\Data\%%L.ten" >nul || (echo STOP: copy of %%L.ten failed & goto :fail)
    echo   %%L.ten
)

echo === 3. Scripts
for %%L in (%LEVELS%) do (
    copy /Y "%DEV%\Engine\Scripts\Levels\%%L.lua" "%REL%\Engine\Scripts\Levels\%%L.lua" >nul || (echo STOP: copy of %%L.lua failed & goto :fail)
)
copy /Y "%DEV%\Engine\Scripts\Gameflow_release.lua" "%REL%\Engine\Scripts\Gameflow.lua" >nul || (echo STOP: Gameflow failed & goto :fail)
findstr /C:"CDV_RELEASE = true" "%REL%\Engine\Scripts\Gameflow.lua" >nul || (echo STOP: the release Gameflow does not have CDV_RELEASE = true & goto :fail)

echo === 4. Screens, logo, music, intro
copy /Y /B "%DEV%\Engine\Screens\main.png" "%REL%\Engine\Screens\main.png" >nul || goto :fail
copy /Y /B "%DEV%\Engine\Screens\loading.png" "%REL%\Engine\Screens\loading.png" >nul || goto :fail
copy /Y /B "%DEV%\Engine\Textures\Logo.png" "%REL%\Engine\Textures\Logo.png" >nul || goto :fail
if exist "%DEV%\Engine\Audio_release\*.mp3" (
    copy /Y /B "%DEV%\Engine\Audio_release\*.mp3" "%REL%\Engine\Audio\" >nul || (echo STOP: music failed & goto :fail)
)
if exist "%DEV%\Engine\Fmv_release\*.mp4" (
    copy /Y /B "%DEV%\Engine\Fmv_release\*.mp4" "%REL%\Engine\Fmv\" >nul || (echo STOP: intro failed & goto :fail)
)

echo === 5. Texts
copy /Y "%DEV%\README_release.txt" "%REL%\README.txt" >nul || goto :fail
copy /Y "%DEV%\WALKTHROUGH.txt" "%REL%\WALKTHROUGH.txt" >nul || goto :fail

echo === 6. Cleaning savegames, logs and backups
if exist "%REL%\Engine\Save" rd /S /Q "%REL%\Engine\Save"
if exist "%REL%\Engine\Logs" rd /S /Q "%REL%\Engine\Logs"
del /S /Q "%REL%\*.backup.*" >nul 2>&1
del /S /Q "%REL%\*.log" >nul 2>&1

echo === 7. Zip
where tar >nul 2>&1 || (echo STOP: tar.exe not found, Windows 10 or later needed & goto :fail)
if exist "%TMPZIP%" del /Q "%TMPZIP%"
tar -a -c -f "%TMPZIP%" -C "%PARENT%" "%NAME%"
if errorlevel 1 (echo STOP: zip failed, the old zip is untouched & del /Q "%TMPZIP%" 2>nul & goto :fail)
move /Y "%TMPZIP%" "%ZIP%" >nul || (echo STOP: could not replace %ZIP% & goto :fail)

echo.
echo DONE
for %%Z in ("%ZIP%") do echo   %%~fZ   %%~zZ bytes
for %%L in (%LEVELS%) do for %%F in ("%REL%\Engine\Data\%%L.ten") do echo   %%~nxF   %%~zF bytes
echo.
pause
exit /b 0

:fail
echo.
echo NOT DONE
pause
exit /b 1
