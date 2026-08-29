with open('app.py', 'rb') as f:
    raw = f.read()
print('app.py 先頭バイト:', raw[:3].hex())
print('app.py 185-190バイト目:', raw[185:191].hex())

with open('stocks_OHLC_3months.csv', 'rb') as f:
    raw2 = f.read(200)
print('CSV 先頭バイト:', raw2[:3].hex())
print('CSV 180-190バイト目:', raw2[180:191].hex())