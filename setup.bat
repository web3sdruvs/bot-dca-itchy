@echo off
echo Checking if the virtual environment exists...

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating the virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo Setup completed!
pause