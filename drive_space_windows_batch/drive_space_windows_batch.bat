echo off
cls

goto main

:drive_free_space
rem имя диска
set drive_name=%1
if not defined drive_name (
  echo drive name is not specified
  exit /b
)
echo get free space for drive %drive_name%

rem set report_file=drive_free_space__%drive_name%.txt

if exist %drive_name%:\ (
  dir %drive_name%:\ | findstr " свободно" > %temp%\space_free_%drive_name%.tmp
  set /p space_free=<%temp%\space_free_%drive_name%.tmp
) else (
  set space_free=drive %drive_name% does not exist
)
echo %date% %time% %space_free% >> drive_free_space__%drive_name%.txt

exit /b


rem ------------------------- main ------------------------
:main

rem перейти в каталог, в котором находится батник
cd /D "%~dp0"

call :drive_free_space c
call :drive_free_space d

ping -n 100 127.0.0.1 > nul
