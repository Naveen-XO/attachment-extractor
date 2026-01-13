@echo off
REM Simple document extraction script for non-technical users
REM Just double-click this file to run!

echo.
echo ================================================================================
echo                    DOCUMENT EXTRACTION TOOL
echo ================================================================================
echo.
echo This tool will:
echo   1. Read all your documents (PDFs, images, CSV files)
echo   2. Extract important information
echo   3. Create organized data files
echo.
echo Press Ctrl+C to cancel at any time.
echo.
echo ================================================================================
echo.

REM Get folder path from user
set /p FOLDER_PATH="Enter the FULL PATH to your documents folder: "

echo.
echo You entered: %FOLDER_PATH%
echo.

REM Validate folder exists
if not exist "%FOLDER_PATH%" (
    echo.
    echo ERROR: Folder not found!
    echo Please check the path and try again.
    echo.
    echo Example: C:\Users\YourName\Documents\MyFiles
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo STARTING EXTRACTION...
echo ================================================================================
echo.
echo Processing all files in: %FOLDER_PATH%
echo.
echo This may take a few minutes. Please wait...
echo.

REM Run the extraction
python src\main.py --input "%FOLDER_PATH%"

REM Check if successful
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo SUCCESS!
    echo ================================================================================
    echo.
    echo Your results are ready in the 'output' folder!
    echo.
    echo What to do next:
    echo   1. Open: output\summary.txt  ^(to see statistics^)
    echo   2. Open: output\index.json    ^(to see all data^)
    echo   3. Check: logs\processing.log ^(for details^)
    echo.
    echo Opening output folder...
    start "" "%~dp0output"
    echo.
) else (
    echo.
    echo ================================================================================
    echo SOMETHING WENT WRONG
    echo ================================================================================
    echo.
    echo Please check:
    echo   1. Python is installed correctly
    echo   2. You ran the setup steps (see FOR_NON_TECHNICAL_USERS.md)
    echo   3. The folder path is correct
    echo.
    echo Check logs\errors.log for details.
    echo.
    echo If you need help, contact your technical support person.
    echo.
)

echo.
pause
