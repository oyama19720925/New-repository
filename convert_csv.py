with open('stocks_OHLC_3months.csv', 'rb') as f:
    content = f.read()

try:
    text = content.decode('shift-jis')
    print('Shift-JISで読み込み成功！')
except:
    try:
        text = content.decode('cp932')
        print('CP932で読み込み成功！')
    except:
        text = content.decode('utf-8-sig')
        print('UTF-8-SIGで読み込み成功！')

with open('stocks_OHLC_3months.csv', 'w', encoding='utf-8', newline='') as f:
    f.write(text)

print('UTF-8に変換完了！')