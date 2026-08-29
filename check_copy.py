with open('app.py', 'rb') as f:
    raw = f.read()

# エラー位置185-186を確認
print("=== app.py 位置185前後 ===")
print(raw[180:195].hex())

with open('app_repaired.py', 'rb') as f:
    raw2 = f.read()

print("\n=== app_repaired.py 位置185前後 ===")
print(raw2[180:195].hex())

print("\n=== 同じファイルか？ ===")
print("YES (同一)" if raw == raw2 else "NO (異なる！)")

print(f"\napp.py サイズ: {len(raw)} bytes")
print(f"app_repaired.py サイズ: {len(raw2)} bytes")