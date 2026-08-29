with open('app.py', encoding='utf-8') as f:
    lines = f.readlines()

start = max(0, 1205 - 1)
end = min(len(lines), 1225)

for i in range(start, end):
    print(str(i+1) + ': ' + lines[i].rstrip())