with open('app.py', encoding='utf-8') as f:
    lines = f.readlines()

found = []
for i, l in enumerate(lines):
    if 'filtered_df' in l:
        found.append((i+1, l.rstrip()))

if found:
    for ln, txt in found:
        print(str(ln) + ': ' + txt)
else:
    print('filtered_df は存在しません')
