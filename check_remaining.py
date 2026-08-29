with open('app.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

check_lines = [169, 170, 312, 313, 340]

print("=== 残り5行の詳細確認 ===")
for lineno in check_lines:
    line = lines[lineno-1]
    print(f"\nline {lineno}: {repr(line)}")
    print(f"  表示: {line.rstrip()}")
    has_replacement = '\ufffd' in line
    print(f"  文字化け文字(U+FFFD)あり: {has_replacement}")