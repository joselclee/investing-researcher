@echo off

:: Activate the virtual environment
call .venv\Scripts\Activate.ps1

:: Set environment variables from .env file
for /f "tokens=1,2 delims==" %%i in (.env) do (
    set %%i=%%j
)

:: Start the Flask server
python app.py