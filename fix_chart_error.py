# fix_chart_error.py

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# 修正前：result_df が未定義の場合にエラーになるコード
OLD = "        if len(result_df) > 0:"

# 修正後：session_state 経由で安全にアクセス
NEW = "        if 'result_df' in st.session_state and len(st.session_state['result_df']) > 0:"

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    print("✅ Step1: result_df チェックを修正しました")
else:
    print("⚠️ Step1: 対象行が見つかりません（手動確認が必要）")

# result_df の参照をすべて session_state 経由に変更
OLD2 = """            chart_options = [
                f"{row['Code']} - {row.get('Name', row['Code'])}"
                for _, row in result_df.iterrows()
            ]"""

NEW2 = """            result_df = st.session_state['result_df']
            chart_options = [
                f"{row['Code']} - {row.get('Name', row['Code'])}"
                for _, row in result_df.iterrows()
            ]"""

if OLD2 in content:
    content = content.replace(OLD2, NEW2, 1)
    print("✅ Step2: result_df の参照を session_state 経由に修正しました")
else:
    print("⚠️ Step2: 対象ブロックが見つかりません（手動確認が必要）")

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("\n✅ 修正完了！")