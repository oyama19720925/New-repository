with open('app.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if '.csv' in line or 'read_csv' in line:
            print(f'行{i:4d}: {line}', end='')