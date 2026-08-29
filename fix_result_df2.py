# fix_result_df2.py

with open("app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# 行605の直後（行606の後）に result_df の格納処理を追加
# 行605: st.session_state['screen_results'] = results
# 行606: st.session_state['checked_codes']  = {r['Code']: False for r in results}
# → 行607に以下を挿入

insert_line = 606  # 0始まりで605番目 = 行606の後

new_lines = [
    "    # result_df を DataFrame として保存\n",
    "    import pandas as pd\n",
    "    if results:\n",
    "        st.session_state['result_df'] = pd.DataFrame(results)\n",
    "    else:\n",
    "        st.session_state['result_df'] = pd.DataFrame()\n",
]

lines = lines[:insert_line] + new_lines + lines[insert_line:]

with open("app.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("✅ 修正完了！")
print(f"挿入行: {insert_line + 1} 〜 {insert_line + len(new_lines)}")