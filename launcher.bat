@echo off
cd /d C:\stock_system
echo ========================================
echo    株スクリーナー 起動中...
echo.
echo ========================================
echo.
echo [1/3] データ更新中...
python fix_csv2.py
echo.
echo [2/3] ブラウザを開きます...
timeout /t 3 /nobreak > nul
start http://localhost:8501
echo.
echo [3/3] アプリ起動中...
streamlit run app.py
