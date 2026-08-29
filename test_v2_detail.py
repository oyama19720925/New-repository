# C:\stock_system\test_v2_detail.py
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
API_KEY = os.getenv("JQUANTS_API_KEY", "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU")

BASE_URL = "https://api.jquants.com/v2"
HEADERS = {"x-api-key": API_KEY}

# 直近の営業日
today = datetime.now()
date_str = today.strftime("%Y-%m-%d")
date_str_nodash = today.strftime("%Y%m%d")

print("=" * 60)
print(f"テスト日付: {date_str}")
print("=" * 60)

# ── テスト1: 上場銘柄一覧 ──────────────────────────────
print("\n📋 [1] 上場銘柄一覧 /equities/master")
r = requests.get(f"{BASE_URL}/equities/master", headers=HEADERS)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json().get("data", [])
    print(f"   件数: {len(data)}")
    print(f"   サンプル: {data[0] if data else 'なし'}")

# ── テスト2: 株価四本値（銘柄指定）──────────────────────
print("\n📈 [2] 株価四本値 /equities/bars/daily (code=7203 トヨタ)")
r = requests.get(
    f"{BASE_URL}/equities/bars/daily",
    headers=HEADERS,
    params={"code": "7203", "date": date_str}
)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json().get("data", [])
    print(f"   件数: {len(data)}")
    print(f"   サンプル: {data[0] if data else 'なし'}")
else:
    print(f"   Response: {r.text[:200]}")

# ── テスト3: 株価四本値（日付指定）──────────────────────
print(f"\n📈 [3] 株価四本値 /equities/bars/daily (date={date_str})")
r = requests.get(
    f"{BASE_URL}/equities/bars/daily",
    headers=HEADERS,
    params={"date": date_str}
)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json().get("data", [])
    print(f"   件数: {len(data)}")
    print(f"   サンプル: {data[0] if data else 'なし'}")
else:
    print(f"   Response: {r.text[:200]}")

# ── テスト4: 財務情報（銘柄指定）────────────────────────
print("\n💰 [4] 財務情報 /fins/summary (code=7203 トヨタ)")
r = requests.get(
    f"{BASE_URL}/fins/summary",
    headers=HEADERS,
    params={"code": "7203"}
)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json().get("data", [])
    print(f"   件数: {len(data)}")
    print(f"   サンプル: {data[0] if data else 'なし'}")
else:
    print(f"   Response: {r.text[:200]}")

# ── テスト5: 財務情報（日付指定）────────────────────────
print(f"\n💰 [5] 財務情報 /fins/summary (date={date_str})")
r = requests.get(
    f"{BASE_URL}/fins/summary",
    headers=HEADERS,
    params={"date": date_str}
)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json().get("data", [])
    print(f"   件数: {len(data)}")
    print(f"   サンプル: {data[0] if data else 'なし'}")
else:
    print(f"   Response: {r.text[:200]}")

# ── テスト6: 過去日付で株価取得 ──────────────────────────
past_date = (today - timedelta(days=5)).strftime("%Y-%m-%d")
print(f"\n📅 [6] 過去日付 /equities/bars/daily (date={past_date})")
r = requests.get(
    f"{BASE_URL}/equities/bars/daily",
    headers=HEADERS,
    params={"date": past_date}
)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    data = r.json().get("data", [])
    print(f"   件数: {len(data)}")
    print(f"   サンプル: {data[0] if data else 'なし'}")
else:
    print(f"   Response: {r.text[:200]}")

print("\n" + "=" * 60)
print("✅ テスト完了")
print("=" * 60)