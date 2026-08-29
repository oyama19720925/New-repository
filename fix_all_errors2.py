with open('app.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

fixes = {
    21:  '# ========== データ読み込み ==========\n',
    92:  '# ========== サイドバー分析ツール ==========\n',
    93:  'st.sidebar.header("📊 フィルタ＆ツール")\n',
    95:  '# --- 移動平均 ---\n',
    96:  'st.sidebar.subheader("📉 移動平均")\n',
    97:  'use_ma = st.sidebar.checkbox("移動平均を使用", value=True)\n',
    99:  '    ma_short = st.sidebar.number_input("短期MA（日）", min_value=1, max_value=200, value=5)\n',
    100: '    ma_long  = st.sidebar.number_input("長期MA（日）", min_value=1, max_value=200, value=25)\n',
    111: '    rsi_period = st.sidebar.number_input("RSI期間（日）", min_value=2, max_value=100, value=14)\n',
    123: '    stoch_k   = st.sidebar.number_input("%K期間（日）", min_value=1, max_value=100, value=14)\n',
    124: '    stoch_d   = st.sidebar.number_input("%D期間（日）", min_value=1, max_value=100, value=3)\n',
    128: '        stoch_pos_min = st.sidebar.slider("%K 最小値", 0, 100, 20)\n',
    129: '        stoch_pos_max = st.sidebar.slider("%K 最大値", 0, 100, 80)\n',
    142: 'st.sidebar.subheader("📦 出来高")\n',
    145: '    vol_days = st.sidebar.number_input("平均日数", min_value=1, max_value=60, value=5)\n',
    146: '    vol_min  = st.sidebar.number_input("最小出来高（平均）", min_value=0, value=100000, step=10000)\n',
    151: '# ========== データ絞り込み ==========\n',
    163: 'st.write(f"📋 対象データ: {len(target_df):,} 行 / {target_df[COL_CODE].nunique():,} 銘柄")\n',
    187: '        # ========== 移動平均 ==========\n',
    288: '        st.warning("⚠️ フィルタが全てOFFです。少なくとも1つをONにしてください。")\n',
    294: '            st.warning("⚠️ 条件に合う銘柄が見つかりませんでした。条件を緩めてみてください。")\n',
    296: '            st.success(f"✅ {len(result_df)} 銘柄が条件に一致しました！")\n',
    336: 'st.header("📊 個別チャート")\n',
    337: 'chart_code = st.text_input("銘柄コードを入力（例: 7203）", value="")\n',
    343: '        st.warning(f"⚠️ 銘柄コード {chart_code} のデータが見つかりません。")\n',
    366: '        # 移動平均線\n',
}

print("=== 修正開始 ===")
for lineno, new_content in fixes.items():
    print(f"修正前 line {lineno}: {repr(lines[lineno-1])}")
    lines[lineno-1] = new_content
    print(f"修正後 line {lineno}: {repr(lines[lineno-1])}")
    print()

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ app.py を修正・保存しました！")