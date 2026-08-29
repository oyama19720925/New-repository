import streamlit as st
import requests
import pandas as pd

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
BASE = "https://api.jquants.com/v2"
HEADERS = {"x-api-key": API_KEY}

st.set_page_config(page_title="財務データビューア", layout="wide")
st.title("📊 日本株 財務データビューア")

# --- 銘柄入力 ---
col1, col2 = st.columns([1, 3])
with col1:
    code = st.text_input("銘柄コード（例：7203）", value="7203")

if st.button("📥 財務データ取得"):
    with st.spinner("データ取得中..."):

        # --- マスター情報取得 ---
        master_resp = requests.get(
            f"{BASE}/equities/master",
            headers=HEADERS,
            params={"code": code},
            timeout=10
        )
        master_data = master_resp.json().get("data", [])
        if master_data:
            m = master_data[-1]
            st.subheader(f"🏢 {m.get('CoName', '')}（{code}）")
            st.caption(f"セクター: {m.get('S33Nm', '')} ／ 市場: {m.get('ScaleCat', '')}")

        # --- 財務サマリー取得 ---
        fins_resp = requests.get(
            f"{BASE}/fins/summary",
            headers=HEADERS,
            params={"code": code},
            timeout=10
        )
        fins_data = fins_resp.json().get("data", [])

        if not fins_data:
            st.warning("財務データが取得できませんでした")
        else:
            latest = fins_data[-1]

            st.markdown("---")

            # --- 実績データ ---
            st.subheader("📈 直近実績")
            col1, col2, col3, col4 = st.columns(4)
            def fmt_oku(v):
                try:
                    return f"{float(v)/1e8:,.0f}億円" if v else "－"
                except:
                    return "－"
            def fmt_val(v, suffix=""):
                try:
                    return f"{float(v):,.2f}{suffix}" if v else "－"
                except:
                    return "－"

            col1.metric("売上高", fmt_oku(latest.get("Sales")))
            col2.metric("営業利益", fmt_oku(latest.get("OP")))
            col3.metric("純利益", fmt_oku(latest.get("NP")))
            col4.metric("EPS", fmt_val(latest.get("EPS"), "円"))

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("総資産", fmt_oku(latest.get("TA")))
            col2.metric("純資産", fmt_oku(latest.get("Eq")))
            col3.metric("自己資本比率", fmt_val(latest.get("EqAR", 0) if not latest.get("EqAR") == "" else None, "%") if latest.get("EqAR") else "－")
            col4.metric("BPS", fmt_val(latest.get("BPS"), "円"))

            col1, col2, col3 = st.columns(3)
            col1.metric("営業CF", fmt_oku(latest.get("CFO")))
            col2.metric("投資CF", fmt_oku(latest.get("CFI")))
            col3.metric("財務CF", fmt_oku(latest.get("CFF")))

            st.markdown("---")

            # --- 予想データ ---
            st.subheader("🎯 通期予想")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("売上高予想", fmt_oku(latest.get("FSales")))
            col2.metric("営業利益予想", fmt_oku(latest.get("FOP")))
            col3.metric("純利益予想", fmt_oku(latest.get("FNP")))
            col4.metric("EPS予想", fmt_val(latest.get("FEPS"), "円"))

            col1, col2 = st.columns(2)
            col1.metric("年間配当予想", fmt_val(latest.get("FDivAnn"), "円"))
            col2.metric("期末配当予想", fmt_val(latest.get("FDivFY"), "円"))

            st.markdown("---")

            # --- 期間情報 ---
            st.caption(
                f"📅 開示日: {latest.get('DiscDate', '')}　"
                f"期間: {latest.get('CurPerSt', '')} ～ {latest.get('CurPerEn', '')}　"
                f"種別: {latest.get('DocType', '')}　"
                f"四半期: {latest.get('CurPerType', '')}"
            )

            # --- 全データ表示（展開式） ---
            with st.expander("🔍 全フィールド表示"):
                df = pd.DataFrame([latest])
                st.dataframe(df.T.rename(columns={0: "値"}), use_container_width=True)

            # --- 過去データ推移 ---
            with st.expander("📉 過去の開示履歴"):
                hist_df = pd.DataFrame(fins_data)[
                    ["DiscDate", "CurPerType", "Sales", "OP", "NP", "EPS", "FSales", "FOP", "FNP", "FEPS"]
                ].copy()
                for col in ["Sales", "OP", "NP", "FSales", "FOP", "FNP"]:
                    hist_df[col] = pd.to_numeric(hist_df[col], errors="coerce") / 1e8
                hist_df = hist_df.rename(columns={
                    "Sales": "売上(億)", "OP": "営業利益(億)", "NP": "純利益(億)",
                    "FSales": "予想売上(億)", "FOP": "予想営業利益(億)", "FNP": "予想純利益(億)"
                })
                st.dataframe(hist_df.sort_values("DiscDate", ascending=False), use_container_width=True)