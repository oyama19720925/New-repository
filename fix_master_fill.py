import pandas as pd

path = r"C:\stock_system\stocks_OHLC_20260515_20260818_merged.csv"
output_path = r"C:\stock_system\stocks_OHLC_20260515_20260818_fixed.csv"

print("📂 CSVを読み込み中...")
df = pd.read_csv(path, encoding='utf-8', low_memory=False)
df.columns = df.columns.str.strip()

print(f"✅ 読み込み完了: {len(df)}行")

# ── マスタ情報を持つ行からCode→Name/Sector/Marketのマッピングを作成 ──
master_cols = ['Name', 'Sector', 'Market']

df_master = df[df['Name'].notna()][['Code'] + master_cols].drop_duplicates('Code')
print(f"📋 マスタ情報のあるCode数: {len(df_master)}")

# Codeをインデックスにしてマッピング辞書を作成
master_map = df_master.set_index('Code')

# ── 全行にName/Sector/Marketを上書き埋め ──
for col in master_cols:
    df[col] = df['Code'].map(master_map[col])

# 埋め後の確認
filled = df['Name'].notna().sum()
print(f"✅ Name埋め後: {filled}行 / {len(df)}行 ({filled/len(df)*100:.1f}%)")

# Name無しのCodeを確認（マスタに存在しない銘柄）
missing_codes = df[df['Name'].isna()]['Code'].unique()
print(f"⚠️ マスタ未登録のCode数: {len(missing_codes)}")
if len(missing_codes) > 0:
    print(f"   サンプル: {missing_codes[:10].tolist()}")

# ── 保存 ──
print(f"\n💾 保存中: {output_path}")
df.to_csv(output_path, index=False, encoding='utf-8')
print("✅ 保存完了！")

# ── 最終確認 ──
print("\n📈 修正後の充填率:")
for col in ['Name', 'Sector', 'Market', 'Close', 'Volume', 'MktCap']:
    cnt = df[col].notna().sum()
    print(f"  {col:15s}: {cnt:>7,}件 ({cnt/len(df)*100:.1f}%)")