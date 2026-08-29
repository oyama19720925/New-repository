# check_volume_missing.py
import pandas as pd

path = r"C:\stock_system\stocks_OHLC_20260515_20260818_fixed.csv"
df = pd.read_csv(path, encoding='utf-8', low_memory=False)
df.columns = df.columns.str.strip()

print("=" * 60)
print("📊 Volume欠損の分析")
print("=" * 60)

# 欠損と非欠損に分ける
df_ok   = df[df['Volume'].notna()]
df_miss = df[df['Volume'].isna()]

print(f"✅ Volume有り: {len(df_ok):,}行")
print(f"❌ Volume無し: {len(df_miss):,}行")

# 日付別の欠損状況
print("\n📅 日付別 Volume欠損行数（先頭20日）:")
date_miss = df_miss.groupby('Date').size().reset_index(name='欠損数')
date_ok   = df_ok.groupby('Date').size().reset_index(name='有り数')
date_summary = pd.merge(date_ok, date_miss, on='Date', how='outer').fillna(0)
date_summary['欠損率'] = (date_summary['欠損数'] / 
                          (date_summary['有り数'] + date_summary['欠損数']) * 100).round(1)
print(date_summary.sort_values('Date').head(20).to_string(index=False))

# Market別の欠損状況
print("\n🏢 Market別 Volume欠損状況:")
mkt_summary = df.groupby('Market')['Volume'].agg(
    総行数='count',
    有り数=lambda x: x.notna().sum(),
    欠損数=lambda x: x.isna().sum()
).reset_index()
mkt_summary['欠損率(%)'] = (mkt_summary['欠損数'] / 
                             (mkt_summary['有り数'] + mkt_summary['欠損数']) * 100).round(1)
print(mkt_summary.to_string(index=False))

# Sector別の欠損状況
print("\n🏭 Sector別 Volume欠損状況（欠損率上位10）:")
sec_summary = df.groupby('Sector')['Volume'].agg(
    有り数=lambda x: x.notna().sum(),
    欠損数=lambda x: x.isna().sum()
).reset_index()
sec_summary['欠損率(%)'] = (sec_summary['欠損数'] / 
                             (sec_summary['有り数'] + sec_summary['欠損数']) * 100).round(1)
print(sec_summary.sort_values('欠損率(%)', ascending=False).head(10).to_string(index=False))

# Volume無しのサンプル行
print("\n📌 Volume無しのサンプル（先頭5行）:")
print(df_miss[['Date','Code','Name','Market','Sector','Close','Volume','MktCap']].head())