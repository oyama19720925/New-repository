with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if 'read_csv' in line or 'open(' in line or 'encoding' in line:
        print(f'行{i:3d}: {line.rstrip()}')