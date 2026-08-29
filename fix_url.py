with open('C:/stock_system/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# v1 → v2 に修正
old_patterns = [
    'https://api.jquants.com/v1/fins/summary',
    'https://api.jquants.com/v1',
]

for old in old_patterns:
    if old in content:
        new = old.replace('/v1', '/v2')
        content = content.replace(old, new)
        print(f'修正: {old} → {new}')

with open('C:/stock_system/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('完了')

# 確認：fins/summaryの周辺行を表示
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'fins/summary' in line or 'jquants.com' in line:
        print(f'行{i+1}: {line.strip()}')