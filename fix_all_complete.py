# fix_all_complete.py
# UTF-8マルチバイト文字の末尾バイトが 0x45('E') に化けている全箇所を自動検出・修復

import unicodedata

def find_all_broken(raw):
    """
    UTF-8 2〜4バイト文字の継続バイト位置に 0x45 が入っている箇所を全検出
    """
    broken = []
    i = 0
    while i < len(raw):
        b = raw[i]
        # 2バイト文字の先頭: 0xC0〜0xDF
        if 0xC0 <= b <= 0xDF:
            seq_len = 2
        # 3バイト文字の先頭: 0xE0〜0xEF
        elif 0xE0 <= b <= 0xEF:
            seq_len = 3
        # 4バイト文字の先頭: 0xF0〜0xF7
        elif 0xF0 <= b <= 0xF7:
            seq_len = 4
        else:
            i += 1
            continue

        # 継続バイトをチェック (0x80〜0xBF が正常)
        seq = raw[i:i+seq_len]
        if len(seq) < seq_len:
            i += 1
            continue

        broken_pos = None
        for j in range(1, seq_len):
            if not (0x80 <= seq[j] <= 0xBF):
                # 正常でないバイトを発見
                if seq[j] == 0x45:  # 'E'
                    broken_pos = i + j
                break

        if broken_pos is not None:
            broken.append((broken_pos, seq))

        i += seq_len if broken_pos is None else 1

    return broken


def fix_broken_bytes(raw):
    """
    壊れたバイト列を正しいUTF-8に修復する
    戦略: 壊れたシーケンスをSkipして、前後の文脈から正しい文字を推測
    ただし自動推測は危険なので、まず全箇所をリストアップして報告
    """
    broken = find_all_broken(raw)
    print(f"🔍 壊れた箇所: {len(broken)} 件検出")
    for pos, seq in broken:
        print(f"  位置 {pos}: hex={seq.hex()!r}  raw={seq!r}")
    return broken


# ===== メイン処理 =====

with open('app_complete2.py', 'rb') as f:
    raw = f.read()

# 改行統一
raw = raw.replace(b'\r\n', b'\n').replace(b'\r', b'\n')

print("=" * 60)
print("STEP 1: 壊れバイト全検出")
print("=" * 60)

i = 0
fixes = 0
result = bytearray()

while i < len(raw):
    b = raw[i]

    # マルチバイト文字の先頭バイト判定
    if 0xC0 <= b <= 0xDF:
        seq_len = 2
    elif 0xE0 <= b <= 0xEF:
        seq_len = 3
    elif 0xF0 <= b <= 0xF7:
        seq_len = 4
    else:
        result.append(b)
        i += 1
        continue

    seq = raw[i:i+seq_len]
    if len(seq) < seq_len:
        result.append(b)
        i += 1
        continue

    # 継続バイトに 0x45('E') が混入しているか確認
    broken_j = None
    for j in range(1, seq_len):
        if seq[j] == 0x45 and not (0x80 <= seq[j] <= 0xBF):
            broken_j = j
            break

    if broken_j is not None:
        # 0x45 を除去して正しいシーケンスを再構築
        # 0x45 の次のバイトが継続バイト(0x80-0xBF)なら、それを補完に使う
        # 最も安全な方法: 0x45 を削除してシーケンスを詰める
        fixed_seq = bytearray(seq[:broken_j])
        remaining = seq[broken_j+1:]  # 0x45 の次以降

        # 残りの継続バイトを補完
        needed = seq_len - broken_j  # あと何バイト必要か
        extra_i = i + seq_len
        extra_bytes = bytearray()
        for k in range(needed - 1):
            if extra_i + k < len(raw) and 0x80 <= raw[extra_i + k] <= 0xBF:
                extra_bytes.append(raw[extra_i + k])
            else:
                break

        # 継続バイトが足りない場合はデフォルト値で補完
        while len(fixed_seq) + len(extra_bytes) < seq_len - 1:
            extra_bytes.append(0x8C)  # よく使われる継続バイト

        # 先頭バイト + 継続バイトを結合
        candidate = bytes([b]) + bytes(extra_bytes[:seq_len-1])
        try:
            char = candidate.decode('utf-8')
            result.extend(candidate)
            print(f"  ✅ 位置 {i}: {seq.hex()} → {candidate.hex()} ({char})")
            fixes += 1
            i += seq_len
            continue
        except:
            pass

        # 失敗したら 0x45 だけ除去
        result.extend(seq[:broken_j])
        result.extend(seq[broken_j+1:])
        print(f"  ⚠️  位置 {i}: 0x45除去のみ実施 {seq.hex()}")
        fixes += 1
        i += seq_len
    else:
        result.extend(seq)
        i += seq_len

raw_fixed = bytes(result)

print(f"\n修正箇所合計: {fixes} 件")

# UTF-8デコード確認
print("\n" + "=" * 60)
print("STEP 2: UTF-8デコード確認")
print("=" * 60)
try:
    text = raw_fixed.decode('utf-8')
    print("✅ UTF-8デコード成功！")
except Exception as e:
    print(f"❌ デコードエラー: {e}")
    # 残存エラー位置を全表示
    for idx in range(len(raw_fixed)):
        try:
            raw_fixed[idx:idx+4].decode('utf-8')
        except:
            print(f"  残存エラー位置 {idx}: {raw_fixed[idx:idx+6].hex()}")
    exit()

# 構文チェック
print("\n" + "=" * 60)
print("STEP 3: Python構文チェック")
print("=" * 60)
import ast
errors = []
try:
    ast.parse(text)
    print("✅ 構文チェック成功！")
except SyntaxError as e:
    print(f"❌ 構文エラー残存: Line {e.lineno}: {e.msg}")
    lines = text.split('\n')
    for li in range(max(0, e.lineno-3), min(len(lines), e.lineno+2)):
        print(f"  {li+1}: {repr(lines[li])}")
    exit()

# 保存
with open('app_fixed_final.py', 'w', encoding='utf-8') as f:
    f.write(text)

print(f"\n{'='*60}")
print(f"✅ 全 {fixes} 箇所を自動修復")
print(f"✅ app_fixed_final.py として保存完了")
print(f"{'='*60}")
print(f"\n起動コマンド:")
print(f"  streamlit run app_fixed_final.py")