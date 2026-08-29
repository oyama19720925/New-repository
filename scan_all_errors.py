with open('app.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

print("=== 文字化け疑いの行 ===")
suspicious = []
for i, line in enumerate(lines, start=1):
    if ('\ufffd' in line or 'ぁE' in line or '❁' in line or 
        '抁' in line or '宁E' in line or '坁' in line or
        'E)' in line or 'EE' in line or '忁' in line):
        suspicious.append((i, line))
        print(f"line {i}: {repr(line)}")

if not suspicious:
    print("✅ 文字化けは見つかりませんでした！")
else:
    print(f"\n⚠️ 合計 {len(suspicious)} 行に問題あり")