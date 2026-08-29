# check_missing_detail2.py
import pandas as pd

CSV_PATH = r"C:\stock_system\stocks_OHLC_20260515_20260818_fixed.csv"
df = pd.read_csv(CSV_PATH, dtype={"Code": str})
df["Date"] = pd.to_datetime(df["Date"])

missing = df[df["Volume"].isna() | (df["Volume"] == 0)]
valid   = df[df["Volume"].notna() & (df["Volume"] != 0)]

# 各銘柄の総日数・欠損日数・欠損率
total_by_code   = df.groupby("Code")["Date"].count().rename("total")
missing_by_code = missing.groupby("Code")["Date"].count().rename("missing")
summary = pd.concat([total_by_code, missing_by_code], axis=1).fillna(0)
summary["missing"] = summary["missing"].astype(int)
summary["miss_rate"] = (summary["missing"] / summary["total"] * 100).round(1)

# 欠損率100%（全期間欠損）の銘柄
all_missing = summary[summary["miss_rate"] == 100.0]
partial_missing = summary[(summary["miss_rate"] > 0) & (summary["miss_rate"] < 100.0)]
no_missing = summary[summary["miss_rate"] == 0]

print(f"=== 欠損率別 銘柄数 ===")
print(f"欠損率 100%（全期間欠損） : {len(all_missing):,} 銘柄")
print(f"欠損率 1〜99%（部分欠損） : {len(partial_missing):,} 銘柄")
print(f"欠損率   0%（正常）       : {len(no_missing):,} 銘柄")

print(f"\n=== 部分欠損の銘柄（上位20）===")
# Code+Nameを付けて表示
name_map = df.drop_duplicates("Code").set_index("Code")["Name"]
partial_with_name = partial_missing.join(name_map)
print(partial_with_name.sort_values("miss_rate", ascending=False).head(20).to_string())

print(f"\n=== 部分欠損の銘柄：欠損期間の特定（最初の5銘柄）===")
sample_codes = partial_missing.index[:5].tolist()
for code in sample_codes:
    sub = df[df["Code"] == code].sort_values("Date")
    miss_dates = sub[sub["Volume"].isna() | (sub["Volume"] == 0)]["Date"]
    valid_dates = sub[sub["Volume"].notna() & (sub["Volume"] != 0)]["Date"]
    name = name_map.get(code, "不明")
    print(f"\n  [{code}] {name}")
    print(f"    欠損期間: {miss_dates.min().date()} 〜 {miss_dates.max().date()} ({len(miss_dates)}日)")
    print(f"    有効期間: {valid_dates.min().date()} 〜 {valid_dates.max().date()} ({len(valid_dates)}日)")