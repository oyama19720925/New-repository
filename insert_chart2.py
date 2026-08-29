# insert_chart2.py

INSERT_CODE = '''
        # ══════════════════════════════════════════════
        # 📊 選択銘柄チャート表示セクション
        # ══════════════════════════════════════════════
        st.markdown("---")
        st.markdown("## 📈 銘柄チャート確認")

        from chart_section import plot_stock_chart

        if len(result_df) > 0:
            chart_options = [
                f"{row['Code']} - {row.get('Name', row['Code'])}"
                for _, row in result_df.iterrows()
            ]
            selected_chart_stocks = st.multiselect(
                "📌 チャートを表示する銘柄を選択（最大3銘柄）",
                options=chart_options,
                default=chart_options[:min(3, len(chart_options))],
                max_selections=3,
                key="chart_select"
            )
            CHART_COLORS = ["#00bfff", "#ff8800", "#00ff88"]
            if selected_chart_stocks:
                for i, sel in enumerate(selected_chart_stocks):
                    code = sel.split(" - ")[0].strip()
                    df_s = df_all[df_all["Code"] == code].copy()
                    if len(df_s) == 0:
                        st.warning(f"⚠️ {code} のデータが見つかりません")
                        continue
                    name  = df_s["Name"].iloc[0] if "Name" in df_s.columns else code
                    color = CHART_COLORS[i % len(CHART_COLORS)]
                    fig   = plot_stock_chart(df_s, code, name, color)
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{code}")

                    col1, col2, col3, col4 = st.columns(4)
                    latest = df_s.sort_values("Date").iloc[-1]
                    prev   = df_s.sort_values("Date").iloc[-2] if len(df_s) > 1 else latest
                    change     = latest["Close"] - prev["Close"]
                    change_pct = (change / prev["Close"] * 100) if prev["Close"] != 0 else 0
                    arrow      = "🔺" if change >= 0 else "🔻"
                    col1.metric("📅 最終日",         str(latest["Date"])[:10])
                    col2.metric("💴 終値",           f"¥{latest['Close']:,.0f}")
                    col3.metric(f"{arrow} 前日比",   f"{change:+,.0f}円",
                                f"{change_pct:+.2f}%")
                    col4.metric("📊 出来高",         f"{latest['Volume']:,.0f}")
                    st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.info("👆 上のドロップダウンから銘柄を選択してください")
        else:
            st.info("🔍 先にスクリーニングを実行してください")

        st.markdown("---")
'''

with open("app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# 行676付近の「バックテスト実行ボタン」コメント行を探す
insert_line = None
for i, line in enumerate(lines):
    if "バックテスト実行ボタン" in line:
        insert_line = i  # この行の直前に挿入
        break

if insert_line is None:
    print("❌ 挿入位置が見つかりません")
else:
    # 挿入
    new_lines = lines[:insert_line] + [INSERT_CODE + "\n"] + lines[insert_line:]
    with open("app.py", "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"✅ 行{insert_line+1}の直前にチャートセクションを挿入しました！")
    print(f"   挿入後の総行数: {len(new_lines)}")