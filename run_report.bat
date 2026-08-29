@echo off
cd /d C:\stock_system
call venv\Scripts\activate.bat
streamlit run stock_report_app.py
pause