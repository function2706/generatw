@echo off
echo Creating virtual environment...
python -m venv venv

echo Activating venv...
call venv\Scripts\activate

echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo Done.
pause