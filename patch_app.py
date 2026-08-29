# patch_app.py
patch_code = '''

# =============================================
# API設定 & ファンダメンタルデータ取得
# =============================================
API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
BASE_URL = "https://api.jquants.com/v2"

def get_fundamental_data(code):
    code_str = str(code).zfill(5)
    url = f"{BASE_URL}/fins/summary"
    headers = {"X-API-KEY": API_KEY}
    params = {"code": code_str}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            records = resp.json().get("data", [])
            if records:
                return pd.DataFrame(records)
        return None
    except Exception as e:
        st.error(f"取得エラー: {e}")
        return None

def display_fundamental_data(code, name=""):
    st.subheader(f"📊 ファンダメンタルデータ: {name} ({code})")
    with st.spinner("データ取得中..."):
        df = get_fundamental_data(code)
    if df is None or df.empty:
        st.warning("データが取得できませんでした")
        return
    if "DiscDate" in df.columns:
        df = df.sort_values("DiscDate", ascending=False)
    latest = df.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        v = latest.get("PER", "N/A")
        st.metric("PER", f"{float(v):.2f}倍" if v not in ["N/A", None, ""] else "N/A")
    with col2:
        v = latest.get("PBR", "N/A")
        st.metric("PBR", f"{float(v):.2f}倍" if v not in ["N/A", None, ""] else "N/A")
    with col3:
        v = latest.get("ROE", "N/A")
        st.metric("ROE", f"{float(v):.2f}%" if v not in ["N/A", None, ""] else "N/A")
    with col4:
        v = latest.get("MarketCapitalization", "N/A")
        st.metric("時価総額", f"{float(v)/1e8:.0f}億円" if v not in ["N/A", None, ""] else "N/A")
    with st.expander("📋 詳細データ"):
        st.dataframe(df.head(8), use_container_width=True)
'''

with open('C:/stock_system/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'get_fundamental_data' not in content:
    content = content.replace('import requests', 'import requests' + patch_code, 1)
    with open('C:/stock_system/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ 追加完了")
else:
    print("✅ 既に存在します（変更不要）")