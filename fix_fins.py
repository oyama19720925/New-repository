import re

with open('C:/stock_system/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# fetch_fundamental関数のitemsの行を探す
m = re.search(r'items = data\.get\(.+\)', content)
if m:
    print('現在の行:', m.group())
    old = m.group()
    new = 'items = data.get("data", [])'
    content = content.replace(old, new)
    with open('C:/stock_system/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('修正完了')
else:
    print('該当行が見つかりません')
    # fetch_fundamental関数周辺を表示
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'fetch_fundamental' in line or 'fins' in line.lower():
            print(f'行{i+1}: {line}')