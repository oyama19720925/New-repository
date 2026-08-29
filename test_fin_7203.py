import os
import requests

API_KEY = os.getenv("JQUANTS_API_KEY", "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU")
headers = {"x-api-key": API_KEY}
url = "https://api.jquants.com/v2/fins/summary"

for code in ["72030", "7203"]:
    r = requests.get(url, headers=headers, params={"code": code}, timeout=15)
    print(f"--- code={code} (ステータス: {r.status_code}) ---")
    if r.status_code == 200:
        data = r.json()
        items = data.get("data") or data.get("fins_summary") or data.get("summary") or []
        print(f"取得件数: {len(items)}")
        if items:
            last = items[-1]
            print("直近レコード主要項目:")
            for k in ["DiscDate", "DocType", "CurPerType", "BPS", "EPS", "FEPS", "NxFEPS"]:
                print(f"  {k}: {last.get(k)}")
    else:
        print(r.text[:200])