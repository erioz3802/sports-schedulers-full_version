@echo off
echo 🏀 Sports Schedulers Web Application
echo ======================================
echo.

cd /d "C:\Users\c65917\Documents\Jupyter Notebook\Personal\Sports_Scheduler_Multi_User_Web\sports-scheduler-web"

echo Checking Python installation...
python --version
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo.
echo Checking dependencies...
pip show flask > nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install flask flask-sqlalchemy flask-jwt-extended flask-cors werkzeug python-dateutil
)

echo.
echo Starting Sports Schedulers Web Application...
echo 🌐 Access at: http://localhost:5000
echo 👤 Login: jose_1 / Josu2398-1 or admin / admin123
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py

pause
