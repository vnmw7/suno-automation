@echo off
SETLOCAL EnableDelayedExpansion

REM --- Configuration ---
SET "inputFile=postgresql_query.txt"
SET "linesPerFile=1000"
SET "outputBaseName=output_part_"
SET "outputExtension=.txt"
REM --- End Configuration ---

IF NOT EXIST "%inputFile%" (
    echo Error: Input file "%inputFile%" not found.
    GOTO :EOF
)

SET /A lineCounter=0
SET /A filePart=0 
SET "currentOutputFile="

echo Splitting "%inputFile%" into parts of %linesPerFile% lines each...

REM Optional: Delete old output files first
IF EXIST "%outputBaseName%*%outputExtension%" (
    echo Deleting existing output files: %outputBaseName%*%outputExtension%
    DEL /Q "%outputBaseName%*%outputExtension%"
)

FOR /F "usebackq delims=" %%L IN ("%inputFile%") DO (
    SET /A modResult = !lineCounter! %% %linesPerFile%

    IF !modResult! EQU 0 (
        SET /A filePart+=1
        SET "currentOutputFile=!outputBaseName!!filePart!!outputExtension!"
        echo Creating/writing to: !currentOutputFile!
    )

    REM Append the line to the current output file
    REM Using >> ensures we append. The () around ECHO are for safety with special characters.
    (ECHO %%L)>>"!currentOutputFile!"
    
    SET /A lineCounter+=1
)

IF !lineCounter! EQU 0 (
    echo Input file "%inputFile%" was empty or could not be read.
) ELSE (
    echo.
    echo Splitting complete.
    echo Total lines processed: !lineCounter!
    echo Last file created: !currentOutputFile!
)

ENDLOCAL
GOTO :EOF