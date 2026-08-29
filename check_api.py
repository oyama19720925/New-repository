import os
import requests

API_KEY = os.getenv("JQUANTS_API_KEY", "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU")
headers = {"x-api-key": API_KEY}
base = "https://api.jquants.com/v2"

print("--- 1. マスタAPI確認 ---")
r1 = requests.get(f"{base}/equities/master", headers=headers, timeout=10)
print(f"ステータス: {r1.status_code}")
if r1.status_code == 200:
    data1 = r1.json()
    items1 = data1.get("data") or data1.get("master") or []
    if items1:
        print("マスタ1件目のキー:", list(items1[0].keys()))
        print("マスタ1件目のデータ:", items1[0])
    else:
        print("マスタのデータが空です:", data1)
else:
    print("マスタ取得失敗:", r1.text[:200])

print("\n--- 2. 財務API確認 (13010) ---")
r2 = requests.get(f"{base}/fins/summary", headers=headers, params={"code": "13010"}, timeout=10)
print(f"ステータス: {r2.status_code}")
if r2.status_code == 200:
    data2 = r2.json()
    items2 = data2.get("fins_summary") or data2.get("data") or data2.get("summary") or []
    if items2:
        print("財務1件目のキー:", list(items2[-1].keys()))
        print("財務1件目のデータ:", items2[-1])
    else:
        print("財務のデータが空です:", data2)
else:
    print("財務取得失敗:", r2.text[:200])