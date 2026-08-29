cd /d C:\stock_system
title 全銘柄クリーンデータベース新規構築中...

echo ========================================================
echo  東証全4,000銘柄の最新データをJ-Quantsから一括取得中...
echo  (※約1〜2分かかります。そのままお待ちください)
echo ========================================================

venv\Scripts\python.exe fetch_clean_db.py

echo.
pause