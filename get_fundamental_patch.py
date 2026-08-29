# このファイルはapp.pyのget_fundamental_data関数を確認・テスト用
# 実際はapp.pyに組み込む

def get_fundamental_data(code, current_price=None):
    import requests
    
    API_KEY = '4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU'
    
    # 4桁→5桁変換
    if len(str(code)) == 4:
        code_str = str(code) + '0'
    else:
        code_str = str(code)
    
    try:
        r = requests.get(
            'https://api.jquants.com/v2/fins/summary',
            headers={'X-API-KEY': API_KEY},
            params={'code': code_str},
            timeout=10
        )
        if r.status_code != 200:
            return None
        
        items = r.json().get('data', [])
        if not items:
            return None
        
        latest = items[-1]
        
        # 数値変換ヘルパー
        def to_float(val, default=None):
            try:
                return float(val) if val != '' and val is not None else default
            except:
                return default
        
        # 基本指標取得
        eps   = to_float(latest.get('EPS'))
        feps  = to_float(latest.get('FEPS'))   # 通期予想EPS
        eq    = to_float(latest.get('Eq'))
        ta    = to_float(latest.get('TA'))
        np_   = to_float(latest.get('NP'))
        sales = to_float(latest.get('Sales'))
        op    = to_float(latest.get('OP'))
        eq_ar = to_float(latest.get('EqAR'))
        fdiv  = to_float(latest.get('FDivAnn'))
        fop   = to_float(latest.get('FOP'))
        fsales= to_float(latest.get('FSales'))
        cfo   = to_float(latest.get('CFO'))
        
        # 株式数
        sh_out = to_float(latest.get('ShOutFY'))
        tr_sh  = to_float(latest.get('TrShFY'), 0)
        avg_sh = to_float(latest.get('AvgSh'))
        
        # BPS計算（APIに値がない場合）
        bps = to_float(latest.get('BPS'))
        if bps is None and eq and sh_out:
            net_sh = sh_out - (tr_sh or 0)
            if net_sh > 0:
                bps = eq / net_sh
        
        # ROE計算
        roe = to_float(latest.get('ROE'))
        if roe is None and np_ and eq and eq > 0:
            roe = (np_ / eq) * 100
        
        # PER・PBR計算（株価が必要）
        per = None
        pbr = None
        div_yield = None
        
        if current_price and current_price > 0:
            use_eps = feps if feps else eps   # 通期予想EPSを優先
            if use_eps and use_eps > 0:
                per = round(current_price / use_eps, 2)
            if bps and bps > 0:
                pbr = round(current_price / bps, 2)
            if fdiv and fdiv > 0:
                div_yield = round((fdiv / current_price) * 100, 2)
        
        return {
            # 株価指標
            'PER':       per,
            'PBR':       pbr,
            'ROE':       round(roe, 2) if roe else None,
            'EPS':       eps,
            'FEPS':      feps,
            'BPS':       round(bps, 1) if bps else None,
            'DivYield':  div_yield,
            'FDivAnn':   fdiv,
            # 損益
            'Sales':     sales,
            'OP':        op,
            'NP':        np_,
            'FSales':    fsales,
            'FOP':       fop,
            # 財務
            'Eq':        eq,
            'TA':        ta,
            'EqAR':      eq_ar,
            'CFO':       cfo,
            # 開示情報
            'DiscDate':  latest.get('DiscDate'),
            'DocType':   latest.get('DocType'),
            'CurPerType':latest.get('CurPerType'),
            'CurFYEn':   latest.get('CurFYEn'),
        }
    
    except Exception as e:
        print(f'ファンダメンタルデータ取得エラー: {e}')
        return None


# ===== テスト実行 =====
if __name__ == '__main__':
    result = get_fundamental_data('7203', current_price=3000)
    if result:
        print('=== ファンダメンタルデータ ===')
        for k, v in result.items():
            print(f'  {k}: {v}')