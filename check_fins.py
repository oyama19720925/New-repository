import requests
import json

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
headers = {"X-API-KEY": API_KEY}
BASE = "https://api.jquants.com/v2"

# テスト銘柄（トヨタ）
code = "7203"

r = requests.get(f"{BASE}/fins/summary", headers=headers, params={"code": code})
print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    records = data.get("data", [])
    print(f"レコード数: {len(records)}")
    
    if records:
        # 最新レコードの全キーと値を表示
        latest = records[-1]
        print("\n=== 最新レコード 全フィールド ===")
        for k, v in latest.items():
            print(f"  {k}: {v}")
        
        print("\n=== 直近3件のEPS/BPS/PER/PBR関連 ===")
        for rec in records[-3:]:
            print(f"\n  期間: {rec.get('CurPerType')} / 開示: {rec.get('DiscDate')}")
            print(f"  EPS:  {rec.get('EPS')}")
            print(f"  BPS:  {rec.get('BPS')}")
            print(f"  FEPS: {rec.get('FEPS')}")
            print(f"  FDivAnn: {rec.get('FDivAnn')}")
            print(f"  ROE:  {rec.get('ROE')}")
            print(f"  EqAR: {rec.get('EqAR')}")
            print(f"  NP:   {rec.get('NP')}")
            print(f"  Eq:   {rec.get('Eq')}")
else:
    print(r.text)