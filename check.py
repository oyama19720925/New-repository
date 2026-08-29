# 最小テスト用app.pyを作成
content = '''import streamlit as st
st.title("テスト")
st.write("動作確認OK")
'''
with open(r'C:\stock_system\test_app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("test_app.py 作成完了")