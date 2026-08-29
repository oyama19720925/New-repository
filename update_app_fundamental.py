"""
app.pyにファンダメンタルデータ機能を統合するパッチスクリプト
"""
import re

APP_PATH = r'C:\stock_system\app.py'

# ========== 1. get_fundamental_data 関数の新バージョン ==========
NEW_FUNC = '''
def get_fundamental_data(code, current_price=None):
    """J-Quants /v2/fins/summary からファンダメンタルデータを取得・計算"""
    import requests

    API_KEY = '4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU'

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

        def to_float(val, default=None):
            try:
                return float(val) if val not in ('', None) else default
            except:
                return default

        eps    = to_float(latest.get('EPS'))
        feps   = to_float(latest.get('FEPS'))
        eq     = to_float(latest.get('Eq'))
        ta     = to_float(latest.get('TA'))
        np_    = to_float(latest.get('NP'))
        sales  = to_float(latest.get('Sales'))
        op     = to_float(latest.get('OP'))
        eq_ar  = to_float(latest.get('EqAR'))
        fdiv   = to_float(latest.get('FDivAnn'))
        fop    = to_float(latest.get('FOP'))
        fsales = to_float(latest.get('FSales'))
        cfo    = to_float(latest.get('CFO'))
        sh_out = to_float(latest.get('ShOutFY'))
        tr_sh  = to_float(latest.get('TrShFY'), 0)

        bps = to_float(latest.get('BPS'))
        if bps is None and eq and sh_out:
            net_sh = sh_out - (tr_sh or 0)
            if net_sh > 0:
                bps = eq / net_sh

        roe = to_float(latest.get('ROE'))
        if roe is None and np_ and eq and eq > 0:
            roe = (np_ / eq) * 100

        per = pbr = div_yield = None
        if current_price and current_price > 0:
            use_eps = feps if feps else eps
            if use_eps and use_eps > 0:
                per = round(current_price / use_eps, 2)
            if bps and bps > 0:
                pbr = round(current_price / bps, 2)
            if fdiv and fdiv > 0:
                div_yield = round((fdiv / current_price) * 100, 2)

        return {
            'PER': per, 'PBR': pbr,
            'ROE': round(roe, 2) if roe else None,
            'EPS': eps, 'FEPS': feps,
            'BPS': round(bps, 1) if bps else None,
            'DivYield': div_yield, 'FDivAnn': fdiv,
            'Sales': sales, 'OP': op, 'NP': np_,
            'FSales': fsales, 'FOP': fop,
            'Eq': eq, 'TA': ta, 'EqAR': eq_ar, 'CFO': cfo,
            'DiscDate': latest.get('DiscDate'),
            'DocType':  latest.get('DocType'),
            'CurPerType': latest.get('CurPerType'),
            'CurFYEn':  latest.get('CurFYEn'),
        }

    except Exception as e:
        st.warning(f'ファンダメンタルデータ取得エラー: {e}')
        return None

'''

# ========== 2. ファンダメンタル表示関数 ==========
DISPLAY_FUNC = '''
def display_fundamental(fd, code, name=""):
    """ファンダメンタルデータをStreamlitで表示"""
    if fd is None:
        st.warning("ファンダメンタルデータを取得できませんでした")
        return

    st.markdown("---")
    st.subheader(f"📊 ファンダメンタル分析　{name}（{code}）")

    # 開示情報ヘッダー
    col_info = st.columns(4)
    col_info[0].metric("開示日", fd.get('DiscDate', 'N/A'))
    col_info[1].metric("決算種別", fd.get('CurPerType', 'N/A'))
    col_info[2].metric("期末", fd.get('CurFYEn', 'N/A'))
    col_info[3].metric("書類種別", fd.get('DocType', 'N/A')[:20] if fd.get('DocType') else 'N/A')

    st.markdown("#### 💹 株価指標")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("PER（予想）", f"{fd['PER']}倍"    if fd['PER']      else "N/A")
    c2.metric("PBR",         f"{fd['PBR']}倍"    if fd['PBR']      else "N/A")
    c3.metric("ROE（1Q）",   f"{fd['ROE']}%"     if fd['ROE']      else "N/A")
    c4.metric("配当利回り",  f"{fd['DivYield']}%" if fd['DivYield'] else "N/A")
    c5.metric("年間配当",    f"{fd['FDivAnn']}円" if fd['FDivAnn']  else "N/A")

    st.markdown("#### 📈 1株指標")
    c6, c7, c8 = st.columns(3)
    c6.metric("EPS（実績）",   f"¥{fd['EPS']}"  if fd['EPS']  else "N/A")
    c7.metric("FEPS（通期予想）", f"¥{fd['FEPS']}" if fd['FEPS'] else "N/A")
    c8.metric("BPS",           f"¥{fd['BPS']}"  if fd['BPS']  else "N/A")

    st.markdown("#### 🏢 損益（直近四半期）")
    def fmt_oku(val):
        if val is None:
            return "N/A"
        if abs(val) >= 1e12:
            return f"{val/1e12:.2f}兆円"
        elif abs(val) >= 1e8:
            return f"{val/1e8:.0f}億円"
        else:
            return f"{val:,.0f}円"

    c9, c10, c11 = st.columns(3)
    c9.metric("売上高",   fmt_oku(fd['Sales']))
    c10.metric("営業利益", fmt_oku(fd['OP']))
    c11.metric("純利益",  fmt_oku(fd['NP']))

    c12, c13 = st.columns(2)
    c12.metric("売上高（通期予想）", fmt_oku(fd['FSales']))
    c13.metric("営業利益（通期予想）", fmt_oku(fd['FOP']))

    st.markdown("#### 🏦 財務状況")
    c14, c15, c16, c17 = st.columns(4)
    c14.metric("純資産",       fmt_oku(fd['Eq']))
    c15.metric("総資産",       fmt_oku(fd['TA']))
    c16.metric("自己資本比率", f"{fd['EqAR']*100:.1f}%" if fd['EqAR'] else "N/A")
    c17.metric("営業CF",       fmt_oku(fd['CFO']))

'''

# ========== 3. app.py 読み込み・更新 ==========
with open(APP_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# バックアップ
with open(APP_PATH + '.bak3', 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ バックアップ作成: app.py.bak3")

# --- get_fundamental_data 関数を置換または追加 ---
pattern_func = r'def get_fundamental_data\(.*?\n(?=\ndef |\nclass |\nst\.)'
if re.search(pattern_func, content, re.DOTALL):
    content = re.sub(pattern_func, NEW_FUNC.lstrip('\n'), content, flags=re.DOTALL)
    print("✅ get_fundamental_data 関数を置換しました")
else:
    # importブロックの直後に挿入
    insert_pos = content.find('\ndef ')
    if insert_pos == -1:
        insert_pos = content.find('\nst.')
    content = content[:insert_pos] + '\n' + NEW_FUNC + content[insert_pos:]
    print("✅ get_fundamental_data 関数を追加しました")

# --- display_fundamental 関数を置換または追加 ---
pattern_disp = r'def display_fundamental\(.*?\n(?=\ndef |\nclass |\nst\.)'
if re.search(pattern_disp, content, re.DOTALL):
    content = re.sub(pattern_disp, DISPLAY_FUNC.lstrip('\n'), content, flags=re.DOTALL)
    print("✅ display_fundamental 関数を置換しました")
else:
    insert_pos = content.find('\ndef ')
    content = content[:insert_pos] + '\n' + DISPLAY_FUNC + content[insert_pos:]
    print("✅ display_fundamental 関数を追加しました")

# ========== 4. バックテスト結果の後にファンダメンタル表示を追加 ==========
# バックテスト結果表示の後を探す
FUNDAMENTAL_CALL = '''
            # ===== ファンダメンタルデータ表示 =====
            if st.session_state.get('show_fundamental', True):
                with st.spinner('ファンダメンタルデータ取得中...'):
                    latest_price = float(filtered_df['Close'].iloc[-1]) if 'Close' in filtered_df.columns else None
                    fd = get_fundamental_data(selected_code, current_price=latest_price)
                    display_fundamental(fd, selected_code, selected_name)
'''

# バックテスト結果表示箇所を探す（st.dataframe や st.write でbacktest結果を表示している箇所の後）
backtest_markers = [
    'st.dataframe(backtest',
    'st.write(backtest',
    'バックテスト結果',
    'backtest_result',
    '# バックテスト',
]

inserted = False
for marker in backtest_markers:
    if marker in content:
        # markerの行末を探して次の行に挿入
        idx = content.find(marker)
        line_end = content.find('\n', idx)
        # 次のブロック（空行）を探す
        next_block = content.find('\n\n', line_end)
        if next_block != -1:
            content = content[:next_block] + '\n' + FUNDAMENTAL_CALL + content[next_block:]
            print(f"✅ ファンダメンタル表示コードを '{marker}' の後に追加しました")
            inserted = True
            break

if not inserted:
    print("⚠️  バックテスト結果表示箇所が見つかりませんでした")
    print("   → 手動で display_fundamental() の呼び出しを追加してください")

# ========== 5. セッション状態の初期化を確認・追加 ==========
SESSION_INIT = "    if 'show_fundamental' not in st.session_state:\n        st.session_state['show_fundamental'] = True\n"
if 'show_fundamental' not in content:
    # session_state初期化ブロックを探す
    ss_marker = "if 'selected_code' not in st.session_state"
    if ss_marker in content:
        idx = content.find(ss_marker)
        line_end = content.find('\n', idx)
        content = content[:line_end+1] + SESSION_INIT + content[line_end+1:]
        print("✅ show_fundamental セッション状態を追加しました")

# ========== 6. サイドバーにファンダメンタル表示チェックボックスを追加 ==========
SIDEBAR_CHECKBOX = '''
    # ファンダメンタル表示オプション
    st.session_state['show_fundamental'] = st.sidebar.checkbox(
        "📊 ファンダメンタル分析を表示",
        value=st.session_state.get('show_fundamental', True)
    )
'''
if 'show_fundamental' not in content or 'sidebar.checkbox' not in content:
    # サイドバー設定の末尾を探す
    sidebar_markers = ['st.sidebar.selectbox', 'st.sidebar.checkbox', 'st.sidebar.slider']
    for sm in sidebar_markers:
        if sm in content:
            idx = content.rfind(sm)  # 最後の出現
            line_end = content.find('\n', idx)
            next_line_end = content.find('\n', line_end + 1)
            content = content[:next_line_end+1] + SIDEBAR_CHECKBOX + content[next_line_end+1:]
            print(f"✅ サイドバーにファンダメンタルチェックボックスを追加しました")
            break

# ========== 7. 保存 ==========
with open(APP_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n🎉 app.py の更新が完了しました！")
print("以下のコマンドでアプリを起動してください：")
print("  cd C:\\stock_system && venv\\Scripts\\streamlit run app.py")