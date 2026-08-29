# C:\stock_system\integrate_fundamental_ui.py

path = r"C:\stock_system\app.py"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# ① show_fundamental_section 関数を追加（既存なら置換）
import re

new_ui_func = '''
def show_fundamental_section(selected_code: str, selected_name: str, current_price: float):
    """ファンダメンタル分析セクションの表示"""
    st.markdown("---")
    st.subheader(f"📊 ファンダメンタル分析：{selected_name}（{selected_code}）")

    with st.spinner("ファンダメンタルデータ取得中..."):
        fd = fetch_fundamental(selected_code, current_price)

    if fd is None:
        st.warning("⚠️ データが取得できませんでした")
        return

    if "error" in fd:
        st.error(f"❌ エラー: {fd['error']}")
        return

    # メタ情報
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.caption(f"📅 最新開示日: {fd.get('_disc_date', 'N/A')}")
    with col_m2:
        st.caption(f"📅 FY決算期末: {fd.get('_fy_date', 'N/A')}")

    # バリュエーション
    st.markdown("#### 💹 バリュエーション")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PER（倍）",    fd.get("PER(倍)",       "N/A"), help="株価収益率")
    c2.metric("PBR（倍）",    fd.get("PBR(倍)",       "N/A"), help="株価純資産倍率")
    c3.metric("ROE（%）",     fd.get("ROE(%)",        "N/A"), help="自己資本利益率")
    c4.metric("配当利回り（%）", fd.get("配当利回り(%)", "N/A"), help="予想配当利回り")

    # 1株指標
    st.markdown("#### 📌 1株指標")
    c5, c6, c7, c8 = st.columns(4)
    c5.metric("EPS（円）",     fd.get("EPS(円)",      "N/A"), help="1株当たり利益")
    c6.metric("BPS（円）",     fd.get("BPS(円)",      "N/A"), help="1株当たり純資産")
    c7.metric("予想EPS（円）",  fd.get("予想EPS(円)",  "N/A"), help="通期予想EPS")
    c8.metric("予想配当（円）",  fd.get("予想配当(円)", "N/A"), help="通期予想配当")

    # 業績（億円）
    st.markdown("#### 🏢 業績（直近FY・億円）")
    c9, c10, c11, c12 = st.columns(4)
    c9.metric("売上高",    fd.get("売上高(億円)",   "N/A"))
    c10.metric("営業利益", fd.get("営業利益(億円)", "N/A"))
    c11.metric("純利益",   fd.get("純利益(億円)",   "N/A"))
    c12.metric("営業CF",   fd.get("営業CF(億円)",   "N/A"))

    # 財務健全性
    st.markdown("#### 🛡️ 財務健全性")
    c13, c14, c15, c16 = st.columns(4)
    c13.metric("自己資本比率（%）", fd.get("自己資本比率(%)", "N/A"))
    c14.metric("", "")
    c15.metric("", "")
    c16.metric("", "")

'''

# show_fundamental_section が既存なら置換、なければ末尾に追加
pattern_ui = r'def show_fundamental_section\(.*?(?=\ndef |\Z)'
if re.search(pattern_ui, content, re.DOTALL):
    content = re.sub(pattern_ui, new_ui_func.strip() + "\n\n", content, flags=re.DOTALL)
    print("✅ show_fundamental_section を更新しました")
else:
    content += "\n" + new_ui_func
    print("✅ show_fundamental_section を末尾に追加しました")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ app.py への書き込み完了")