# fix_script.py を作成
@"
f=open('fetch_3months.py','rb')
c=f.read()
f.close()
lines=c.split(b'\n')
print(f'Total lines: {len(lines)}')
for i,l in enumerate(lines):
    print(i+1, repr(l))
"@ | Out-File -FilePath fix_script.py -Encoding utf8

python fix_script.py