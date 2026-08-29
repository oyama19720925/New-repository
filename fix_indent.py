# fix_indent.py
with open(r"C:\stock_system\app.py", "r", encoding="utf-8") as f:
    content = f.read()

# 旧関数を新関数に置き換え
old_func_start = "def fetch_fundamental("
new_func = '''def fetch_fundamental(code, current_price=None):
    url = f"{JQUANTS_BASE}/v2/fins/summary"
    headers = {"X-API-KEY": JQUANTS_API_KEY}
    params = {"code": str(code)}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            items = data.get("fins_summary") or data.get("FInsSummary") or []

            if not items:
                return {"error": "データが空です", "raw": data}

            if isinstance(items, list):
                if len(items) == 0:
                    return {"error": "データが空リストです", "raw": data}
                latest = items[0]
            elif isinstance(items, dict):
                latest = items
            else:
                return {"error": f"予期しないデータ形式: {type(items)}", "raw": data}

            if not isinstance(latest, dict):
                return {"error": f"latestが辞書ではありません: {type(latest)}", "raw": data}

            eps    = latest.get("EPS")
            bps    = latest.get("BPS")
            roe    = latest.get("ROE")
            np_    = latest.get("NP")
            eq     = latest.get("Eq")
            sales  = latest.get("Sales")
            op     = latest.get("OP")
            cfo    = latest.get("CFO")
            feps   = latest.get("FEPS")
            fdiv   = latest.get("FDivAnn")
            fsales = latest.get("FSales")
            fop    = latest.get("FOP")
            eqar   = latest.get("EqAR")

            per, pbr = None, None
            if current_price:
                try:
                    eps_v = float(eps) if eps not in [None, "", "0", 0] else None
                    bps_v = float(bps) if bps not in [None, "", "0", 0] else None
                    if eps_v and eps_v != 0:
                        per = round(current_price / eps_v, 2)
                    if bps_v and bps_v != 0:
                        pbr = round(current_price / bps_v, 2)
                except (ValueError, TypeError):
                    pass

            result = {
                "PER":          per,
                "PBR":          pbr,
                "ROE":          roe,
                "EPS":          eps,
                "BPS":          bps,
                "純利益":       np_,
                "自己資本":     eq,
                "売上高":       sales,
                "営業利益":     op,
                "営業CF":       cfo,
                "予想EPS":      feps,
                "予想配当":     fdiv,
                "予想売上":     fsales,
                "予想営業利益": fop,
                "自己資本比率": eqar,
                "取得日時":     datetime.now().strftime("%Y-%m-%d %H:%M"),
                "raw":          latest
            }
            return result

        else:
            return {
                "error":  f"HTTPエラー {response.status_code}",
                "detail": response.text[:300]
            }

    except Exception as e:
        return {"error": str(e)}
'''

# 関数の開始位置を特定して置換
lines = content.split('\n')
start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if line.strip().startswith("def fetch_fundamental("):
        start_idx = i
    if start_idx is not None and i > start_idx:
        # 次のdef または空行+defで終了を検出
        if line.startswith("def ") or (line.startswith("class ")):
            end_idx = i
            break

if start_idx is None:
    print("❌ fetch_fundamental 関数が見つかりません")
else:
    if end_idx is None:
        end_idx = len(lines)
    
    print(f"✅ 関数発見: {start_idx+1}行目 〜 {end_idx}行目")
    
    # バックアップ
    with open(r"C:\stock_system\app.py.bak", "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ バックアップ作成: app.py.bak")
    
    # 置換
    new_lines = lines[:start_idx] + new_func.split('\n') + lines[end_idx:]
    new_content = '\n'.join(new_lines)
    
    with open(r"C:\stock_system\app.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("✅ 関数置換完了")

# 構文チェック
import ast
try:
    with open(r"C:\stock_system\app.py", "r", encoding="utf-8") as f:
        source = f.read()
    ast.parse(source)
    print("✅ 構文チェック: 問題なし")
except SyntaxError as e:
    print(f"❌ 構文エラー: {e}")