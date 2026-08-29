cd /d "C:\stock_system"

echo ========================================================
echo  起動テスト中...
echo ========================================================

:: 1. 仮想環境のPythonで app08.py を実行
if exist "app08.py" (
    "C:\stock_system\venv\Scripts\python.exe" -m streamlit run app08.py
) else if exist "app0828.py" (
    "C:\stock_system\venv\Scripts\python.exe" -m streamlit run app0828.py
) else if exist "stock_report_app.py" (
    "C:\stock_system\venv\Scripts\python.exe" -m streamlit run stock_report_app.py
) else (
    echo [エラー] 対象のPythonファイルが見つかりません。
    dir *.py
)

echo.
echo ========================================================
echo  処理が終了しました（キーを押すと閉じます）
echo ========================================================
pause