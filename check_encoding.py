import chardet

with open('stocks_OHLC_3months.csv', 'rb') as f:
    raw = f.read(10000)

result = chardet.detect(raw)
print(result)