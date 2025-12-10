@echo off
echo ============================================================
echo Microsoft Graph API Token Generator
echo ============================================================
echo.

REM First, install msal if not already installed
echo Installing required packages...
C:/ProgramData/anaconda3/Scripts/conda.exe run -p c:\Satish\AI\MRComments_Extractor\.conda pip install msal requests

echo.
echo ============================================================
echo Generating token...
echo ============================================================
echo.

REM Run the token generator
C:/ProgramData/anaconda3/Scripts/conda.exe run -p c:\Satish\AI\MRComments_Extractor\.conda python generate_graph_token.py

pause
