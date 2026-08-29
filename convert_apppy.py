# app.pyをShift-JISからUTF-8に変換

encodings_to_try = ['shift-jis', 'cp932', 'utf-8-sig', 'cp775']

for enc in encodings_to_try:
    try:
        with open('app.py', 'r', encoding=enc) as f:
            content = f.read()
        print(f'✅ {enc} で読み込み成功！')
        
        # UTF-8で保存
        with open('app_utf8.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'✅ app_utf8.py として保存しました！')
        break
    except Exception as e:
        print(f'❌ {enc} 失敗: {e}')