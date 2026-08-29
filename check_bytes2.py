with open('app.py', 'rb') as f:
    raw = f.read(300)

print('最初の300バイト(hex):')
print(raw.hex())
print()
print('最初の300バイト(raw):')
print(raw)