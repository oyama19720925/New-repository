# fix_fetch_fundamental_v2.py
path = r"C:\stock_system\app.py"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 旧 fetch_fundamental 関数を検索して置換
import re

new_func = '''def fetch_fundamental(code: str, current_price: float = 0) -> dict | None:
    """J-Quants /fins/summary からファンダメンタルデータを取得"""
    try:
        url = f"{API_BASE}/fins/summary"
        resp = requests.get(
            url,
            headers={"X-API-KEY": API_KEY},
            params={"code": code},
            timeout=10
        )
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}

        items = resp.json().get("data", [])
        if not items:
            return None

        # FY（通期）決算を優先、なければ最新を使用
        fy_items = [x for x in items if x.get("CurPerType") == "FY"]
        latest_fy  = fy_items[-1]  if fy_items  else None
        latest_any = items[-1]

        def _f(v):
            """文字列→float変換、空は None"""
            try:
                return float(v) if v not in ("", None) else None
            except Exception:
                return None

        # BPS/ROEはFYから優先取得
        eps = _f(latest_any.get("EPS"))
        bps = _f(latest_fy.get("BPS"))  if latest_fy else None
        roe = _f(latest_fy.get("ROE"))  if latest_fy else None

        # BPSがFYで空なら最新レコードからも試みる
        if bps is None:
            bps = _f(latest_any.get("BPS"))
        if roe is None:
            roe = _f(latest_any.get("ROE"))

        # 配当・予想
        f_div_ann = _f(latest_any.get("FDivAnn"))
        f_eps     = _f(latest_any.get("FEPS"))
        div_ann   = _f(latest_fy.get("DivAnn")) if latest_fy else None
        eq_ar     = _f(latest_any.get("EqAR"))

        # PER / PBR 計算
        per = round(current_price / eps, 2)  if (eps and eps > 0 and current_price > 0) else None
        pbr = round(current_price / bps, 2)  if (bps and bps > 0 and current_price > 0) else None

        # 配当利回り
        div_yield = None
        if f_div_ann and f_div_ann > 0 and current_price > 0:
            div_yield = round(f_div_ann / current_price * 100, 2)
        elif div_ann and div_ann > 0 and current_price > 0:
            div_yield = round(div_ann / current_price * 100, 2)

        # 業績（直近FY）
        sales = _f(latest_fy.get("Sales")) if latest_fy else None
        op    = _f(latest_fy.get("OP"))    if latest_fy else None
        np_   = _f(latest_fy.get("NP"))    if latest_fy else None
        cfo   = _f(latest_fy.get("CFO"))   if latest_fy else None

        def _fmt_oku(v):
            """円→億円表示"""
            if v is None:
                return None
            return round(v / 1e8, 1)

        return {
            "PER(倍)":      f"{per:.1f}" if per else "N/A",
            "PBR(倍)":      f"{pbr:.2f}" if pbr else "N/A",
            "ROE(%)":       f"{roe*100:.1f}" if roe else "N/A",
            "配当利回り(%)": f"{div_yield:.2f}" if div_yield else "N/A",
            "EPS(円)":      f"{eps:.2f}"  if eps else "N/A",
            "BPS(円)":      f"{bps:.2f}"  if bps else "N/A",
            # 業績
            "売上高(億円)":   _fmt_oku(sales),
            "営業利益(億円)": _fmt_oku(op),
            "純利益(億円)":   _fmt_oku(np_),
            "営業CF(億円)":   _fmt_oku(cfo),
            # 予想
            "予想EPS(円)":    f"{f_eps:.2f}"     if f_eps    else "N/A",
            "予想配当(円)":   f"{f_div_ann:.1f}" if f_div_ann else "N/A",
            "自己資本比率(%)":f"{eq_ar*100:.1f}" if eq_ar    else "N/A",
            # メタ
            "_per_raw": per,
            "_pbr_raw": pbr,
            "_disc_date": latest_any.get("DiscDate", ""),
            "_fy_date":   latest_fy.get("CurFYEn", "") if latest_fy else "",
        }
    except Exception as e:
        return {"error": str(e)}
'''

# 関数全体を正規表現で置換
pattern = r'def fetch_fundamental\(.*?(?=\ndef |\Z)'
if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, new_func + '\n\n', content, flags=re.DOTALL)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ fetch_fundamental 関数を更新しました")
else:
    print("❌ fetch_fundamental 関数が見つかりません")
    print("手動で確認してください")