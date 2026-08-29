with open('app.py', 'rb') as f:
    content = f.read()
content = content.replace(b'stocks_OHLC_20260515_20260813.csv', b'stocks_OHLC_3months.csv')
with open('app.py', 'wb') as f:
    f.write(content)
print('完了！')
with open('app.py', 'rb') as f:
    content = f.read()

content = content.replace(
    b'stocks_OHLC_20260515_20260813.csv',
    b'stocks_OHLC_3months.csv'
)

with open('app.py', 'wb') as f:
    f.write(content)

print('完了！置換しました！')
