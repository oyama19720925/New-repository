 
with open('app.py', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if 'run_backtest' in line or 'bt_short' in line or 'bt_long' in line:
        print(f'行{i:4d}: {line}', end='')