import jquantsapi

API_KEY = "ここにAPIキーを入力"

client = jquantsapi.ClientV2(api_key=API_KEY)

# 利用可能なメソッド一覧を表示
methods = [m for m in dir(client) if not m.startswith("_") and "list" in m.lower()]
print("=== listを含むメソッド ===")
for m in methods:
    print(m)

print()
methods2 = [m for m in dir(client) if not m.startswith("_") and "info" in m.lower()]
print("=== infoを含むメソッド ===")
for m in methods2:
    print(m)

print()
methods3 = [m for m in dir(client) if not m.startswith("_") and "stock" in m.lower()]
print("=== stockを含むメソッド ===")
for m in methods3:
    print(m)

print()
print("=== 全メソッド一覧 ===")
all_methods = [m for m in dir(client) if not m.startswith("_")]
for m in all_methods:
    print(m)