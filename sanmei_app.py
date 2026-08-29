import streamlit as st
import datetime
import calendar
import math
import io
import textwrap
import matplotlib.pyplot as plt
import japanize_matplotlib
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Set

# ==========================================
# 0. 外部ライブラリ安全インポート
# ==========================================
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# ==========================================
# 1. ページ基本設定 & カスタムCSS & 根本対策レンダラー
# ==========================================
st.set_page_config(
    page_title="SANMEI TRADING & TALENT ANALYTICS",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

def render_html(html_content: str):
    """HTML内の全行頭インデント・余分な改行を完全除去してMarkdownコードブロック化を根絶する"""
    clean_html = "".join([line.strip() for line in html_content.splitlines()])
    st.markdown(clean_html, unsafe_allow_html=True)

CUSTOM_CSS = """
<style>
.stApp {
    background: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #0f172a 60%, #020617 100%);
    color: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
}
.analytics-header {
    text-align: center;
    padding: 10px 0 16px 0;
}
.analytics-title {
    font-size: 2.3rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, #c084fc 20%, #38bdf8 60%, #ffffff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}
.analytics-sub {
    color: #38bdf8;
    font-size: 0.95rem;
    font-weight: 600;
}
div.stButton > button {
    width: 100% !important;
    background-color: #1e293b !important;
    color: #f8fafc !important;
    border: 2px solid #475569 !important;
    border-radius: 10px !important;
    padding: 10px 4px !important;
    font-size: 0.88rem !important;
    font-weight: 800 !important;
    transition: all 0.2s ease !important;
}
div.stButton > button:hover {
    background-color: #334155 !important;
    border-color: #c084fc !important;
    color: #ffffff !important;
}
div.stButton > button[kind="primary"] {
    background-color: #6366f1 !important;
    border-color: #a855f7 !important;
    color: #ffffff !important;
    box-shadow: 0 0 18px rgba(168, 85, 247, 0.7) !important;
}
.card-modern {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 14px;
    padding: 20px;
    backdrop-filter: blur(8px);
    margin-bottom: 16px;
}
.card-highlight {
    border: 1px solid #38bdf8;
    background: rgba(56, 189, 248, 0.08);
}
.card-spiritual {
    border: 1px solid #c084fc;
    background: rgba(192, 132, 252, 0.08);
}
.card-energy {
    border: 1px solid #818cf8;
    background: rgba(99, 102, 241, 0.09);
}
.card-warning {
    border: 1px solid rgba(245, 158, 11, 0.6);
    background: rgba(245, 158, 11, 0.06);
}
.card-success {
    border: 1px solid rgba(16, 185, 129, 0.6);
    background: rgba(16, 185, 129, 0.06);
}
.card-danger {
    border: 1px solid rgba(239, 68, 68, 0.6);
    background: rgba(239, 68, 68, 0.08);
}
.metric-val {
    font-size: 3.2rem;
    font-weight: 800;
    line-height: 1;
    color: #38bdf8;
    letter-spacing: -0.03em;
}
.metric-spiritual {
    font-size: 3.2rem;
    font-weight: 800;
    line-height: 1;
    color: #c084fc;
    letter-spacing: -0.03em;
}
.metric-energy {
    font-size: 3.2rem;
    font-weight: 800;
    line-height: 1;
    color: #a5b4fc;
    letter-spacing: -0.03em;
}
.energy-rank-badge {
    display: inline-block;
    background: rgba(129, 140, 248, 0.25);
    color: #c7d2fe;
    border: 1px solid #818cf8;
    padding: 3px 10px;
    border-radius: 6px;
    font-weight: 800;
    font-size: 0.85rem;
    margin-top: 4px;
}
.spiritual-badge {
    display: inline-block;
    background: rgba(192, 132, 252, 0.25);
    color: #f3e8ff;
    border: 1px solid #c084fc;
    padding: 3px 10px;
    border-radius: 6px;
    font-weight: 800;
    font-size: 0.85rem;
    margin-top: 4px;
}
.calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 8px;
    margin-top: 12px;
}
.cal-header {
    text-align: center;
    font-weight: 800;
    font-size: 0.85rem;
    color: #94a3b8;
    padding: 4px 0;
}
.cal-day-box {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px;
    min-height: 95px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.cal-day-entry {
    border-color: #10b981 !important;
    background: rgba(16, 185, 129, 0.12) !important;
}
.cal-day-caution {
    border-color: #ef4444 !important;
    background: rgba(239, 68, 68, 0.12) !important;
}
.cal-day-lunar-boost {
    border-color: #c084fc !important;
    background: rgba(192, 132, 252, 0.18) !important;
    box-shadow: 0 0 10px rgba(192, 132, 252, 0.4);
}
.cal-date-num {
    font-weight: 800;
    font-size: 0.95rem;
    color: #ffffff;
}
.cal-kanshi {
    font-size: 0.72rem;
    color: #94a3b8;
}
.cal-tag {
    font-size: 0.68rem;
    font-weight: 800;
    padding: 2px 4px;
    border-radius: 4px;
    text-align: center;
    margin-top: 2px;
}
.cal-tag-entry {
    background: #059669;
    color: #ffffff;
}
.cal-tag-caution {
    background: #dc2626;
    color: #ffffff;
}
.cal-tag-neutral {
    background: #334155;
    color: #cbd5e1;
}
.cal-tag-lunar {
    background: #7e22ce;
    color: #f3e8ff;
}
.timeline-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
    margin: 16px 0;
}
.taiun-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 14px;
    position: relative;
}
.taiun-card-active {
    border: 2px solid #38bdf8 !important;
    background: rgba(56, 189, 248, 0.12) !important;
    box-shadow: 0 0 14px rgba(56, 189, 248, 0.4);
}
.taiun-card-tenchu {
    border: 2px solid #fbbf24 !important;
    background: rgba(251, 191, 36, 0.08) !important;
}
.taiun-age {
    font-size: 1.15rem;
    font-weight: 800;
    color: #ffffff;
}
.taiun-kanshi {
    font-size: 0.9rem;
    color: #94a3b8;
    margin-bottom: 6px;
}
.taiun-star {
    display: inline-block;
    font-size: 0.8rem;
    font-weight: 700;
    color: #93c5fd;
    background: rgba(59, 130, 246, 0.25);
    padding: 2px 8px;
    border-radius: 4px;
    margin-bottom: 6px;
}
.taiun-badge-active {
    position: absolute;
    top: 10px;
    right: 10px;
    background: #0284c7;
    color: #ffffff;
    font-size: 0.65rem;
    font-weight: 800;
    padding: 2px 6px;
    border-radius: 10px;
}
.taiun-badge-tenchu {
    position: absolute;
    top: 10px;
    right: 10px;
    background: #d97706;
    color: #ffffff;
    font-size: 0.65rem;
    font-weight: 800;
    padding: 2px 6px;
    border-radius: 10px;
}
.asset-compare-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 12px;
    margin: 14px 0;
}
.asset-box {
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 14px;
}
.asset-box-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 6px;
    display: flex;
    justify-content: space-between;
}
.asset-box-pros {
    color: #34d399;
    font-size: 0.8rem;
    line-height: 1.5;
    margin-bottom: 4px;
}
.asset-box-cons {
    color: #f87171;
    font-size: 0.8rem;
    line-height: 1.5;
}
.talent-tile-modern {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 18px;
    height: 100%;
}
.talent-tag {
    font-size: 0.75rem;
    font-weight: 700;
    color: #94a3b8;
    text-transform: uppercase;
}
.talent-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #ffffff;
    margin: 4px 0 6px 0;
}
.star-tag {
    display: inline-block;
    font-size: 0.75rem;
    color: #93c5fd;
    background: rgba(59, 130, 246, 0.2);
    padding: 2px 8px;
    border-radius: 4px;
    margin-bottom: 10px;
}
.hearts-display {
    font-size: 1.8rem;
    color: #f43f5e;
    letter-spacing: 2px;
}
.ratio-pill-clean {
    display: inline-flex;
    align-items: center;
    background: rgba(244, 63, 94, 0.12);
    border: 1px solid rgba(244, 63, 94, 0.4);
    color: #fda4af;
    font-weight: 700;
    font-size: 0.85rem;
    padding: 5px 14px;
    border-radius: 20px;
    margin-top: 10px;
}
</style>
"""
render_html(CUSTOM_CSS)

# ==========================================
# 2. 算命学ロジック & 統計・偏差値定義
# ==========================================
KAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
SHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
KANSHI_60 = [KAN[i % 10] + SHI[i % 12] for i in range(60)]

ZOKAN_MAP = {
    "子": "癸", "丑": "己", "寅": "甲", "卯": "乙",
    "辰": "戊", "巳": "丙", "午": "丁", "未": "己",
    "申": "庚", "酉": "辛", "戌": "戊", "亥": "壬"
}

TENCHUSATSU_MAP = {
    0: ("戌亥天中殺", ["戌", "亥"], "精神探求・内省型"),
    1: ("申酉天中殺", ["申", "酉"], "前進力・社会開拓型"),
    2: ("午未天中殺", ["午", "未"], "知性・基盤集約型"),
    3: ("辰巳天中殺", ["辰", "巳"], "現実推進・スケール型"),
    4: ("寅卯天中殺", ["寅", "卯"], "エネルギッシュ・拠点構築型"),
    5: ("子丑天中殺", ["子", "丑"], "独立独歩・初代開拓型")
}

KAN_GOU_PAIRS = [("甲", "己"), ("乙", "庚"), ("丙", "辛"), ("丁", "壬"), ("戊", "癸")]
SHI_GOU_PAIRS = [("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"), ("巳", "申"), ("午", "未")]
SAN_GOU_GROUPS = [
    {"申", "子", "辰"},
    {"巳", "酉", "丑"},
    {"寅", "午", "戌"},
    {"亥", "卯", "未"}
]

SPIRIT_STARS = {"鳳閣星", "調舒星", "龍高星", "玉堂星"}
REAL_STARS = {"貫索星", "石門星", "禄存星", "司禄星", "車騎星", "牽牛星"}
INTUITION_STARS = {"調舒星", "龍高星", "天胡星", "天極星"}

SHUGOSHIN_MAP = {
    "甲": ("丙", "癸", "木", "東・南東", "フォレストグリーン・エメラルド", "太陽の光と清らかな水が巨木を大成させる。ひらめきと知性を磨く環境が運気を開花。"),
    "乙": ("丙", "癸", "木", "東・南", "ライムグリーン・ミント", "暖かな日差しと適度な潤いが草花を美しく咲かせる。柔軟な調和と社交性が武器。"),
    "丙": ("壬", "甲", "火", "南", "クリムゾンレッド・ゴールド", "大河の水面に反射する太陽が最も輝く。スケールの大きな市場でのびのび勝負。"),
    "丁": ("甲", "庚", "火", "南・南西", "パープル・ローズピンク", "良質な木材とそれを削る刃物が灯火を燃え上がらせる。鋭敏な分析と集中力が鍵。"),
    "戊": ("丙", "甲", "土", "中央・南西", "イエロー・テラコッタ", "太陽の温もりと木々の根が広大な山岳を緑豊かにする。重厚な構えと揺るがぬ自信。"),
    "己": ("丙", "癸", "土", "中央・北東", "キャメルベージュ・オーカー", "太陽と雨露が田園を肥沃にする。着実なデータ蓄積とプロセス管理で富を形成。"),
    "庚": ("丁", "甲", "金", "西・北西", "ホワイト・プラチナシルバー", "炉の火と薪が鋼鉄を名刀へと鍛え上げる。試練と損切り訓練が勝負師としての格を上げる。"),
    "辛": ("壬", "丙", "金", "西", "クリアシルバー・シャンパンゴールド", "清らかな水で洗われ太陽に照らされた宝石が輝く。独自の直感と洗練された選別眼。"),
    "壬": ("戊", "丙", "水", "北・北西", "ディープネイビー・コバルトブルー", "頑丈な堤防と太陽が大河の氾濫を防ぎ豊かさをもたらす。ダイナミックな資金循環。"),
    "癸": ("辛", "丙", "水", "北", "シアンブルー・アクア", "水源となる鉱脈と太陽が雨露を絶え間なく湧き出させる。深い探求心と情報収集力。")
}

GOGYO_SECTOR_MAP = {
    "木（自立・成長）": {
        "theme": "先端半導体・情報通信・AIソフトウェア・農林バイオ",
        "desc": "上に向かって真っ直ぐ伸びる成長株・イノベーションテック銘柄。"
    },
    "火（表現・拡散）": {
        "theme": "メディア・エンタメ・ゲーム・電力ガス・広告",
        "desc": "世間の注目を集め、華やかに話題化するモメンタム・テーマ株銘柄。"
    },
    "土（蓄積・引力）": {
        "theme": "総合商社・不動産・建設・倉庫運輸・メガバンク",
        "desc": "実物資産と強固な資本基盤を持ち、インカムゲインを生み続けるバリュー株。"
    },
    "金（決断・攻撃）": {
        "theme": "自動車・重工防衛・鉄鋼非鉄・精密機械・鉱業",
        "desc": "グローバルな景気循環や為替・コモディティ価格に連動する大型シクリカル株。"
    },
    "水（知性・流動）": {
        "theme": "医薬品・ヘルスケア・海運・水産・クオンツ金融",
        "desc": "ディフェンシブな需要と世界的な物流網・知財を握るグローバル銘柄。"
    }
}

STAR_MAP = {
    "貫索星": {
        "modern": "強固な推進軸（自立・意志）",
        "desc": "自ら設定した基準を着実に達成する高い一貫性と自己完結力。",
        "fit_jobs": "個人事業主、エンジニア、職人、独立系コンサルタント、専門研究職",
        "unfit_jobs": "上意下達が激しい組織の兵隊役、方針が頻繁に変わるベンチャー営業",
        "invest_type": "長期積立・バリュー株投資（コア・サテライト戦略）",
        "invest_reason": "一度決めた銘柄を愚直にホールドできる握力があり、ノイズに惑わされない長期現物投資で最大のパフォーマンスを発揮します。",
        "bias_trait": "頑固ホールド傾向。損切りルールを機械的に自動化することが資産防衛の鍵。",
        "affirmation": "「私は自らの基準を信頼し、市場の雑音に惑わされず静寂の中で最適な決断を下す。」"
    },
    "石門星": {
        "modern": "合意形成・統率力（連携）",
        "desc": "多様なステークホルダーを結集して共通目標へ導くネットワーク力。",
        "fit_jobs": "プロジェクトマネージャー、経営者、人事責任者、政治・渉外、コミュニティ運営",
        "unfit_jobs": "孤独な単独作業、裁量のないルーチンワーク、個人完結型の作業",
        "invest_type": "インデックス投資 ＋ クラウドファンディング・共同投資",
        "invest_reason": "市場全体（集合体）の成長に乗るインデックスや、人脈・ネットワークを活かした共同投資・事業投資に適性があります。",
        "bias_trait": "周囲の噂や他人の意見に流されやすい。独自の定量フィルターによる検証が必須。",
        "affirmation": "「私は他者の波長を調和させつつ、自らの軸を保ち客観的な数字に従って行動する。」"
    },
    "鳳閣星": {
        "modern": "客観分析・伝達力（広報）",
        "desc": "バイアスのない視点で事実を把握し、要点を分かりやすく周囲に伝える能力。",
        "fit_jobs": "アナリスト、ジャーナリスト、マーケター、広報、飲食・観光・エンタメ業",
        "unfit_jobs": "過度に切迫したノルマ営業、閉鎖的で感情労働の多い環境",
        "invest_type": "高配当株投資 ＋ 中期トレンドフォロー",
        "invest_reason": "市場を冷静かつ客観的に観察できるため、無理なレバレッジを避け、着実にインカムゲイン（配当）を得ながら波に乗るスタイルが最適です。",
        "bias_trait": "のんびり構えすぎてエントリーが遅れる傾向。アラート設定によるトリガー発注が有効。",
        "affirmation": "「私はあるがままの相場の呼吸を観察し、自然なタイミングで優雅に波に乗る。」"
    },
    "調舒星": {
        "modern": "鋭敏な洞察・企画力（感性）",
        "desc": "妥協のない美意識と細部へのこだわりで、独自性の高い付加価値を生み出す力。",
        "fit_jobs": "クリエイティブディレクター、デザイナー、作家、特化型専門職、システムアーキテクト",
        "unfit_jobs": "大所帯での画一的な集団行動、感情を押し殺す接客・コールセンター",
        "invest_type": "グロース成長株 ＋ 個別集中投資",
        "invest_reason": "他人が見落とす歪みや未来のメガトレンドを直感的に見抜くため、尖ったニッチ成長株の選別投資で大化けを狙えます。",
        "bias_trait": "完璧主義と反発心から逆張りで熱くなりやすい。ポジションサイズを小さく保つことが肝要。",
        "affirmation": "「私の研ぎ澄まされた直感は真実を見抜く。感情の波を手放し、純粋な閃きに従う。」"
    },
    "禄存星": {
        "modern": "資源配分・求心力（魅力）",
        "desc": "人・資本・情報に対する強い求心力を持ち、全体の活性化を図る才能。",
        "fit_jobs": "投資家、事業開発、総合営業、金融・不動産ブローカー、エンタメプロデューサー",
        "unfit_jobs": "細かな帳簿付けのみの事務、予算権限のない固定ポジション",
        "invest_type": "中短期スイングトレード ＋ 実物資産（不動産・コモディティ）",
        "invest_reason": "資金を滞留させずダイナミックに循環させる回転力があるため、市場のうねりを取っていくスイングや現物資産の運用に強みがあります。",
        "bias_trait": "回転売買の回転数が上がりすぎて手数料負けしやすい。トレード回数の上限設定が有効。",
        "affirmation": "「富は循環するエネルギーである。私は愛と感謝をもって資本を正しく動かし、繁栄を受け取る。」"
    },
    "司禄星": {
        "modern": "着実な資産蓄積（堅実）",
        "desc": "日々のプロセスとデータを着実に積み重ね、長期的な安全性を担保する力。",
        "fit_jobs": "財務・経理、リスク管理、公務員、データアナリスト、資産運用アドバイザー",
        "unfit_jobs": "ハイリスクな一発勝負、不透明な資金繰りを強いられる環境",
        "invest_type": "高配当・連続増配株 ＋ 債券・定期積立（ドルコスト平均法）",
        "invest_reason": "複利の効果を最も信じて待てる資質です。暴落時でも淡々と買い増し、配当再投資で雪だるま式に資産を築く王道投資が最適です。",
        "bias_trait": "損失回避バイアスが強く機会損失を生みやすい。少額のサテライト枠でリスク許容度を訓練。",
        "affirmation": "「一歩ずつの着実な積み重ねが揺るぎない基盤を創る。私は複利の力を信じ、焦りを手放す。」"
    },
    "車騎星": {
        "modern": "即応・突破力（機動力）",
        "desc": "課題発生時の初動が極めて早く、現場で最短距離の意思決定をやり切る力。",
        "fit_jobs": "現場指揮官、救急・防災、フィールドセールス、新規事業立ち上げ、アスリート",
        "unfit_jobs": "承認プロセスが長い大企業、机上の空論ばかりで進まない会議",
        "invest_type": "デイトレード ＋ モメンタム短期売買",
        "invest_reason": "迅速な意思決定と損切り判断ができるため、資金効率を最大化するデイトレや短期ブレイクアウト手法で強みを発揮します。",
        "bias_trait": "リベンジトレード（負けた直後の無理な突撃）に注意。連敗時は即座にPCを閉じるルールが必須。",
        "affirmation": "「私の行動は迅速でありながら冷静である。損切りを味方につけ、明鏡止水の心で刃を振るう。」"
    },
    "牽牛星": {
        "modern": "組織責任・統制力（規律）",
        "desc": "役割や職責を厳格に全うし、組織のブランドや社会的信用を維持する姿勢。",
        "fit_jobs": "大企業エグゼクティブ、官僚、法務・コンプライアンス、監査役、ブランドマネージャー",
        "unfit_jobs": "コンプライアンスが緩いグレーな事業、無秩序な環境",
        "invest_type": "大型優良株（メガキャップ） ＋ 国債・安全資産",
        "invest_reason": "確固たる信用と格付けを重視するため、倒産リスクが極めて低いグローバルメガキャップや優良インフラ株への手堅い投資が向いています。",
        "bias_trait": "プライドからミスを認めるのが遅れやすい。客観的なトレード日誌による週次振り返りが武器。",
        "affirmation": "「私は自らに課した規律を尊び、誇り高く、かつ謙虚に市場の真実に従う。」"
    },
    "龍高星": {
        "modern": "構造改革・イノベーション（改革）",
        "desc": "既成概念に捉われず、新しい技術を取り入れて枠組みを刷新する開拓力。",
        "fit_jobs": "海外事業、先端テック開発、経営改革コンサルタント、冒険的スタートアップ、ジャーナリスト",
        "unfit_jobs": "前例踏襲しか認められない保守的組織、固定された定型業務",
        "invest_type": "暗号資産（仮想通貨） ＋ 先端ディープテック株 ＋ FX",
        "invest_reason": "未知の市場やボラティリティを恐れず、パラダイムシフトの波に乗るのが得意なため、新興アセットやマクロトレンドを捉えた為替取引に適性があります。",
        "bias_trait": "新しい対象へ目移りしやすい。運用コア資産と実験的サテライト資産を厳格に分離。",
        "affirmation": "「私は変化を歓迎し、未知の領域に潜むチャンスを直観で見抜き、軽やかに跳躍する。」"
    },
    "玉堂星": {
        "modern": "論理構築・知性（研究）",
        "desc": "体系的な知識体系をインプットし、再現性のある理論基盤を構築する力。",
        "fit_jobs": "大学教授、研究開発、教育・指導者、シンクタンク研究員、法曹関係者",
        "unfit_jobs": "科学的根拠のない感覚任せの仕事、ノリと勢いだけの営業",
        "invest_type": "ファンダメンタルズ徹底分析投資 ＋ クオンツ・統計モデル投資",
        "invest_reason": "決算書、財務諸表、統計バックテストを論理的に読み解く知性があるため、数字と裏付けに基づいた合理的投資で高い勝率を維持できます。",
        "bias_trait": "分析麻痺（Analysis Paralysis）。完璧な条件が揃うのを待ちすぎて絶好の売買機を逃す点に留意。",
        "affirmation": "「知恵は私の羅針盤である。私は理論に魂を吹き込み、確信をもって勝負に臨む。」"
    }
}

def get_partner_role(star_name: str) -> str:
    role_mapping = {
        "貫索星": "【独立・推進役】独自の明確な基準を維持し、ブレずに目標を完遂する実務推進と自立行動。",
        "石門星": "【連携・渉外役】チーム全体の合意形成、外部ステークホルダーとの交渉・ネットワーク拡大。",
        "鳳閣星": "【伝達・観察役】客観的な市場分析と情報の可視化、組織の雰囲気を和ませる情報発信。",
        "調舒星": "【企画・洞察役】独自の感性と鋭い洞察力を活かした企画立案、細部のクオリティ管理。",
        "禄存星": "【資本・求心役】人・資本・情報のダイナミックな循環と調達、市場開拓・営業主導。",
        "司禄星": "【財務・蓄積役】着実なリスク管理、日々の資産・データ蓄積、バックオフィスの堅実運用。",
        "車騎星": "【機動・決断役】現場での即時判断と最短距離の行動、課題発生時の突破とスピーディな実行。",
        "牽牛星": "【統制・規律役】組織のブランドと社会的信用の維持、ルール設計とコンプライアンス管理。",
        "龍高星": "【改革・開拓役】新技術・新規事業の開拓、既成概念を打破するイノベーションと環境適応。",
        "玉堂星": "【戦略・研究役】体系的な理論構築とバックテスト検証、論理的裏付けに基づく戦略策定。"
    }
    return role_mapping.get(star_name, "【戦略推進役】強みを活かした役割分担の主導。")

def get_star(nikkan: str, target: str) -> str:
    n_idx, t_idx = KAN.index(nikkan), KAN.index(target)
    diff = (t_idx // 2 - n_idx // 2) % 5
    same = (n_idx % 2 == t_idx % 2)
    mapping = {
        (0, True): "貫索星", (0, False): "石門星",
        (1, True): "鳳閣星", (1, False): "調舒星",
        (2, True): "禄存星", (2, False): "司禄星",
        (3, True): "車騎星", (3, False): "牽牛星",
        (4, True): "龍高星", (4, False): "玉堂星",
    }
    return mapping.get((diff, same), "貫索星")

def get_kanshi_indices(dt: datetime.date) -> Tuple[int, int, int]:
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3
    jd = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    day_idx = (jd + 50) % 60

    is_after_risshun = (dt.month > 2) or (dt.month == 2 and dt.day >= 4)
    cal_year = dt.year if is_after_risshun else dt.year - 1
    year_idx = (cal_year - 4) % 60

    setsuri = [6, 4, 6, 5, 6, 6, 7, 8, 8, 8, 7, 7]
    if dt.day >= setsuri[dt.month - 1]:
        m_idx_raw = dt.month
    else:
        m_idx_raw = dt.month - 1
        if m_idx_raw == 0:
            m_idx_raw = 12

    month_branch = (m_idx_raw + 1) % 12
    year_stem = year_idx % 10
    month_stem = ((year_stem % 5) * 2 + 2 + (m_idx_raw - 2)) % 10
    month_idx = (6 * month_stem - 5 * month_branch) % 60

    return year_idx, month_idx, day_idx

def get_yosen_stars(year_idx: int, month_idx: int, day_idx: int) -> Dict[str, str]:
    nikkan = KANSHI_60[day_idx][0]
    y_kan = KANSHI_60[year_idx][0]
    y_shi = KANSHI_60[year_idx][1]
    m_kan = KANSHI_60[month_idx][0]
    m_shi = KANSHI_60[month_idx][1]
    d_shi = KANSHI_60[day_idx][1]
    
    return {
        "core": get_star(nikkan, ZOKAN_MAP.get(m_shi, "戊")),
        "north": get_star(nikkan, y_kan),
        "east": get_star(nikkan, ZOKAN_MAP.get(d_shi, "癸")),
        "south": get_star(nikkan, m_kan),
        "west": get_star(nikkan, ZOKAN_MAP.get(y_shi, "丙"))
    }

def get_tenchusatsu_info(day_kanshi_idx: int) -> Tuple[str, List[str], str]:
    group_idx = (day_kanshi_idx // 10) % 6
    return TENCHUSATSU_MAP[group_idx]

def get_moon_phase(dt: datetime.date) -> Tuple[str, str, float, str]:
    ref_date = datetime.date(2024, 1, 11)
    diff_days = (dt - ref_date).days
    synodic_cycle = 29.53058867
    phase_age = (diff_days % synodic_cycle)
    
    if phase_age < 1.5 or phase_age > 28.0:
        phase_name = "🌑 新月（ニュームーン）"
        phase_type = "new"
        desc = "【種まき・初動】集合意識のリセット。新たなトレンド発生の契機となる仕込み期。"
    elif 13.5 <= phase_age <= 16.0:
        phase_name = "🌕 満月（フルムーン）"
        phase_type = "full"
        desc = "【達成・過熱・リバーサル】集合意識の熱狂がピークに達する転換点。利確優先。"
    elif 1.5 <= phase_age < 13.5:
        phase_name = "🌓 上弦の月（満ちる月）"
        phase_type = "waxing"
        desc = "【エネルギー拡大】流動性が高まり、順張りモメンタムが走りやすい上昇サイクル。"
    else:
        phase_name = "🌗 下弦の月（欠ける月）"
        phase_type = "waning"
        desc = "【調整・手仕舞い・浄化】過熱感が沈静化。ポジション整理や無駄の削ぎ落とし期。"
        
    return phase_name, phase_type, round(phase_age, 1), desc

def calculate_intuition_index(stars: Dict[str, str], day_kanshi: str) -> Tuple[int, str, str]:
    star_list = [stars["core"], stars["north"], stars["east"], stars["south"], stars["west"]]
    intuition_count = sum(1 for s in star_list if s in INTUITION_STARS)
    
    base_score = 60 + intuition_count * 10
    
    if base_score >= 85:
        level = "超感覚・インスピレーション型（霊感直感マスター）"
        strategy = "チャートの『違和感』や板の気配に対する第一感を最重視。テクニカル指標の遅行に騙されない直感エントリーが最大の武器。"
    elif base_score >= 70:
        level = "直感・論理ハイブリッド型（バランス直感）"
        strategy = "定量分析で候補を絞り、最後のエントリートリガーは直感（呼吸）で引くアプローチが最適。"
    else:
        level = "徹底論理・クオンツ型（現実客観マスター）"
        strategy = "直感を過信せず、バックテストされたルールと統計数値のみに従うシステムトレードで最大の勝率を発揮。"
        
    return base_score, level, strategy

def calculate_mind_consistency(stars: Dict[str, str]) -> Tuple[int, str, str]:
    star_list = [stars["core"], stars["north"], stars["east"], stars["south"], stars["west"]]
    spirit_count = sum(1 for s in star_list if s in SPIRIT_STARS)
    real_count = sum(1 for s in star_list if s in REAL_STARS)
    
    ratio = max(spirit_count, real_count) / 5.0
    score = int(ratio * 100)
    
    if spirit_count >= 4:
        label = "純星（精神探求型・理論統一）"
        desc = "判断基準が理念・美意識・論理で純化されており、迷いなく長期ビジョンを貫ける強みがあります。"
    elif real_count >= 4:
        label = "純星（現実推進型・実利統一）"
        desc = "判断基準が数字・実益・結果に直結しており、現場で最短距離の意思決定をやり切る強みがあります。"
    else:
        label = "混星（精神・現実 ハイブリッド型）"
        desc = "理想と現実のバランス感覚に優れますが、局面によって判断基準が揺れやすいため、事前のルール化が不可欠です。"
        
    return score, label, desc

# 偏差値・統計分布対応エネルギー算出エンジン
def calculate_energy_metrics(day_idx: int, month_idx: int, year_idx: int) -> Tuple[int, str, float, float, str, Dict[str, int]]:
    base_val = 150 + ((day_idx * 17 + month_idx * 11 + year_idx * 7) % 130)
    
    if base_val >= 230:
        energy_class = "最身強（自力突破・スケール型）"
    elif base_val >= 190:
        energy_class = "身強（リーダー・現実推進型）"
    elif base_val >= 155:
        energy_class = "身中（柔軟適応・バランス型）"
    else:
        energy_class = "身弱（知性・スペシャリスト型）"
        
    z = (base_val - 185) / 32.0
    t_score = round(50.0 + 10.0 * z, 1)
    top_pct = round(max(0.8, min(99.2, 100.0 * (1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2)))))), 1)
    
    if top_pct <= 20.0:
        one_in_n = max(2, round(100.0 / top_pct))
        rank_label = f"全体の上位 {top_pct}%（偏差値 {t_score} / 約 {one_in_n}人に1人の高エネルギー）"
    elif top_pct <= 80.0:
        rank_label = f"全体の中央層（上位 {top_pct}% / 偏差値 {t_score} / 平均分布ゾーン）"
    else:
        one_in_n = max(2, round(100.0 / (100.0 - top_pct)))
        rank_label = f"堅実・知性特化層（上位 {top_pct}% / 偏差値 {t_score} / 約 {one_in_n}人に1人）"
        
    gogyo_dist = {
        "木（自立・成長）": 20 + ((day_idx * 3) % 40),
        "火（表現・拡散）": 15 + ((month_idx * 5) % 35),
        "土（蓄積・引力）": 25 + ((year_idx * 2) % 45),
        "金（決断・攻撃）": 15 + ((day_idx + year_idx) % 35),
        "水（知性・流動）": 20 + ((base_val * 3) % 40)
    }
    return base_val, energy_class, top_pct, t_score, rank_label, gogyo_dist

def calculate_year_phase(current_year: int, p1_indices: Tuple[int, int, int]) -> Tuple[str, str, str]:
    curr_cal_year = current_year
    curr_year_idx = (curr_cal_year - 4) % 60
    curr_kanshi = KANSHI_60[curr_year_idx]
    curr_branch = curr_kanshi[1]
    
    d_branch = KANSHI_60[p1_indices[2]][1]
    
    is_shigo = (curr_branch, d_branch) in SHI_GOU_PAIRS or (d_branch, curr_branch) in SHI_GOU_PAIRS
    is_sango = any({curr_branch, d_branch}.issubset(g) for g in SAN_GOU_GROUPS)
    diff_branch = abs(SHI.index(curr_branch) - SHI.index(d_branch))
    is_taichu = (diff_branch == 6)
    
    if is_shigo or is_sango:
        phase_label = "【合法年：拡大・推進期】"
        phase_action = "新しい事業投資やポジション構築、ネットワーク拡大に追い風が吹く前進期です。"
    elif is_taichu:
        phase_label = "【散法年：天剋・破壊と再生期】"
        phase_action = "既存の歪みや無駄を整理・損切りし、内部体制のスリム化と再構築に徹すべき調整期です。"
    else:
        phase_label = "【平常年：着実蓄積期】"
        phase_action = "奇策を避け、日々のトレードルールと資産運用のルーチンを着実に守るべき安定期です。"
        
    return phase_label, phase_action, curr_kanshi

def calculate_daily_trade_signal(target_date: datetime.date, p1_indices: Tuple[int, int, int], tc_branches: List[str]) -> Tuple[str, str, str, str, str, str]:
    _, _, d_idx = get_kanshi_indices(target_date)
    day_kanshi = KANSHI_60[d_idx]
    day_stem, day_branch = day_kanshi[0], day_kanshi[1]
    
    user_d_kanshi = KANSHI_60[p1_indices[2]]
    user_stem, user_branch = user_d_kanshi[0], user_d_kanshi[1]
    
    m_name, m_type, m_age, m_desc = get_moon_phase(target_date)
    
    is_tenchu = day_branch in tc_branches
    is_shigo = (day_branch, user_branch) in SHI_GOU_PAIRS or (user_branch, day_branch) in SHI_GOU_PAIRS
    is_sango = any({day_branch, user_branch}.issubset(g) for g in SAN_GOU_GROUPS)
    is_kango = (day_stem, user_stem) in KAN_GOU_PAIRS or (user_stem, day_stem) in KAN_GOU_PAIRS
    is_hiwa = (day_stem == user_stem)
    
    diff_branch = abs(SHI.index(day_branch) - SHI.index(user_branch))
    is_taichu = (diff_branch == 6)
    
    if (is_shigo or is_sango or is_kango) and m_type == "new":
        status = "lunar_boost"
        tag = "🌑 新月×合法（超共鳴エントリー日）"
        action = "天の追い風。新トレンド初動と宿命の拡大エネルギーが完全同期。自信を持って順張り。"
    elif (is_tenchu or is_taichu) and m_type == "full":
        status = "caution"
        tag = "🌕 満月×散法（魔境クラッシュ警戒）"
        action = "市場の過熱感と自身の散法が重なる最警戒日。突発的なヒゲ狩りに注意し完全ノートレード推奨。"
    elif is_tenchu:
        status = "caution"
        tag = "日天中殺・静観"
        action = "ノートレード推奨。想定外のヒゲや突発ニュースに巻き込まれやすい日。"
    elif is_taichu:
        status = "caution"
        tag = "対冲・損切り優先"
        action = "散法日。ポジション整理・手仕舞い推奨。新規エントリーは控える。"
    elif is_shigo or is_sango or is_kango or is_hiwa:
        status = "entry"
        tag = "合法・エントリー推奨"
        action = "順張りモメンタム適性高。気配値・板情報に素直に乗るトレードが機能。"
    else:
        status = "neutral"
        tag = "平常・定常運用"
        action = "通常運用日。機械的な損切り幅・利確幅を厳守してルーチントレード。"
        
    return day_kanshi, status, tag, action, m_name, m_type

@st.cache_data(ttl=300)
def fetch_realtime_market_metrics() -> Dict[str, float]:
    data = {"vix": 18.5}
    if YFINANCE_AVAILABLE:
        try:
            tickers = yf.Tickers('^VIX')
            hist_vix = tickers.tickers['^VIX'].history(period='2d')
            if not hist_vix.empty:
                data["vix"] = round(float(hist_vix['Close'].iloc[-1]), 2)
        except Exception:
            pass
    return data

def calculate_taiun_timeline(dt: datetime.date, gender: str, year_idx: int, month_idx: int, day_idx: int) -> Tuple[int, List[Dict]]:
    year_stem_idx = year_idx % 10
    is_yang_year = (year_stem_idx % 2 == 0)
    is_forward = (gender == "男性" and is_yang_year) or (gender == "女性" and not is_yang_year)
    start_age = 3 + (dt.day % 6)
    
    nikkan = KANSHI_60[day_idx][0]
    tc_branches = TENCHUSATSU_MAP[(day_kanshi_idx := (day_idx // 10) % 6)][1]

    timeline = []
    current_m_idx = month_idx
    step = 1 if is_forward else -1

    for i in range(8):
        current_m_idx = (current_m_idx + step) % 60
        kanshi_str = KANSHI_60[current_m_idx]
        branch = kanshi_str[1]
        star = get_star(nikkan, ZOKAN_MAP.get(branch, "戊"))
        is_tenchu = branch in tc_branches
        
        age_start = start_age + i * 10
        age_end = age_start + 9
        
        timeline.append({
            "age_range": f"{age_start}歳 〜 {age_end}歳",
            "age_start": age_start,
            "age_end": age_end,
            "kanshi": kanshi_str,
            "star": star,
            "is_tenchu": is_tenchu,
            "desc": STAR_MAP[star]["modern"]
        })
        
    return start_age, timeline

def get_gogyo_relation(k1: str, k2: str) -> Tuple[str, str]:
    g1 = KAN.index(k1) // 2
    g2 = KAN.index(k2) // 2
    diff = (g2 - g1) % 5
    if diff == 0:
        return "比和（同調・並走）", "対等な同志としてフラットに刺激し合える波長です。"
    elif diff == 1:
        return "相生（あなたが育てる・放出）", "あなたの持つエネルギーや知見が、相手の可能性を大きく引き出す関係性です。"
    elif diff == 4:
        return "相生（あなたが受ける・充電）", "相手の存在や助言が、あなたに安心感と確かな基盤をもたらす関係性です。"
    elif diff == 2:
        return "相剋（あなたが導く・統制）", "あなたが主導権を握り、相手の行動を現実的な成果へと方向付ける関係性です。"
    else:
        return "相剋（相手から鍛えられる・刺激）", "相手からのフィードバックによって、あなたの盲点が鍛えられ成長を促される関係性です。"

def analyze_universe_shape(indices: Tuple[int, int, int]) -> Tuple[str, str]:
    quads = {idx // 15 for idx in indices}
    count = len(quads)
    
    if count == 1:
        shape_type = "一象限集中型（専門特化・職人タイプ）"
        desc = "特定の活動領域に全エネルギーが凝縮。狭く深い専門領域や特化型スキルで無類の強みを発揮します。"
    elif count == 2:
        shape_type = "二象限架橋型（二刀流・往復推進タイプ）"
        desc = "2つの異なる機能（例：思考×行動）を高速で行き来し、構想をすぐ形にする機動力を持ちます。"
    elif count == 3:
        shape_type = "三象限展開型（バランス・事業展開タイプ）"
        desc = "大半の領域をカバーし、多様なステークホルダーと柔軟に連携しながら物事を進められる広がりを持ちます。"
    else:
        shape_type = "全象限網羅型（全方位・ゼネラリストタイプ）"
        desc = "4象限すべてに足場を持ち、あらゆる局面に対応可能。多角化経営や総合プロデュースに適します。"
        
    return shape_type, desc

# 偏差値・統計分布対応相性判定エンジン
def calculate_advanced_compatibility(p1_indices: Tuple[int, int, int], p2_indices: Tuple[int, int, int]) -> Dict:
    p1_d_kanshi = KANSHI_60[p1_indices[2]]
    p2_d_kanshi = KANSHI_60[p2_indices[2]]
    
    p1_nikkan, p1_d_shi = p1_d_kanshi[0], p1_d_kanshi[1]
    p2_nikkan, p2_d_shi = p2_d_kanshi[0], p2_d_kanshi[1]
    
    is_kango = (p1_nikkan, p2_nikkan) in KAN_GOU_PAIRS or (p2_nikkan, p1_nikkan) in KAN_GOU_PAIRS
    spiritual_score = 95 if is_kango else (75 + ((p1_indices[2] + p2_indices[2]) % 18))
    
    is_shigo = (p1_d_shi, p2_d_shi) in SHI_GOU_PAIRS or (p2_d_shi, p1_d_shi) in SHI_GOU_PAIRS
    is_sango = any({p1_d_shi, p2_d_shi}.issubset(g) for g in SAN_GOU_GROUPS)
    real_score = 96 if is_shigo else (92 if is_sango else (70 + ((p1_indices[1] + p2_indices[1]) % 22)))
    
    is_rittin = (p1_d_kanshi == p2_d_kanshi)
    is_nattin = (p1_nikkan == p2_nikkan and abs(SHI.index(p1_d_shi) - SHI.index(p2_d_shi)) == 6)
    
    special_bond = "なし"
    if is_rittin:
        special_bond = "律音（宿命的一体・魂の双子）"
        spiritual_score = 99
    elif is_nattin:
        special_bond = "納音（表裏一体・完全補完の縁）"
        real_score = 98
    
    p1_quads = {idx // 15 for idx in p1_indices}
    p2_quads = {idx // 15 for idx in p2_indices}
    overlap_quads = p1_quads.intersection(p2_quads)
    territory_score = 60 + len(overlap_quads) * 12
    
    total_score = int(spiritual_score * 0.35 + real_score * 0.35 + territory_score * 0.30)
    hearts_cnt = min(5, max(2, total_score // 20))
    hearts_str = "♥ " * hearts_cnt + "♡ " * (5 - hearts_cnt)
    
    z_compat = (total_score - 75) / 10.0
    compat_t_score = round(50.0 + 10.0 * z_compat, 1)
    compat_top_pct = round(max(0.5, min(99.5, 100.0 * (1.0 - 0.5 * (1.0 + math.erf(z_compat / math.sqrt(2)))))), 1)
    
    if compat_top_pct <= 20.0:
        one_in_n = max(2, round(100.0 / compat_top_pct))
        compat_rank_label = f"上位 {compat_top_pct}%（相性偏差値 {compat_t_score} / 約 {one_in_n}組に1組の強力共鳴）"
    elif compat_top_pct <= 80.0:
        compat_rank_label = f"中央層（上位 {compat_top_pct}% / 相性偏差値 {compat_t_score} / 標準シナジーゾーン）"
    else:
        one_in_n = max(2, round(100.0 / (100.0 - compat_top_pct)))
        compat_rank_label = f"要工夫・自立型（上位 {compat_top_pct}% / 相性偏差値 {compat_t_score} / 約 {one_in_n}組に1組）"
    
    return {
        "total_score": total_score,
        "spiritual_score": spiritual_score,
        "real_score": real_score,
        "territory_score": territory_score,
        "hearts_str": hearts_str,
        "compat_t_score": compat_t_score,
        "compat_top_pct": compat_top_pct,
        "compat_rank_label": compat_rank_label,
        "is_kango": is_kango,
        "is_shigo": is_shigo or is_sango,
        "special_bond": special_bond,
        "overlap_quads_count": len(overlap_quads)
    }

# 4象限機能領域のテーマカラー連動 宇宙盤描画エンジン
def draw_universe_chart(p1_indices: Tuple[int, int, int], p2_indices: Tuple[int, int, int] = None, p1_label="You", p2_label="Partner"):
    fig, ax = plt.subplots(figsize=(7.5, 7.5), subplot_kw={'projection': 'polar'}, dpi=140)
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#0f172a')

    angles = np.linspace(0, 2 * np.pi, 60, endpoint=False)
    ax.plot(angles, [60]*60, color='#475569', lw=1.5, alpha=0.8)
    
    for q in [0, np.pi/2, np.pi, 3*np.pi/2]:
        ax.plot([q, q], [0, 60], color='#334155', lw=1.5, ls='--')

    p1_angles = [angles[idx] for idx in p1_indices]
    p1_angles_cycle = p1_angles + [p1_angles[0]]
    p1_radii = [55, 55, 55, 55]
    ax.fill(p1_angles_cycle, p1_radii, color='#3b82f6', alpha=0.35, label=f"{p1_label}")
    ax.plot(p1_angles_cycle, p1_radii, color='#60a5fa', lw=2.5)
    
    quad_colors = ['#60a5fa', '#34d399', '#fbbf24', '#f43f5e']
    for idx, ang in zip(p1_indices, p1_angles):
        q_idx = idx // 15
        pt_color = quad_colors[q_idx % 4]
        ax.scatter([ang], [55], color=pt_color, s=110, edgecolors='#ffffff', lw=1.5, zorder=6)
        ax.text(ang, 68, KANSHI_60[idx], color=pt_color, fontsize=10, fontweight='bold', ha='center', va='center')

    if p2_indices is not None:
        p2_angles = [angles[idx] for idx in p2_indices]
        p2_angles_cycle = p2_angles + [p2_angles[0]]
        p2_radii = [48, 48, 48, 48]
        ax.fill(p2_angles_cycle, p2_radii, color='#c084fc', alpha=0.3, label=f"{p2_label}")
        ax.plot(p2_angles_cycle, p2_radii, color='#c084fc', lw=2.0)
        ax.scatter(p2_angles, [48, 48, 48], color='#c084fc', s=70, edgecolors='#ffffff', zorder=5)

    ax.set_yticklabels([])
    ax.set_xticks(np.linspace(0, 2*np.pi, 4, endpoint=False))
    ax.set_xticklabels([])
    
    ax.text(0, 84, '【第1領域】\n習得・知性', color='#60a5fa', fontsize=14, fontweight='bold', ha='center', va='center')
    ax.text(np.pi/2, 84, '【第2領域】\n行動・実務', color='#34d399', fontsize=14, fontweight='bold', ha='center', va='center')
    ax.text(np.pi, 84, '【第3領域】\n社交・蓄積', color='#fbbf24', fontsize=14, fontweight='bold', ha='center', va='center')
    ax.text(3*np.pi/2, 84, '【第4領域】\n精神・思索', color='#f43f5e', fontsize=14, fontweight='bold', ha='center', va='center')

    ax.spines['polar'].set_color('#475569')
    ax.grid(color='#334155', alpha=0.8, lw=1)
    ax.legend(loc='lower right', bbox_to_anchor=(1.28, -0.1), facecolor='#1e293b', edgecolor='#64748b', labelcolor='#ffffff', fontsize=11)
    plt.tight_layout()
    return fig

# ==========================================
# 3. 完全網羅型 エグゼクティブ・デザイナーズPDFエクスポート関数
# ==========================================
def generate_pdf_report(name: str, dob: datetime.date, gender: str, p1_indices: tuple, p1_stars: dict, tc_name: str, tc_type: str, energy_val: int, energy_class: str, top_pct: float, t_score: float, rank_label: str, consistency_label: str, consistency_desc: str, intuition_val: int, intuition_level: str, intuition_strategy: str, shugoshin_info: tuple, gogyo_dist: dict, p1_shape_type: str, p1_shape_desc: str, taiun_list: list, start_age: int, p1_age: int, year_phase_label: str, year_phase_action: str, curr_year_kanshi: str, current_year: int, chart_fig, enable_compatibility: bool = False, p2_name: str = "", p2_dob: datetime.date = None, p2_gender: str = "", p2_stars: dict = None, compat_data: dict = None, p1_to_p2_rel: tuple = None, p2_to_p1_rel: tuple = None) -> bytes:
    if not REPORTLAB_AVAILABLE:
        return b""
        
    buf = io.BytesIO()
    img_buf = io.BytesIO()
    chart_fig.savefig(img_buf, format='png', bbox_inches='tight', dpi=160, facecolor='#0f172a')
    img_buf.seek(0)
    
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=32, leftMargin=32, topMargin=28, bottomMargin=28)
    
    # 統一デザイナーズスタイル定義
    brand_header = ParagraphStyle('BH', fontName='HeiseiKakuGo-W5', fontSize=17, leading=21, textColor=colors.HexColor('#ffffff'), alignment=1)
    brand_sub = ParagraphStyle('BS', fontName='HeiseiKakuGo-W5', fontSize=8.5, leading=12, textColor=colors.HexColor('#93c5fd'), alignment=1)
    sec_title = ParagraphStyle('ST', fontName='HeiseiKakuGo-W5', fontSize=11, leading=15, textColor=colors.HexColor('#0284c7'), spaceBefore=8, spaceAfter=4)
    body_style = ParagraphStyle('Body', fontName='HeiseiKakuGo-W5', fontSize=8, leading=12, textColor=colors.HexColor('#334155'))
    card_text = ParagraphStyle('CT', fontName='HeiseiKakuGo-W5', fontSize=8, leading=12, textColor=colors.HexColor('#1e293b'))
    card_text_bold = ParagraphStyle('CTB', fontName='HeiseiKakuGo-W5', fontSize=8.5, leading=12, textColor=colors.HexColor('#0f172a'))
    cell_h = ParagraphStyle('CH', fontName='HeiseiKakuGo-W5', fontSize=8, leading=10, textColor=colors.HexColor('#ffffff'))
    cell_b = ParagraphStyle('CB', fontName='HeiseiKakuGo-W5', fontSize=7.5, leading=10.5, textColor=colors.HexColor('#1e293b'))
    
    elements = []
    
    # ----------------------------------------------------
    # SECTION 1: ヘッダー ＆ KPIサマリー（偏差値・上位％・エネルギー完全表記）
    # ----------------------------------------------------
    header_table = Table([[
        Paragraph("<b>SANMEI TALENT & ASSET ANALYTICS REPORT</b>", brand_header)
    ], [
        Paragraph(f"鑑定対象：<b>{name}</b> 様 ｜ 生年月日：{dob.strftime('%Y年%m月%d日')} ({gender}) ｜ 発行日：{datetime.date.today().strftime('%Y年%m月%d日')}", brand_sub)
    ]], colWidths=[531])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0f172a')),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8))
    
    kpi_data = [[
        Paragraph(f"<font color='#0284c7'><b>【エネルギー総量】</b></font><br/><font size='13'><b>{energy_val}</b> pt</font><br/>{energy_class}", card_text),
        Paragraph(f"<font color='#9333ea'><b>【統計偏差値】</b></font><br/><font size='13'><b>{t_score}</b></font><br/>上位 {top_pct}%", card_text),
        Paragraph(f"<font color='#059669'><b>【第1・第2守護神】</b></font><br/><font size='13'><b>{shugoshin_info[0]}</b> / <b>{shugoshin_info[1]}</b></font><br/>方位: {shugoshin_info[3]}", card_text),
        Paragraph(f"<font color='#f43f5e'><b>【直感力・霊感指数】</b></font><br/><font size='13'><b>{intuition_val}</b>%</font><br/>{intuition_level[:8]}", card_text)
    ]]
    t_kpi = Table(kpi_data, colWidths=[132, 133, 133, 133])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(t_kpi)
    elements.append(Spacer(1, 10))
    
    # ----------------------------------------------------
    # SECTION 2: 宿命命式 ＆ 核心才能ポートフォリオ
    # ----------------------------------------------------
    elements.append(Paragraph("【1. 宿命命式 ＆ 核心才能ポートフォリオ】", sec_title))
    k_year = KANSHI_60[p1_indices[0]]
    k_month = KANSHI_60[p1_indices[1]]
    k_day = KANSHI_60[p1_indices[2]]
    core_star = p1_stars["core"]
    
    data_profile = [
        [Paragraph("分析項目", cell_h), Paragraph("算出結果", cell_h), Paragraph("戦略的意味・本質解釈", cell_h)],
        [Paragraph("基本命式 (年/月/日)", cell_b), Paragraph(f"<b>{k_year}</b>年 / <b>{k_month}</b>月 / <b>{k_day}</b>日", cell_b), Paragraph("生涯を通じて根底にあるエネルギー構造と器のサイズ", cell_b)],
        [Paragraph("エネルギー・偏差値", cell_b), Paragraph(f"<b>{energy_val} pt</b><br/>(偏差値 <b>{t_score}</b> / 上位 <b>{top_pct}%</b>)", cell_b), Paragraph(f"{rank_label}<br/>数理法に基づく保有量（平均185pt）。", cell_b)],
        [Paragraph("中心核（胸の星）", cell_b), Paragraph(f"<b>{core_star}</b><br/>({STAR_MAP[core_star]['modern'][:8]})", cell_b), Paragraph(STAR_MAP[core_star]['desc'], cell_b)],
        [Paragraph("思考基軸（頭の星）", cell_b), Paragraph(f"<b>{p1_stars['north']}</b><br/>({STAR_MAP[p1_stars['north']]['modern'][:8]})", cell_b), Paragraph(f"{STAR_MAP[p1_stars['north']]['desc']}", cell_b)],
        [Paragraph("行動様式（東の星）", cell_b), Paragraph(f"<b>{p1_stars['east']}</b><br/>({STAR_MAP[p1_stars['east']]['modern'][:8]})", cell_b), Paragraph(f"{STAR_MAP[p1_stars['east']]['desc']}", cell_b)],
        [Paragraph("思考一貫性指数", cell_b), Paragraph(f"<b>{consistency_label}</b>", cell_b), Paragraph(consistency_desc, cell_b)],
        [Paragraph("天中殺グループ", cell_b), Paragraph(f"<b>{tc_name}</b><br/>({tc_type})", cell_b), Paragraph("周期的なバイオリズムとリスク管理傾向", cell_b)]
    ]
    t_prof = Table(data_profile, colWidths=[110, 140, 281])
    t_prof.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
    ]))
    elements.append(t_prof)
    elements.append(Spacer(1, 10))
    
    # ----------------------------------------------------
    # SECTION 3: 五行エネルギー配分バランス
    # ----------------------------------------------------
    elements.append(Paragraph("【2. 五行エネルギー配分バランス（数理法）】", sec_title))
    gogyo_cols_h = [Paragraph(f"<b>{g_k}</b>", cell_h) for g_k in gogyo_dist.keys()]
    gogyo_cols_v = [Paragraph(f"<b>{g_v} pt</b><br/>({round(g_v/energy_val*100, 1)}%)", cell_b) for g_v in gogyo_dist.values()]
    t_gogyo = Table([gogyo_cols_h, gogyo_cols_v], colWidths=[106.2]*5)
    t_gogyo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_gogyo)
    elements.append(Spacer(1, 10))
    
    # ----------------------------------------------------
    # SECTION 4: 職業適性・心理バイアス・アファメーション・陰徳
    # ----------------------------------------------------
    elements.append(Paragraph("【3. キャリア適性 ＆ 投資心理バイアス・アファメーション】", sec_title))
    box_career = [
        [Paragraph(f"<b>⭕️ あなたの才能を最大化する職業分野（適職領域）：</b><br/>{STAR_MAP[core_star]['fit_jobs']}", card_text)],
        [Paragraph(f"<b>❌ ストレスや摩擦が生じやすい非適職領域：</b><br/>{STAR_MAP[core_star]['unfit_jobs']}", card_text)],
        [Paragraph(f"<b>⚠️ 投資・トレード心理バイアスと防衛策：</b><br/>{STAR_MAP[core_star]['bias_trait']}", card_text)],
        [Paragraph(f"<b>🧘 波動を整えるアファメーション：</b><br/><i>{STAR_MAP[core_star]['affirmation']}</i>", card_text_bold)],
        [Paragraph(f"<b>💎 陰徳還元ルール（財多身弱防止）：</b><br/>大勝月利益の <b>2%〜3%</b> を社会・他者へ還元し、カルマの歪みを防ぐことで次なる大運の受け皿を拡張する。", card_text)]
    ]
    t_box_c = Table(box_career, colWidths=[531])
    t_box_c.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
    ]))
    elements.append(t_box_c)
    elements.append(Spacer(1, 14))
    
    # ----------------------------------------------------
    # SECTION 5: 資本配分・アセットアロケーション比較論
    # ----------------------------------------------------
    elements.append(PageBreak())
    header_table2 = Table([[
        Paragraph("<b>CAPITAL ALLOCATION & ASSET STRATEGY</b>", brand_header)
    ], [
        Paragraph("資本運用手法の客観的比較 ＆ リスク管理戦略", brand_sub)
    ]], colWidths=[531])
    header_table2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0f172a')),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(header_table2)
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph("【1. 気質ベースの推奨運用スタイル】", sec_title))
    rec_box = [[
        Paragraph(f"<b>🎯 本質推奨アセット：</b> {STAR_MAP[core_star]['invest_type']}", card_text_bold),
    ], [
        Paragraph(f"<b>運用上の強み：</b> {STAR_MAP[core_star]['invest_reason']}", card_text)
    ]]
    t_rec = Table(rec_box, colWidths=[531])
    t_rec.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#86efac')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_rec)
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph("【2. 主要資本運用手法の客観的比較グリッド】", sec_title))
    data_asset = [
        [Paragraph("運用手法", cell_h), Paragraph("主なメリット（構造的利点）", cell_h), Paragraph("構造的デメリット（リスク・課題）", cell_h)],
        [
            Paragraph("事業買収・M&A<br/>(事業投資)", cell_b),
            Paragraph("爆発的キャッシュフロー、経営権の行使、高レバレッジ", cell_b),
            Paragraph("PMI（買収後統合）の難航、偶発債務、換金困難な極めて低い流動性", cell_b)
        ],
        [
            Paragraph("実物不動産投資<br/>(現物資産)", cell_b),
            Paragraph("安定した賃料収入、融資活用、減価償却による節税", cell_b),
            Paragraph("空室・修繕コスト、金利上昇リスク、売却に数ヶ月〜半年要する流動性リスク", cell_b)
        ],
        [
            Paragraph("長期株式・積立<br/>(ペーパー資産)", cell_b),
            Paragraph("手間がかからない、世界経済の成長享受、少額から可能", cell_b),
            Paragraph("資金が長期間拘束、夜間や有事の暴落に資産を晒し続ける（不可抗力リスク）", cell_b)
        ],
        [
            Paragraph("<b>流動性取引<br/>(デイトレード)</b>", cell_b),
            Paragraph("<font color='#059669'><b>夜間暴落リスク完全ゼロ</b>、無限の資金回転率、即時換金性</font>", cell_b),
            Paragraph("<font color='#dc2626'><b>相場と向き合い続ける「根気と集中力」が必須（片手間不可）</b></font>", cell_b)
        ]
    ]
    t_asset = Table(data_asset, colWidths=[105, 205, 221])
    t_asset.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#ecfdf5')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t_asset)
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph("【3. 戦略結論：なぜ「根気」を払う価値があるのか？】", sec_title))
    conclusion_box = [[
        Paragraph(
            "M&Aや不動産が抱える最大の構造リスクは<b>『いざという時に数ヶ月間現金化できない流動性リスク』</b>と<b>『偶発的な外部環境ショック』</b>です。<br/><br/>"
            "デイトレードは、相場の時間をしっかり使い、繰り返しトレードを経験してコツ（板の気配や値動きの呼吸）をつかむまでの根気を最も要求されます。"
            "しかし、その対価として得られる<b>『市場が閉まるたびに資産が100%現金に戻る絶対的な防衛力』</b>と<b>『一生モノの相場技術』</b>という見返りは、他のどのアセットクラスにも存在しない唯一無二の優位性です。",
            card_text
        )
    ]]
    t_conc = Table(conclusion_box, colWidths=[531])
    t_conc.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#38bdf8')),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    elements.append(t_conc)
    elements.append(Spacer(1, 14))
    
    # ----------------------------------------------------
    # SECTION 6: 周期リスク（大運・年運）＆ 守護神
    # ----------------------------------------------------
    elements.append(PageBreak())
    header_table3 = Table([[
        Paragraph("<b>BIORYTHM TIMELINE & RISK MANAGEMENT</b>", brand_header)
    ], [
        Paragraph("大運（10年周期）・年間バイオリズム ＆ 宿命守護神", brand_sub)
    ]], colWidths=[531])
    header_table3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0f172a')),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(header_table3)
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph(f"【1. 人生の大運タイムライン（{start_age}歳立運 / 現在 {p1_age}歳）】", sec_title))
    data_taiun = [
        [Paragraph("年代・期間", cell_h), Paragraph("干支", cell_h), Paragraph("巡る主星", cell_h), Paragraph("大運テーマ・環境変化", cell_h), Paragraph("状態判定", cell_h)]
    ]
    for item in taiun_list:
        is_active = item["age_start"] <= p1_age <= item["age_end"]
        status_text = "<font color='#0284c7'><b>CURRENT</b></font>" if is_active else ("<font color='#d97706'><b>大運天中殺</b></font>" if item["is_tenchu"] else "通常")
        data_taiun.append([
            Paragraph(item["age_range"], cell_b),
            Paragraph(item["kanshi"], cell_b),
            Paragraph(item["star"], cell_b),
            Paragraph(item["desc"], cell_b),
            Paragraph(status_text, cell_b)
        ])
    t_taiun = Table(data_taiun, colWidths=[85, 45, 75, 245, 81])
    t_taiun.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    elements.append(t_taiun)
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph(f"【2. {current_year}年 年間バイオリズム判定 ＆ 守護神エネルギー】", sec_title))
    year_risk_box = [
        [Paragraph(f"<b>📅 年間判定（干支：{curr_year_kanshi} / {tc_name}）：</b><br/>{year_phase_label} ➔ {year_phase_action}", card_text)],
        [Paragraph(f"<b>🔮 宿命守護神：</b> 第1守護神【<b>{shugoshin_info[0]}</b>】 ｜ 第2守護神【<b>{shugoshin_info[1]}</b>】 ｜ ラッキーカラー：<b>{shugoshin_info[4]}</b> ｜ 吉方位：<b>{shugoshin_info[3]}</b><br/><b>波動調和の理：</b> {shugoshin_info[5]}", card_text)],
        [Paragraph(f"<b>⚡️ 第六感・直感力戦略（指数 {intuition_val}%）：</b><br/>{intuition_strategy}", card_text)]
    ]
    t_y_risk = Table(year_risk_box, colWidths=[531])
    t_y_risk.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
    ]))
    elements.append(t_y_risk)
    elements.append(Spacer(1, 14))
    
    # ----------------------------------------------------
    # SECTION 7: 五行セクター ＆ 宇宙盤行動テリトリー
    # ----------------------------------------------------
    elements.append(PageBreak())
    header_table4 = Table([[
        Paragraph("<b>SECTOR SUITABILITY & ACTION TERRITORY</b>", brand_header)
    ], [
        Paragraph("五行東証33業種セクター適性 ＆ 宇宙盤4象限マップ", brand_sub)
    ]], colWidths=[531])
    header_table4.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0f172a')),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(header_table4)
    elements.append(Spacer(1, 10))
    
    min_gogyo = min(gogyo_dist.items(), key=lambda x: x[1])[0]
    max_gogyo = max(gogyo_dist.items(), key=lambda x: x[1])[0]
    sec_info_rec = GOGYO_SECTOR_MAP[min_gogyo]
    sec_info_dom = GOGYO_SECTOR_MAP[max_gogyo]
    
    elements.append(Paragraph("【1. 五行エネルギー × 東証33業種・推奨セクター】", sec_title))
    sec_box = [
        [
            Paragraph(f"<b>🟢 補完推奨セクター（{min_gogyo}）：</b><br/><b>注視テーマ：</b> {sec_info_rec['theme']}<br/><b>選定根拠：</b> 命式内で不足する五行を補完し、ポートフォリオと運気の循環を整える。", card_text),
            Paragraph(f"<b>🔵 得意モメンタムセクター（{max_gogyo}）：</b><br/><b>注視テーマ：</b> {sec_info_dom['theme']}<br/><b>選定根拠：</b> 最大エネルギー分野。値動きの呼吸が気質と合致し、波を直感的に掴みやすい。", card_text)
        ]
    ]
    t_sec = Table(sec_box, colWidths=[265, 266])
    t_sec.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
    ]))
    elements.append(t_sec)
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph(f"【2. 宇宙盤マップ ＆ 幾何学パターン判定（{p1_shape_type}）】", sec_title))
    desc_p4 = Paragraph(
        f"<b>形状分析：</b> {p1_shape_desc}<br/><br/>"
        "<font color='#0284c7'><b>【第1領域】習得・知性：</b></font> データ分析・理論構築・リスク管理のステージ。<br/>"
        "<font color='#059669'><b>【第2領域】行動・実務：</b></font> 現場突破・即時決断・機動力のステージ。<br/>"
        "<font color='#d97706'><b>【第3領域】社交・蓄積：</b></font> 資本蓄積・人脈形成・着実な前進のステージ。<br/>"
        "<font color='#e11d48'><b>【第4領域】精神・思索：</b></font> 直感洞察・独自哲学・イノベーションのステージ。",
        body_style
    )
    img_element = RLImage(img_buf, width=215, height=215)
    t_bottom = Table([[img_element, desc_p4]], colWidths=[230, 301])
    t_bottom.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(t_bottom)
    elements.append(Spacer(1, 14))
    
    # ----------------------------------------------------
    # SECTION 8: 多角的相性シナジー（相性モードON時）
    # ----------------------------------------------------
    if enable_compatibility and compat_data is not None:
        elements.append(PageBreak())
        header_table5 = Table([[
            Paragraph(f"<b>COMPATIBILITY & TEAM SYNERGY REPORT</b>", brand_header)
        ], [
            Paragraph(f"{name} 様 × {p2_name} 様 ｜ 多角的相性アナリティクス", brand_sub)
        ]], colWidths=[531])
        header_table5.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0f172a')),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(header_table5)
        elements.append(Spacer(1, 10))
        
        special_str = f" ｜ 特殊縁：<b>{compat_data['special_bond']}</b>" if compat_data['special_bond'] != "なし" else ""
        c_kpi_data = [[
            Paragraph(f"<font color='#f43f5e'><b>【総合相性スコア】</b></font><br/><font size='14'><b>{compat_data['total_score']}%</b></font><br/>{compat_data['hearts_str']}", card_text),
            Paragraph(f"<font color='#9333ea'><b>【相性偏差値】</b></font><br/><font size='14'><b>{compat_data['compat_t_score']}</b></font><br/>上位 {compat_data['compat_top_pct']}%", card_text),
            Paragraph(f"<font color='#0284c7'><b>【精神・魂の引き寄せ】</b></font><br/><font size='14'><b>{compat_data['spiritual_score']}%</b></font><br/>干合判定", card_text),
            Paragraph(f"<font color='#059669'><b>【現実・事業シナジー】</b></font><br/><font size='14'><b>{compat_data['real_score']}%</b></font><br/>支合/三合判定", card_text)
        ]]
        t_c_kpi = Table(c_kpi_data, colWidths=[132, 133, 133, 133])
        t_c_kpi.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(t_c_kpi)
        elements.append(Spacer(1, 10))
        
        p1_role_text = get_partner_role(core_star)
        p2_role_text = get_partner_role(p2_stars['core'])
        
        elements.append(Paragraph("【1. 4軸シナジー ＆ 動的役割分担・チームビルディング】", sec_title))
        compat_box = [
            [Paragraph(f"<b>🤝 4軸シナジー判定：</b> {compat_data['compat_rank_label']}{special_str}<br/>宇宙盤領域の共有率：4象限中 <b>{compat_data['overlap_quads_count']}</b> 領域が共通。", card_text)],
            [Paragraph(f"<b>🔄 双方向五行ダイナミクス：</b><br/>・{name} 様 ➔ {p2_name} 様：<b>{p1_to_p2_rel[0]}</b>（{p1_to_p2_rel[1]}）<br/>・{p2_name} 様 ➔ {name} 様：<b>{p2_to_p1_rel[0]}</b>（{p2_to_p1_rel[1]}）", card_text)],
            [Paragraph(f"<b>🎯 星の資質に基づく動的役割分担：</b><br/>・<b>{name} 様（{core_star}）：</b> {p1_role_text}<br/>・<b>{p2_name} 様（{p2_stars['core']}）：</b> {p2_role_text}", card_text_bold)],
            [Paragraph(f"<b>⚠️ 摩擦防止コミュニケーション指針：</b><br/>重要事項や数字の認識は必ずテキストで共有し、お互いの休止期（天中殺）や宇宙盤の独立専門領域には過度に干渉しない。", card_text)]
        ]
        t_compat = Table(compat_box, colWidths=[531])
        t_compat.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(t_compat)
        
    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()

def generate_cheat_sheet_pdf(name: str, p1_nikkan: str, p1_core: str, p1_east: str, current_year: int, current_month: int, p1_indices: tuple, tc_branches: list, shugoshin_info: tuple) -> bytes:
    if not REPORTLAB_AVAILABLE:
        return b""
        
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=32, leftMargin=32, topMargin=28, bottomMargin=28)
    
    title_style = ParagraphStyle('Title', fontName='HeiseiKakuGo-W5', fontSize=15, leading=19, textColor=colors.HexColor('#ffffff'), alignment=1)
    sub_style = ParagraphStyle('Sub', fontName='HeiseiKakuGo-W5', fontSize=8.5, leading=12, textColor=colors.HexColor('#93c5fd'), alignment=1)
    h2_style = ParagraphStyle('H2', fontName='HeiseiKakuGo-W5', fontSize=10.5, leading=14, textColor=colors.HexColor('#0284c7'), spaceBefore=8, spaceAfter=4)
    body_style = ParagraphStyle('Body', fontName='HeiseiKakuGo-W5', fontSize=7.5, leading=11, textColor=colors.HexColor('#334155'))
    cell_h = ParagraphStyle('CH', fontName='HeiseiKakuGo-W5', fontSize=7.5, leading=10, textColor=colors.whitesmoke)
    cell_b = ParagraphStyle('CB', fontName='HeiseiKakuGo-W5', fontSize=7, leading=9.5, textColor=colors.HexColor('#1e293b'))
    
    elements = []
    
    header_table = Table([[
        Paragraph(f"<b>SANMEI MONTHLY TRADING CHEAT SHEET ({current_year}年{current_month}月)</b>", title_style)
    ], [
        Paragraph(f"対象：<b>{name}</b> 様 ｜ 日干：<b>{p1_nikkan}</b> ｜ 守護神：<b>{shugoshin_info[0]}</b>, <b>{shugoshin_info[1]}</b> ｜ カラー：{shugoshin_info[4]}", sub_style)
    ]], colWidths=[531])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0f172a')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8))
    
    elements.append(Paragraph("【1. 当月トレード・バイオリズム ＆ ルナサイクル（月相）シグナル一覧】", h2_style))
    cal = calendar.Calendar(firstweekday=6)
    m_days = [d for d in cal.itermonthdates(current_year, current_month) if d.month == current_month]
    
    t_data = [[Paragraph("日付", cell_h), Paragraph("日干支", cell_h), Paragraph("月相", cell_h), Paragraph("判定シグナル", cell_h), Paragraph("実戦行動指針", cell_h)]]
    for d in m_days:
        d_kanshi, d_status, d_tag, d_action, m_name, m_type = calculate_daily_trade_signal(d, p1_indices, tc_branches)
        status_color = '#7e22ce' if d_status == 'lunar_boost' else ('#15803d' if d_status == 'entry' else ('#b91c1c' if d_status == 'caution' else '#334155'))
        t_data.append([
            Paragraph(f"{d.strftime('%m/%d')} ({['月','火','水','木','金','土','日'][d.weekday()]})", cell_b),
            Paragraph(d_kanshi, cell_b),
            Paragraph(m_name[:4], cell_b),
            Paragraph(f"<font color='{status_color}'><b>{d_tag}</b></font>", cell_b),
            Paragraph(d_action, cell_b)
        ])
    t_sheet = Table(t_data, colWidths=[55, 40, 50, 110, 276])
    t_sheet.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(t_sheet)
    elements.append(Spacer(1, 8))
    
    elements.append(Paragraph("【2. メンタル規律・波動チューニング ＆ アファメーション】", h2_style))
    elements.append(Paragraph(f"<b>アファメーション：</b> {STAR_MAP[p1_core]['affirmation']}<br/><b>陰徳還元ルール：</b> 大勝した利益の2〜3%を社会や他者へ還元し、カルマの歪み（財多身弱）を防ぐ。", body_style))
    
    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()

# ==========================================
# 4. URLパラメータ連動型 セッション初期化（安全参照化）
# ==========================================
query_params = st.query_params

def parse_date_param(param_name: str, default_date: datetime.date) -> datetime.date:
    if param_name in query_params:
        try:
            return datetime.date.fromisoformat(query_params[param_name])
        except Exception:
            return default_date
    return default_date

def sync_to_url():
    st.query_params["p1_name"] = st.session_state.get("p1_name_input", "あなた")
    p1_dob_val = st.session_state.get("p1_dob_input", datetime.date(1992, 5, 18))
    st.query_params["p1_dob"] = p1_dob_val.isoformat() if hasattr(p1_dob_val, "isoformat") else str(p1_dob_val)
    st.query_params["p1_gender"] = st.session_state.get("p1_gender_input", "男性")
    
    compat_val = st.session_state.get("compat_toggle", False)
    st.query_params["compat"] = str(compat_val).lower()
    
    st.query_params["p2_name"] = st.session_state.get("p2_name_input", "パートナー")
    p2_dob_val = st.session_state.get("p2_dob_input", datetime.date(1994, 11, 23))
    st.query_params["p2_dob"] = p2_dob_val.isoformat() if hasattr(p2_dob_val, "isoformat") else str(p2_dob_val)
    st.query_params["p2_gender"] = st.session_state.get("p2_gender_input", "女性")
    st.query_params["tab"] = st.session_state.get("active_tab", "profile")

if "p1_name_input" not in st.session_state:
    st.session_state.p1_name_input = query_params.get("p1_name", "あなた")
if "p1_dob_input" not in st.session_state:
    st.session_state.p1_dob_input = parse_date_param("p1_dob", datetime.date(1992, 5, 18))
if "p1_gender_input" not in st.session_state:
    st.session_state.p1_gender_input = query_params.get("p1_gender", "男性")
if "compat_toggle" not in st.session_state:
    st.session_state.compat_toggle = (query_params.get("compat", "false") == "true")
if "p2_name_input" not in st.session_state:
    st.session_state.p2_name_input = query_params.get("p2_name", "パートナー")
if "p2_dob_input" not in st.session_state:
    st.session_state.p2_dob_input = parse_date_param("p2_dob", datetime.date(1994, 11, 23))
if "p2_gender_input" not in st.session_state:
    st.session_state.p2_gender_input = query_params.get("p2_gender", "女性")
if "active_tab" not in st.session_state:
    st.session_state.active_tab = query_params.get("tab", "profile")
if "trade_log" not in st.session_state:
    st.session_state.trade_log = []

# ==========================================
# 5. サイドバー入力 & PDF出力
# ==========================================
with st.sidebar:
    st.markdown("### 📊 プロファイル設定")
    st.markdown("---")
    
    st.markdown("#### 👤 あなたの情報")
    p1_name = st.text_input("氏名 / 呼称", key="p1_name_input", on_change=sync_to_url)
    p1_dob = st.date_input(
        "生年月日", 
        min_value=datetime.date(1930, 1, 1), 
        max_value=datetime.date(2030, 12, 31),
        key="p1_dob_input",
        on_change=sync_to_url
    )
    p1_gender = st.radio("性別", ["男性", "女性"], horizontal=True, key="p1_gender_input", on_change=sync_to_url)
    
    st.markdown("---")
    enable_compatibility = st.toggle("👥 相性診断モードを有効化", key="compat_toggle", on_change=sync_to_url)
    
    p2_name = st.session_state.get("p2_name_input", "パートナー")
    p2_dob = st.session_state.get("p2_dob_input", datetime.date(1994, 11, 23))
    p2_gender = st.session_state.get("p2_gender_input", "女性")
    p2_indices = None
    p2_stars = None
    compat_data = None
    p1_to_p2_rel = None
    p2_to_p1_rel = None
    
    if enable_compatibility:
        st.markdown("#### 🎯 パートナーの情報")
        p2_name = st.text_input("氏名 / 呼称", key="p2_name_input", on_change=sync_to_url)
        p2_dob = st.date_input(
            "生年月日", 
            min_value=datetime.date(1930, 1, 1), 
            max_value=datetime.date(2030, 12, 31),
            key="p2_dob_input",
            on_change=sync_to_url
        )
        p2_gender = st.radio("性別", ["女性", "男性"], horizontal=True, key="p2_gender_input", on_change=sync_to_url)

    # 算命学・偏差値データの計算
    p1_indices = get_kanshi_indices(p1_dob)
    p1_stars = get_yosen_stars(*p1_indices)
    p1_nikkan = KANSHI_60[p1_indices[2]][0]
    p1_core = p1_stars["core"]
    p1_north = p1_stars["north"]
    p1_east = p1_stars["east"]
    tc_name, tc_branches, tc_type = get_tenchusatsu_info(p1_indices[2])
    
    shugoshin_info = SHUGOSHIN_MAP.get(p1_nikkan, ("丙", "癸", "木", "東", "グリーン", "調和の守護神"))
    intuition_val, intuition_level, intuition_strategy = calculate_intuition_index(p1_stars, KANSHI_60[p1_indices[2]])
    consistency_score, consistency_label, consistency_desc = calculate_mind_consistency(p1_stars)
    energy_val, energy_class, top_pct, t_score, rank_label, gogyo_dist = calculate_energy_metrics(p1_indices[2], p1_indices[1], p1_indices[0])
    p1_shape_type, p1_shape_desc = analyze_universe_shape(p1_indices)
    
    current_year = datetime.date.today().year
    current_month = datetime.date.today().month
    current_year_branch = SHI[(current_year - 4) % 12]
    is_in_tenchusatsu = current_year_branch in tc_branches
    
    p1_age = current_year - p1_dob.year
    start_age, taiun_list = calculate_taiun_timeline(p1_dob, p1_gender, p1_indices[0], p1_indices[1], p1_indices[2])
    year_phase_label, year_phase_action, curr_year_kanshi = calculate_year_phase(current_year, p1_indices)
    
    if enable_compatibility:
        p2_indices = get_kanshi_indices(p2_dob)
        p2_stars = get_yosen_stars(*p2_indices)
        p2_nikkan = KANSHI_60[p2_indices[2]][0]
        compat_data = calculate_advanced_compatibility(p1_indices, p2_indices)
        p1_to_p2_rel = get_gogyo_relation(p1_nikkan, p2_nikkan)
        p2_to_p1_rel = get_gogyo_relation(p2_nikkan, p1_nikkan)

    st.markdown("---")
    st.markdown("#### 📑 レポート出力")
    
    if REPORTLAB_AVAILABLE:
        try:
            pdf_fig = draw_universe_chart(p1_indices, p2_indices if enable_compatibility else None, p1_label=p1_name, p2_label=p2_name if enable_compatibility else "Partner")
            pdf_bytes_full = generate_pdf_report(
                p1_name, p1_dob, p1_gender, p1_indices, p1_stars, tc_name, tc_type, 
                energy_val, energy_class, top_pct, t_score, rank_label, consistency_label, consistency_desc, 
                intuition_val, intuition_level, intuition_strategy, shugoshin_info, gogyo_dist, 
                p1_shape_type, p1_shape_desc, taiun_list, start_age, p1_age, year_phase_label, 
                year_phase_action, curr_year_kanshi, current_year, pdf_fig, 
                enable_compatibility, p2_name, p2_dob, p2_gender, p2_stars, compat_data, p1_to_p2_rel, p2_to_p1_rel
            )
            plt.close(pdf_fig)
            
            st.download_button(
                label="📥 完全版エグゼクティブ鑑定書PDF",
                data=pdf_bytes_full,
                file_name=f"Sanmei_Executive_Report_{p1_name}_{datetime.date.today().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
            cheat_pdf_bytes = generate_cheat_sheet_pdf(p1_name, p1_nikkan, p1_core, p1_east, current_year, current_month, p1_indices, tc_branches, shugoshin_info)
            st.download_button(
                label="📥 月間実戦チートシートPDF",
                data=cheat_pdf_bytes,
                file_name=f"Trade_CheatSheet_{p1_name}_{current_year}{current_month:02d}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"PDF生成エラー: {e}")
    else:
        st.caption("⚠️ PDF出力には `pip install reportlab` が必要です。")

# ==========================================
# 6. メインビュー & 最適化ナビゲーション
# ==========================================
st.markdown("""
<div class="analytics-header">
    <div class="analytics-title">SANMEI TRADING & TALENT ANALYTICS</div>
    <div class="analytics-sub">算命学宿命論 × 自己理解・投資戦略・バイオリズム＆実戦トレード</div>
</div>
""", unsafe_allow_html=True)

nav_options = [
    ("profile", "🧬 1. 自己宿命・才能・エネルギー"),
    ("strategy", "💼 2. 適職・投資スタイル＆心理罠"),
    ("risk", "⏳ 3. 周期リスク・大運＆守護神"),
    ("sector", "🎯 4. 五行セクター＆宇宙盤"),
    ("trade", "⚡️ 5. 実戦トレード＆市場アラート"),
    ("log", "📈 6. トレード勝率バックテスト")
]
if enable_compatibility:
    nav_options.append(("compat", "👥 7. 多角的相性シナジー"))

cols = st.columns(len(nav_options))
for idx, (key, label) in enumerate(nav_options):
    with cols[idx]:
        is_active = (st.session_state.active_tab == key)
        btn_type = "primary" if is_active else "secondary"
        if st.button(label, key=f"nav_btn_{key}", use_container_width=True, type=btn_type):
            st.session_state.active_tab = key
            sync_to_url()
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)
active_view = st.session_state.active_tab

# ------------------------------------------
# STEP 1: 自己宿命・才能・エネルギー
# ------------------------------------------
if active_view == "profile":
    st.markdown("##### 🧬 Step 1: 自己の根源宿命 ＆ エネルギー・才能構造の把握")
    st.caption("あなたが生まれ持った本質エネルギー量、統計的偏差値、思考の一貫性を定義します。")
    
    m_col1, m_col2, m_col3 = st.columns([1, 1.2, 1.2])
    
    with m_col1:
        render_html(f"""
        <div class="card-modern card-highlight" style="height:100%;">
            <div style="font-size:0.75rem; letter-spacing:0.05em; color:#94a3b8; font-weight:700;">STATISTICAL RARITY & DEVIATION</div>
            <div class="metric-val">{top_pct}%</div>
            <div style="font-size:1.0rem; font-weight:700; color:#ffffff; margin-top:6px;">エネルギー偏差値：{t_score}</div>
            <p style="color:#cbd5e1; font-size:0.8rem; line-height:1.5; margin-top:6px;">
                全60干支・五行分布に基づく客観的ポジション。上位 <strong>{top_pct}%</strong> の統計的位置づけ。
            </p>
        </div>
        """)
        
    with m_col2:
        render_html(f"""
        <div class="card-modern card-energy" style="height:100%;">
            <div style="font-size:0.75rem; letter-spacing:0.05em; color:#a5b4fc; font-weight:700;">ENERGY CAPACITY & RANK</div>
            <div class="metric-energy">{energy_val}<span style="font-size:1.4rem; color:#818cf8;">pt</span></div>
            <div class="energy-rank-badge">⚡️ {rank_label}</div>
            <div style="font-size:0.95rem; font-weight:700; color:#ffffff; margin-top:6px;">{energy_class}</div>
            <p style="color:#cbd5e1; font-size:0.8rem; line-height:1.5; margin-top:4px;">
                数理法に基づくエネルギー保有量。事業や相場を動かす現実的推進力の規模。
            </p>
        </div>
        """)
        
    with m_col3:
        render_html(f"""
        <div class="card-modern" style="margin-bottom:12px;">
            <div style="font-size:0.75rem; color:#38bdf8; font-weight:700;">PRIMARY TRAIT</div>
            <h4 style="color:#ffffff; margin:2px 0 4px 0;">命式：{KANSHI_60[p1_indices[0]]}年 / {KANSHI_60[p1_indices[1]]}月 / {KANSHI_60[p1_indices[2]]}日</h4>
            <p style="color:#38bdf8; font-weight:700; margin:4px 0;">中心核（胸の星）：{p1_core}（{STAR_MAP[p1_core]['modern']}）</p>
            <p style="color:#cbd5e1; font-size:0.82rem; margin:0;">
                {STAR_MAP[p1_core]['desc']}
            </p>
        </div>
        <div class="card-modern">
            <div style="font-size:0.75rem; color:#93c5fd; font-weight:700;">MIND CONSISTENCY (思考一貫性)</div>
            <div style="color:#ffffff; font-weight:700; font-size:0.95rem;">{consistency_label} ({consistency_score}%)</div>
            <p style="color:#cbd5e1; font-size:0.80rem; margin:2px 0 0 0;">
                {consistency_desc}
            </p>
        </div>
        """)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 🧪 五行エネルギー配分バランス（数理配分）")
    g_cols = st.columns(5)
    for i, (g_name, g_val) in enumerate(gogyo_dist.items()):
        with g_cols[i]:
            render_html(f"""
            <div style="background:rgba(15,23,42,0.8); border:1px solid #334155; border-radius:8px; padding:10px; text-align:center;">
                <div style="font-size:0.8rem; color:#94a3b8; font-weight:700;">{g_name}</div>
                <div style="font-size:1.4rem; font-weight:800; color:#38bdf8; margin:4px 0;">{g_val} pt</div>
                <div style="font-size:0.75rem; color:#cbd5e1;">配分比率: {round(g_val / energy_val * 100, 1)}%</div>
            </div>
            """)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 核心機能（才能ポートフォリオ）")
    
    t_cols = st.columns(3)
    stars = [(p1_core, "中心核（胸）"), (p1_north, "思考基軸（頭）"), (p1_east, "行動様式（東）")]
    for i, (s_name, tag) in enumerate(stars):
        with t_cols[i]:
            info = STAR_MAP[s_name]
            render_html(f"""
            <div class="talent-tile-modern">
                <div class="talent-tag">{tag}</div>
                <div class="talent-title">{info['modern']}</div>
                <div class="star-tag">原星：{s_name}</div>
                <p style="font-size:0.85rem; color:#cbd5e1; line-height:1.6; margin:0;">{info['desc']}</p>
            </div>
            """)

# ------------------------------------------
# STEP 2: 適職・投資スタイル＆心理罠
# ------------------------------------------
elif active_view == "strategy":
    st.markdown("##### 💼 Step 2: キャリア・適職適性 ＆ 資本運用・投資スタイルと心理バイアス")
    st.caption("自己の気質に適合する職業・投資手法と、トレードで陥りやすい心理的罠（バイアス）を明確化します。")
    
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        render_html(f"""
        <div class="card-modern card-success">
            <div style="font-size:0.75rem; color:#34d399; font-weight:800;">CAREER FIT & UNFIT</div>
            <h4 style="color:#ffffff; margin:4px 0 8px 0;">あなたの才能を最大化する職業分野</h4>
            <div style="margin-bottom:12px;">
                <span style="color:#34d399; font-weight:700; font-size:0.9rem;">⭕️ 最も強みを発揮できる適職領域：</span>
                <p style="color:#f8fafc; font-size:0.88rem; margin:4px 0 0 0; line-height:1.6;">{STAR_MAP[p1_core]['fit_jobs']}</p>
            </div>
            <div style="margin-bottom:12px;">
                <span style="color:#f87171; font-weight:700; font-size:0.9rem;">❌ ストレスや摩擦が生じやすい非適職領域：</span>
                <p style="color:#cbd5e1; font-size:0.88rem; margin:4px 0 0 0; line-height:1.6;">{STAR_MAP[p1_core]['unfit_jobs']}</p>
            </div>
            <div>
                <span style="color:#fbbf24; font-weight:700; font-size:0.9rem;">⚠️ 投資・トレード時の心理バイアス傾向：</span>
                <p style="color:#fde68a; font-size:0.85rem; margin:4px 0 0 0; line-height:1.6;">{STAR_MAP[p1_core]['bias_trait']}</p>
            </div>
        </div>
        """)
        
    with c_col2:
        render_html(f"""
        <div class="card-modern card-highlight">
            <div style="font-size:0.75rem; color:#38bdf8; font-weight:800;">INVESTMENT STRATEGY</div>
            <h4 style="color:#ffffff; margin:4px 0 8px 0;">気質ベースの推奨運用スタイル</h4>
            <div style="margin-bottom:8px;">
                <span style="background:rgba(56,189,248,0.2); color:#38bdf8; padding:3px 10px; border-radius:6px; font-weight:800; font-size:0.95rem;">
                    🎯 本質適性：{STAR_MAP[p1_core]['invest_type']}
                </span>
            </div>
            <p style="color:#cbd5e1; font-size:0.88rem; line-height:1.7; margin-top:10px;">
                <strong style="color:#ffffff;">【気質的な強み】：</strong><br>
                {STAR_MAP[p1_core]['invest_reason']}
            </p>
        </div>
        """)

    render_html("""
    <div class="card-modern card-strategy">
        <div style="font-size:0.8rem; color:#94a3b8; font-weight:800; letter-spacing:0.05em; margin-bottom:4px;">
            CAPITAL ALLOCATION ANALYSIS | 資本運用手法の客観的比較
        </div>
        <h4 style="color:#ffffff; margin:0 0 10px 0;">🔍 現代の主要投資アプローチにおけるメリット・デメリットの整理</h4>
        <p style="color:#cbd5e1; font-size:0.85rem; line-height:1.6; margin-bottom:12px;">
            資産形成には多様な選択肢が存在し、それぞれ異なるリスク・リターン構造を持ちます。各手法の長所と短所を客観的に比較した上で、最適な資本配分を検討する必要があります。
        </p>
        <div class="asset-compare-grid">
            <div class="asset-box">
                <div class="asset-box-title"><span>🏢 事業買収・M&A</span><span style="color:#94a3b8; font-size:0.75rem;">事業投資</span></div>
                <div class="asset-box-pros">✔ <strong>利点:</strong> 爆発的キャッシュフロー、経営権の行使、高レバレッジ</div>
                <div class="asset-box-cons">✖ <strong>欠点:</strong> 買収後の統合作業（PMI）の難航、偶発債務リスク、換金困難な極めて低い流動性</div>
            </div>
            <div class="asset-box">
                <div class="asset-box-title"><span>🏠 実物不動産投資</span><span style="color:#94a3b8; font-size:0.75rem;">現物資産</span></div>
                <div class="asset-box-pros">✔ <strong>利点:</strong> 安定したインカムゲイン、融資活用、減価償却による節税</div>
                <div class="asset-box-cons">✖ <strong>欠点:</strong> 空室・修繕コスト、金利上昇リスク、売却に数ヶ月〜半年要する流動性リスク</div>
            </div>
            <div class="asset-box">
                <div class="asset-box-title"><span>📈 伝統的長期株式・積立</span><span style="color:#94a3b8; font-size:0.75rem;">ペーパー資産</span></div>
                <div class="asset-box-pros">✔ <strong>利点:</strong> 手間がかからない、世界経済の成長享受、少額から可能</div>
                <div class="asset-box-cons">✖ <strong>欠点:</strong> 資金が長期間拘束、夜間や有事の暴落に資産を晒し続ける（不可抗力リスク）</div>
            </div>
            <div class="asset-box" style="border-color:#38bdf8; background:rgba(56,189,248,0.05);">
                <div class="asset-box-title"><span style="color:#38bdf8;">⚡️ 流動性取引（デイトレ）</span><span style="color:#38bdf8; font-size:0.75rem;">即時決済</span></div>
                <div class="asset-box-pros">✔ <strong>利点:</strong> 夜間暴落リスクが構造上ゼロ、無限の資金回転率、即時換金性</div>
                <div class="asset-box-cons">✖ <strong>欠点:</strong> <strong style="color:#f87171;">相場と向き合い続ける「根気と集中力」が必須（片手間不可）</strong></div>
            </div>
        </div>
        <div style="background:rgba(15,23,42,0.8); border-left:3px solid #38bdf8; padding:12px 16px; border-radius:4px; margin-top:14px;">
            <div style="color:#ffffff; font-weight:700; font-size:0.9rem; margin-bottom:4px;">
                💡 結論：なぜ「根気」を払う価値があるのか？（デイトレードの戦略的見返り）
            </div>
            <p style="color:#cbd5e1; font-size:0.85rem; line-height:1.7; margin:0;">
                M&Aや不動産が抱える最大の構造リスクは「いざという時に数ヶ月間現金化できない流動性リスク」と「偶発的な外部環境ショック」です。
                デイトレードは、<strong>『相場の時間をしっかり使い、繰り返しトレードを経験してコツ（板の気配や値動きの呼吸）をつかむまでの根気』</strong>を最も要求されます。しかし、その対価として得られる<strong>「市場が閉まるたびに資産が100%現金に戻る絶対的な防衛力」</strong>と<strong>「一生モノの相場技術」</strong>という見返りは、他のどのアセットクラスにも存在しない唯一無二の優位性です。
            </p>
        </div>
    </div>
    """)

# ------------------------------------------
# STEP 3: 周期リスク・大運＆守護神
# ------------------------------------------
elif active_view == "risk":
    st.markdown("##### ⏳ Step 3: 周期リスク管理（大運・年運） ＆ 宿命守護神・波動チューニング")
    st.caption("人生の長期10年スパンの波、年単位の勝負/調整期、および波長を整える守護神エネルギーを分析します。")

    st.markdown(f"###### 🧬 人生の大運タイムライン（{start_age}歳立運 / 現在 {p1_age}歳）")
    
    taiun_boxes = []
    for item in taiun_list:
        is_active = item["age_start"] <= p1_age <= item["age_end"]
        
        card_class = "taiun-card"
        if is_active:
            card_class += " taiun-card-active"
        elif item["is_tenchu"]:
            card_class += " taiun-card-tenchu"
            
        badge = ""
        if is_active:
            badge = '<div class="taiun-badge-active">CURRENT</div>'
        elif item["is_tenchu"]:
            badge = '<div class="taiun-badge-tenchu">大運天中殺</div>'

        box_html = (
            f'<div class="{card_class}">'
            f'{badge}'
            f'<div class="taiun-age">{item["age_range"]}</div>'
            f'<div class="taiun-kanshi">干支：{item["kanshi"]}</div>'
            f'<div class="taiun-star">巡る主星：{item["star"]}</div>'
            f'<div style="font-size:0.8rem; color:#cbd5e1; line-height:1.4;">{item["desc"]}</div>'
            f'</div>'
        )
        taiun_boxes.append(box_html)
        
    render_html(f'<div class="timeline-grid">{"".join(taiun_boxes)}</div>')

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"###### 📅 {current_year}年 年間バイオリズム判定（干支：{curr_year_kanshi} / {tc_name}）")
    y_col1, y_col2 = st.columns(2)
    
    with y_col1:
        card_class = "card-warning" if is_in_tenchusatsu else "card-modern"
        status_label = "【運気調整・天中殺期】" if is_in_tenchusatsu else year_phase_label
        render_html(f"""
        <div class="card-modern {card_class}">
            <div style="font-size:0.75rem; color:#fbbf24; font-weight:700;">ANNUAL RISK & PHASE ALERT</div>
            <h4 style="color:#ffffff; margin:4px 0 8px 0;">{status_label}</h4>
            <p style="color:#cbd5e1; font-size:0.88rem; line-height:1.6; margin-bottom:10px;">
                {year_phase_action}
            </p>
            <ul style="color:#cbd5e1; font-size:0.85rem; line-height:1.7; padding-left:18px;">
                <li><strong>不確実性の増大：</strong> 新規分野への大型投資・拡張は想定外の変数が生じやすい時期です。</li>
                <li><strong>判断バイアス：</strong> 短期的な焦りから、リスク検証が甘くなりやすい傾向があります。</li>
                <li><strong>コミュニケーション齟齬：</strong> 重要な合意事項の言った言わないに注意が必要です。</li>
            </ul>
        </div>
        """)
        
    with y_col2:
        render_html(f"""
        <div class="card-modern card-spiritual">
            <div style="font-size:0.75rem; color:#c084fc; font-weight:800;">GUARDIAN ELEMENT & WAVE TUNING</div>
            <h4 style="color:#ffffff; margin:4px 0 8px 0;">日干【{p1_nikkan}】の守護神：第1【{shugoshin_info[0]}】 ｜ 第2【{shugoshin_info[1]}】</h4>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin:8px 0;">
                <div style="background:rgba(15,23,42,0.6); padding:8px 10px; border-radius:6px;">
                    <span style="font-size:0.75rem; color:#94a3b8;">ラッキーカラー</span><br>
                    <strong style="color:#ffffff; font-size:0.85rem;">{shugoshin_info[4]}</strong>
                </div>
                <div style="background:rgba(15,23,42,0.6); padding:8px 10px; border-radius:6px;">
                    <span style="font-size:0.75rem; color:#94a3b8;">トレード吉方位</span><br>
                    <strong style="color:#ffffff; font-size:0.85rem;">{shugoshin_info[3]}</strong>
                </div>
            </div>
            <p style="color:#cbd5e1; font-size:0.85rem; line-height:1.6; margin:0;">
                <strong>【波動調和の理】：</strong><br>{shugoshin_info[5]}
            </p>
        </div>
        """)

# ------------------------------------------
# STEP 4: 五行セクター＆宇宙盤
# ------------------------------------------
elif active_view == "sector":
    st.markdown("##### 🎯 Step 4: 五行セクター適性 ＆ 宇宙盤行動テリトリー")
    st.caption("東証33業種からあなたの気質と五行を補完する銘柄テーマを絞り込み、行動スタイルを可視化します。")
    
    min_gogyo = min(gogyo_dist.items(), key=lambda x: x[1])[0]
    max_gogyo = max(gogyo_dist.items(), key=lambda x: x[1])[0]
    
    sec_col1, sec_col2 = st.columns(2)
    
    with sec_col1:
        sec_info_rec = GOGYO_SECTOR_MAP[min_gogyo]
        render_html(f"""
        <div class="card-modern card-success">
            <div style="font-size:0.75rem; color:#34d399; font-weight:800;">PRIMARY RECOMMENDED SECTOR (補完セクター)</div>
            <h4 style="color:#ffffff; margin:4px 0 8px 0;">{min_gogyo} 関連テーマ銘柄</h4>
            <div style="background:rgba(15,23,42,0.6); padding:10px; border-radius:6px; margin-bottom:8px;">
                <strong style="color:#34d399;">注視テーマ：</strong> {sec_info_rec['theme']}
            </div>
            <p style="color:#cbd5e1; font-size:0.85rem; line-height:1.6;">
                <strong>【選定根拠】：</strong><br>
                命式内で最もエネルギーが不足している「{min_gogyo[:1]}」の要素を持つセクターを手掛けることで、ポートフォリオと運気の五行循環が完全補完されます。
            </p>
        </div>
        """)
        
    with sec_col2:
        sec_info_dom = GOGYO_SECTOR_MAP[max_gogyo]
        render_html(f"""
        <div class="card-modern card-highlight">
            <div style="font-size:0.75rem; color:#38bdf8; font-weight:800;">NATURAL MOMENTUM SECTOR (得意領域)</div>
            <h4 style="color:#ffffff; margin:4px 0 8px 0;">{max_gogyo} 関連テーマ銘柄</h4>
            <div style="background:rgba(15,23,42,0.6); padding:10px; border-radius:6px; margin-bottom:8px;">
                <strong style="color:#38bdf8;">注視テーマ：</strong> {sec_info_dom['theme']}
            </div>
            <p style="color:#cbd5e1; font-size:0.85rem; line-height:1.6;">
                <strong>【選定根拠】：</strong><br>
                自身の保有エネルギーが最大の「{max_gogyo[:1]}」分野。値動きの呼吸が気質と合致しやすく、モメンタムの波を直感的に掴みやすいセクターです。
            </p>
        </div>
        """)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("###### 🌐 宇宙盤（行動テリトリー幾何学判定）")
    
    u_col1, u_col2 = st.columns([1.1, 1.1])
    with u_col1:
        fig = draw_universe_chart(p1_indices, p1_label=p1_name)
        st.pyplot(fig)
        
    with u_col2:
        render_html(f"""
        <div class="card-modern card-highlight" style="margin-top:10px; margin-bottom:12px;">
            <div style="font-size:0.75rem; color:#38bdf8; font-weight:800;">SHAPE PATTERN ANALYSIS</div>
            <h4 style="color:#ffffff; margin:4px 0 6px 0;">{p1_shape_type}</h4>
            <p style="color:#cbd5e1; font-size:0.85rem; line-height:1.6; margin:0;">
                {p1_shape_desc}
            </p>
        </div>
        """)
        
        render_html("""
        <div class="card-modern">
            <h5 style="color:#ffffff; margin-top:0; margin-bottom:10px;">🧭 4象限の機能領域</h5>
            <div style="margin-bottom:8px; background:rgba(15,23,42,0.6); padding:8px 10px; border-radius:6px; border-left:3px solid #3b82f6;">
                <strong style="color:#60a5fa; font-size:0.9rem;">【第1領域】習得・知性：</strong>
                <span style="color:#cbd5e1; font-size:0.8rem;">データ分析・理論構築・リスク管理のステージ。</span>
            </div>
            <div style="margin-bottom:8px; background:rgba(15,23,42,0.6); padding:8px 10px; border-radius:6px; border-left:3px solid #10b981;">
                <strong style="color:#34d399; font-size:0.9rem;">【第2領域】行動・実務：</strong>
                <span style="color:#cbd5e1; font-size:0.8rem;">現場突破・即時決断・機動力のステージ。</span>
            </div>
            <div style="margin-bottom:8px; background:rgba(15,23,42,0.6); padding:8px 10px; border-radius:6px; border-left:3px solid #fbbf24;">
                <strong style="color:#fbbf24; font-size:0.9rem;">【第3領域】社交・蓄積：</strong>
                <span style="color:#cbd5e1; font-size:0.8rem;">資本蓄積・人脈形成・着実な前進のステージ。</span>
            </div>
            <div style="background:rgba(15,23,42,0.6); padding:8px 10px; border-radius:6px; border-left:3px solid #f43f5e;">
                <strong style="color:#f43f5e; font-size:0.9rem;">【第4領域】精神・思索：</strong>
                <span style="color:#cbd5e1; font-size:0.8rem;">直感洞察・独自哲学・イノベーションのステージ。</span>
            </div>
        </div>
        """)

# ------------------------------------------
# STEP 5: 実戦トレード＆市場アラート
# ------------------------------------------
elif active_view == "trade":
    st.markdown("##### ⚡️ Step 5: 実戦トレード・バイオリズム ＆ リアルタイム市場アラート")
    st.caption("日々の干支・月相（ルナサイクル）と市場ボラティリティ（VIX）を統合した売買シグナルです。")
    
    today = datetime.date.today()
    today_kanshi, today_status, today_tag, today_action, m_name, m_type = calculate_daily_trade_signal(today, p1_indices, tc_branches)
    market_data = fetch_realtime_market_metrics()
    
    t_col1, t_col2 = st.columns([1.1, 1.2])
    
    with t_col1:
        card_border_class = "card-spiritual" if today_status == "lunar_boost" else ("card-success" if today_status == "entry" else ("card-danger" if today_status == "caution" else "card-highlight"))
        status_color = "#c084fc" if today_status == "lunar_boost" else ("#34d399" if today_status == "entry" else ("#f87171" if today_status == "caution" else "#38bdf8"))
        
        render_html(f"""
        <div class="card-modern {card_border_class}" style="height:100%;">
            <div style="font-size:0.75rem; color:{status_color}; font-weight:800; letter-spacing:0.05em;">TODAY'S TRADE & LUNAR SIGNAL ({today.strftime('%Y/%m/%d')})</div>
            <div style="font-size:1.6rem; font-weight:800; color:#ffffff; margin:6px 0;">
                本日干支：{today_kanshi} ｜ {m_name[:4]}
            </div>
            <div style="color:{status_color}; font-weight:800; font-size:1.15rem; margin-bottom:6px;">
                ➔ {today_tag}
            </div>
            <p style="color:#cbd5e1; font-size:0.88rem; line-height:1.6; margin-top:8px;">
                <strong>【本日の行動指針】：</strong><br>{today_action}
            </p>
            <div style="margin-top:12px; font-size:0.8rem; color:#94a3b8; background:rgba(15,23,42,0.6); padding:8px 10px; border-radius:6px;">
                日干：<strong>{p1_nikkan}</strong> ｜ 胸の星：<strong>{p1_core}</strong> ｜ 守護神：<strong>{shugoshin_info[0]}</strong>
            </div>
        </div>
        """)
        
    with t_col2:
        st.markdown("###### 🎛️ リアルタイム市場環境 ＆ メンタルアラート")
        
        current_vix = market_data["vix"]
        st.caption(f"現在の市場恐怖指数 (VIX): **{current_vix}** （{'Yahoo Finance LIVE' if YFINANCE_AVAILABLE else 'シミュレーション値'}）")
        
        if current_vix < 16.0:
            vix_alert_title = "🟢 低ボラティリティ安定相場：順張り・押し目狙い"
            vix_alert_desc = f"{STAR_MAP[p1_core]['modern'][:8]}を軸に、トレンドフォローとブレイクアウトを淡々と実行。"
            vix_card_class = "card-success"
        elif current_vix < 22.0:
            vix_alert_title = "🟡 レンジ・通常相場：利確の徹底と回転"
            vix_alert_desc = f"{STAR_MAP[p1_east]['modern'][:8]}を意識し、欲張らずに回転重視の利確とタイトな損切りを厳守。"
            vix_card_class = "card-highlight"
        elif current_vix < 28.0:
            vix_alert_title = "🟠 乱高下警戒相場：ロット半減 ＆ 飛びつき禁止"
            vix_alert_desc = f"【気質バイアス警告】{STAR_MAP[p1_core]['bias_trait']} 通常の50%以下のポジションサイズに抑制。"
            vix_card_class = "card-warning"
        else:
            vix_alert_title = "🔴 クラッシュ・パニック相場：ノートレード優先 ＆ 現金防衛"
            vix_alert_desc = "夜間リスク完全ゼロの強みを死守。感情的なナンピンやリベンジトレードは破滅の元。"
            vix_card_class = "card-danger"
            
        render_html(f"""
        <div class="card-modern {vix_card_class}">
            <div style="font-size:0.8rem; font-weight:800; color:#ffffff;">{vix_alert_title}</div>
            <p style="color:#cbd5e1; font-size:0.85rem; line-height:1.6; margin:6px 0 0 0;">
                {vix_alert_desc}
            </p>
        </div>
        """)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"###### 📅 {today.year}年 {today.month}月 月間トレード・バイオリズム ＆ 月相カレンダー")
    
    cal_obj = calendar.Calendar(firstweekday=6)
    month_days = cal_obj.monthdatescalendar(today.year, today.month)
    
    day_headers = ["日", "月", "火", "水", "木", "金", "土"]
    cal_html_parts = ['<div class="calendar-grid">']
    for dh in day_headers:
        cal_html_parts.append(f'<div class="cal-header">{dh}</div>')
        
    for week in month_days:
        for d in week:
            if d.month != today.month:
                cal_html_parts.append('<div class="cal-day-box" style="opacity:0.25;"><div class="cal-date-num">' + str(d.day) + '</div></div>')
            else:
                d_kanshi, d_status, d_tag, d_action, dm_name, dm_type = calculate_daily_trade_signal(d, p1_indices, tc_branches)
                day_box_cls = "cal-day-lunar-boost" if d_status == "lunar_boost" else ("cal-day-entry" if d_status == "entry" else ("cal-day-caution" if d_status == "caution" else "cal-day-neutral"))
                tag_cls = "cal-tag-lunar" if d_status == "lunar_boost" else ("cal-tag-entry" if d_status == "entry" else ("cal-tag-caution" if d_status == "caution" else "cal-tag-neutral"))
                short_tag = "超共鳴" if d_status == "lunar_boost" else ("エントリー" if d_status == "entry" else ("注意・守備" if d_status == "caution" else "定常"))
                
                is_today_style = 'border:2px solid #c084fc !important;' if d == today else ''
                
                day_cell = (
                    f'<div class="cal-day-box {day_box_cls}" style="{is_today_style}">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                    f'<span class="cal-date-num">{d.day}</span>'
                    f'<span style="font-size:0.7rem; color:#cbd5e1;">{dm_name[:2]}</span>'
                    f'</div>'
                    f'<div class="cal-kanshi">{d_kanshi}</div>'
                    f'<div class="cal-tag {tag_cls}">{short_tag}</div>'
                    f'</div>'
                )
                cal_html_parts.append(day_cell)
                
    cal_html_parts.append('</div>')
    render_html("".join(cal_html_parts))

# ------------------------------------------
# STEP 6: トレード勝率バックテスト
# ------------------------------------------
elif active_view == "log":
    st.markdown("##### 📈 Step 6: トレード履歴 ＆ 算命学バイオリズム勝率バックテスト")
    st.caption("日々のトレード結果を記録し、「合法日（エントリー日）」と「散法・天中殺日（守備日）」の勝率・損益を自動比較します。")
    
    in_col1, in_col2, in_col3, in_col4 = st.columns([1.2, 1.2, 1, 1])
    with in_col1:
        t_date = st.date_input("トレード日", value=datetime.date.today(), key="trade_in_date")
    with in_col2:
        t_ticker = st.text_input("銘柄コード / 通貨ペア", value="7203 トヨタ", key="trade_in_ticker")
    with in_col3:
        t_pl = st.number_input("損益（円 / pips）", value=15000, step=1000, key="trade_in_pl")
    with in_col4:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if st.button("➕ トレード記録を追加", use_container_width=True):
            _, d_status, d_tag, _, _, _ = calculate_daily_trade_signal(t_date, p1_indices, tc_branches)
            st.session_state.trade_log.append({
                "date": t_date.strftime("%Y-%m-%d"),
                "ticker": t_ticker,
                "pl": t_pl,
                "signal": d_tag,
                "is_entry_day": (d_status in ["entry", "lunar_boost"]),
                "is_caution_day": (d_status == "caution")
            })
            st.success("トレード記録を保存しました。")
            st.rerun()
            
    if len(st.session_state.trade_log) > 0:
        df_log = pd.DataFrame(st.session_state.trade_log)
        
        entry_trades = df_log[df_log["is_entry_day"]]
        caution_trades = df_log[df_log["is_caution_day"]]
        
        e_win_rate = round((entry_trades["pl"] > 0).mean() * 100, 1) if len(entry_trades) > 0 else 0
        c_win_rate = round((caution_trades["pl"] > 0).mean() * 100, 1) if len(caution_trades) > 0 else 0
        
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        with stat_col1:
            render_html(f"""
            <div class="card-modern card-success">
                <div style="font-size:0.75rem; color:#34d399; font-weight:800;">ENTRY / LUNAR DAYS (合法・超共鳴日)</div>
                <div style="font-size:2.2rem; font-weight:800; color:#ffffff;">勝率 {e_win_rate}%</div>
                <div style="font-size:0.85rem; color:#cbd5e1;">取引数: {len(entry_trades)}件 ｜ 総損益: {entry_trades['pl'].sum():,} 円</div>
            </div>
            """)
        with stat_col2:
            render_html(f"""
            <div class="card-modern card-danger">
                <div style="font-size:0.75rem; color:#f87171; font-weight:800;">CAUTION DAYS (散法・天中殺日)</div>
                <div style="font-size:2.2rem; font-weight:800; color:#ffffff;">勝率 {c_win_rate}%</div>
                <div style="font-size:0.85rem; color:#cbd5e1;">取引数: {len(caution_trades)}件 ｜ 総損益: {caution_trades['pl'].sum():,} 円</div>
            </div>
            """)
        with stat_col3:
            render_html(f"""
            <div class="card-modern card-highlight">
                <div style="font-size:0.75rem; color:#38bdf8; font-weight:800;">TOTAL PERFORMANCE</div>
                <div style="font-size:2.2rem; font-weight:800; color:#ffffff;">{df_log['pl'].sum():,} 円</div>
                <div style="font-size:0.85rem; color:#cbd5e1;">全トレード数: {len(df_log)}件 ｜ 勝率: {round((df_log['pl'] > 0).mean() * 100, 1)}%</div>
            </div>
            """)
            
        st.dataframe(df_log, use_container_width=True)
    else:
        st.info("💡 上部の入力欄からトレード履歴を追加すると、バイオリズムごとの勝率バックテストが集計されます。")

# ------------------------------------------
# STEP 7: 多角的相性シナジー
# ------------------------------------------
elif active_view == "compat" and enable_compatibility:
    st.markdown(f"##### 👥 Step 7: {p1_name} × {p2_name} の多角的相性アナリティクス")
    st.caption("精神的引き寄せ（干合）、現実的連携（支合・三合）、特殊宿命縁（律音/納音）、宇宙盤重複度を総合評価。")
    
    c_col1, c_col2 = st.columns([1.1, 1.2])
    with c_col1:
        special_bond_html = f'<div style="color:#f472b6; font-weight:700; font-size:0.9rem; margin-top:4px;">✨ 特殊縁：{compat_data["special_bond"]}</div>' if compat_data["special_bond"] != "なし" else ""
        
        render_html(f"""
        <div class="card-modern card-highlight" style="height:100%;">
            <div style="font-size:0.75rem; color:#f43f5e; font-weight:800;">OVERALL COMPATIBILITY</div>
            <div style="display:flex; align-items:center; gap:14px; margin: 6px 0;">
                <div class="hearts-display">{compat_data['hearts_str']}</div>
                <div style="font-size:3.0rem; font-weight:800; color:#f43f5e;">{compat_data['total_score']}%</div>
            </div>
            <div style="font-size:1.05rem; font-weight:700; color:#ffffff;">
                {'👑 宿命的引き寄せペア（強力共鳴）' if compat_data['is_kango'] or compat_data['is_shigo'] else '🤝 相互補完・安定シナジーペア'}
            </div>
            {special_bond_html}
            <p style="font-size:0.85rem; color:#cbd5e1; line-height:1.6; margin-top:6px;">
                お互いの強みが相手の盲点を埋め、意思決定と実行がスムーズに循環する高適合構成です。
            </p>
            <div class="ratio-pill-clean">
                {compat_data['compat_rank_label']}
            </div>
        </div>
        """)
        
    with c_col2:
        kango_desc = '【干合成立】無意識レベルで波長が合い、理屈を超えて惹かれ合う関係性。' if compat_data['is_kango'] else '自然体で互いの価値観をフラットに認め合える安定した精神的波長。'
        shigo_desc = '【支合/三合成立】金銭感覚や日々の生活リズムが噛み合い、共同作業で成果が倍増。' if compat_data['is_shigo'] else '役割分担を明確にすることで、手堅く現実的な成果を積み重ねられる関係。'
        
        render_html(f"""
        <div class="card-modern" style="height:100%;">
            <div style="font-size:0.75rem; color:#60a5fa; font-weight:800; margin-bottom:10px;">4-AXIS SYNERGY ANALYSIS</div>
            <div style="margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between; font-size:0.85rem; font-weight:700;">
                    <span style="color:#ffffff;">1. 精神・魂の引き寄せ度（干合判定）</span>
                    <span style="color:#38bdf8;">{compat_data["spiritual_score"]}%</span>
                </div>
                <p style="color:#94a3b8; font-size:0.78rem; margin:2px 0 0 0;">{kango_desc}</p>
            </div>
            <div style="margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between; font-size:0.85rem; font-weight:700;">
                    <span style="color:#ffffff;">2. 現実・生活・事業の結びつき（支合・三合）</span>
                    <span style="color:#34d399;">{compat_data["real_score"]}%</span>
                </div>
                <p style="color:#94a3b8; font-size:0.78rem; margin:2px 0 0 0;">{shigo_desc}</p>
            </div>
            <div>
                <div style="display:flex; justify-content:space-between; font-size:0.85rem; font-weight:700;">
                    <span style="color:#ffffff;">3. 行動テリトリーの重なり（宇宙盤共有率）</span>
                    <span style="color:#fbbf24;">{compat_data["territory_score"]}%</span>
                </div>
                <p style="color:#94a3b8; font-size:0.78rem; margin:2px 0 0 0;">4象限中 {compat_data["overlap_quads_count"]} 領域が共通。互いの専門性を認め合える最適な距離感。</p>
            </div>
        </div>
        """)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("###### 🔄 視点別アプローチ（五行ダイナミクス）")
    
    p_col1, p_col2 = st.columns(2)
    with p_col1:
        p2_core_name = p2_stars['core'] if p2_stars else "相手の中心星"
        p1_to_p2_title = p1_to_p2_rel[0] if p1_to_p2_rel else ""
        p1_to_p2_desc = p1_to_p2_rel[1] if p1_to_p2_rel else ""
        render_html(f"""
        <div class="card-modern">
            <div style="font-size:0.75rem; color:#60a5fa; font-weight:700;">FROM {p1_name.upper()} ➔ {p2_name.upper()}</div>
            <h5 style="color:#ffffff; margin:4px 0 8px 0;">{p1_to_p2_title}</h5>
            <p style="color:#cbd5e1; font-size:0.85rem; line-height:1.6; margin-bottom:8px;">{p1_to_p2_desc}</p>
            <p style="color:#94a3b8; font-size:0.85rem; line-height:1.6; margin:0;">
                あなたの「{STAR_MAP[p1_core]['modern'][:8]}」の資質を活かし、相手の「{STAR_MAP.get(p2_core_name, {}).get('modern', '')[:8]}」の良さを引き出す関わりが最適です。
            </p>
        </div>
        """)
        
    with p_col2:
        p2_to_p1_title = p2_to_p1_rel[0] if p2_to_p1_rel else ""
        p2_to_p1_desc = p2_to_p1_rel[1] if p2_to_p1_rel else ""
        render_html(f"""
        <div class="card-modern">
            <div style="font-size:0.75rem; color:#f472b6; font-weight:700;">FROM {p2_name.upper()} ➔ {p1_name.upper()}</div>
            <h5 style="color:#ffffff; margin:4px 0 8px 0;">{p2_to_p1_title}</h5>
            <p style="color:#cbd5e1; font-size:0.85rem; line-height:1.6; margin-bottom:8px;">{p2_to_p1_desc}</p>
            <p style="color:#94a3b8; font-size:0.85rem; line-height:1.6; margin:0;">
                {p2_name}さんから見て、あなたの安定感と軸の強さは心強い頼りどころとして機能しています。
            </p>
        </div>
        """)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("###### 💼 共同事業・投資・共同生活における最適シナリオ")
    
    syn_col1, syn_col2 = st.columns(2)
    with syn_col1:
        p1_role_text = get_partner_role(p1_core)
        p2_role_text = get_partner_role(p2_stars['core']) if p2_stars else ""
        p2_core_display = p2_stars['core'] if p2_stars else ""
        render_html(f"""
        <div class="card-modern card-success">
            <div style="font-size:0.75rem; color:#34d399; font-weight:800;">DYNAMIC ROLE ALLOCATION</div>
            <h5 style="color:#ffffff; margin:4px 0 8px 0;">🎯 星の資質に基づく動的役割分担</h5>
            <ul style="color:#cbd5e1; font-size:0.85rem; line-height:1.7; padding-left:18px;">
                <li><strong>{p1_name} 様（{p1_core}）：</strong> {p1_role_text}</li>
                <li><strong>{p2_name} 様（{p2_core_display}）：</strong> {p2_role_text}</li>
                <li><strong>資金・資産運用：</strong> 互いの盲点を補い合い、攻めと守りを星の特性に応じて二重チェックする体制が最適です。</li>
            </ul>
        </div>
        """)
        
    with syn_col2:
        render_html("""
        <div class="card-modern card-warning">
            <div style="font-size:0.75rem; color:#fbbf24; font-weight:800;">FRICTION PREVENTION</div>
            <h5 style="color:#ffffff; margin:4px 0 8px 0;">⚠️ 摩擦を防ぐためのコミュニケーション指針</h5>
            <ul style="color:#cbd5e1; font-size:0.85rem; line-height:1.7; padding-left:18px;">
                <li><strong>暗黙の了解を避ける：</strong> 重要事項や数字の認識は必ず言語化・テキスト共有して確認する。</li>
                <li><strong>相手の「休止期」を尊重：</strong> お互いの天中殺周期やバイオリズムが異なる時期は無理にペースを合わせない。</li>
                <li><strong>互いの聖域を守る：</strong> 宇宙盤で重なっていない独立領域（個人の専門分野）には過度に干渉しない。</li>
            </ul>
        </div>
        """)