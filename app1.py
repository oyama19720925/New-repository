import streamlit as st
import pandas as pd

st.title("📈 株価スクリーナー - テスト版")

# CSVアップロード
uploaded_file = st.file_uploader("CSVファイルをアップロード", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success(f"✅ データ読み込み成功: {len(df)} 行")
    
    # 列名表示
    st.write("### 📋 CSVの列名")
    st.write(df.columns.tolist())
    
    # データプレビュー
    st.write("### 📊 データプレビュー")
    st.dataframe(df.head())
    
    # サイドバーにドロップダウン
    st.sidebar.header("📋 列名の設定")
    col_select = st.sidebar.selectbox("テスト用ドロップダウン", df.columns.tolist())
    st.sidebar.write(f"選択した列: {col_select}")
else:
    st.info("👆 CSVファイルをアップロードしてください")