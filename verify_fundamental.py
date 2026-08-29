# verify_fundamental.py
import requests

API_KEY  = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
API_BASE = "https://api.jquants.com/v2"

def fetch_fundamental(code, current_price=0):
    url   = f"{API_BASE}/fins/summary"
    resp  = requests.get(url, headers={"X-API-KEY": API_KEY},
                         params={"code": code}, timeout=10)
    items = resp.json().get("data", [])
    if not items:
        return None

    fy_items   = [x for x in items if x.get("CurPerType") == "FY"]
    latest_fy  = fy_items[-1]  if fy_items  else None
    latest_any = items[-1]

    def _f(v):
        try:   return float(v) if v not in ("", None) else None
        except: return None

    eps = _f(latest_any.get("EPS"))
    bps = _f(latest_fy.get("BPS")) if latest_fy else _f(latest_any.get("BPS"))
    roe = _f(latest_fy.get("ROE")) if latest_fy else _f(latest_any.get("ROE"))
    f_div_ann = _f(latest_any.get("FDivAnn"))

    per = round(current_price / eps, 2) if (eps and eps > 0 and current_price > 0) else None
    pbr = round(current_price / bps, 2) if (bps and bps > 0 and current_price > 0) else None
    div_yield = round(f_div_ann / current_price * 100, 2) if (f_div_ann and current_price > 0) else None

    return {
        "PER": per, "PBR": pbr,
        "ROE": f"{roe*100:.1f}%" if roe else "N/A",
        "EPS": eps, "BPS": bps,
        "配当利回り": f"{div_yield:.2f}%" if div_yield else "N/A",
        "FY決算期": latest_fy.get("CurFYEn") if latest_fy else "N/A",
        "最新開示": latest_any.get("DiscDate"),
    }

# トヨタ(7203) 株価約3000円で試算
result = fetch_fundamental("72030", current_price=3000)
for k, v in result.items():
    print(f"{k}: {v}")