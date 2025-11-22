import streamlit as st

def apply_portal_style():
    """公開画面用の白ベースデザイン"""
    st.markdown("""
        <style>
        /* 全体設定 */
        .stApp { background-color: #ffffff !important; color: #333333 !important; }
        .block-container { max-width: 1100px; padding-top: 1rem; padding-bottom: 5rem; }
        
        /* --- UI非表示設定 (超強力版) --- */
        
        /* 1. ヘッダー・ツールバー・装飾ライン */
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        .stDeployButton { 
            display: none !important; 
            visibility: hidden !important;
        }
        
        /* 2. フッター ("Hosted with Streamlit" など) 
           display:noneで消えない場合があるため、透明にして画面外へ飛ばす */
        footer { 
            visibility: hidden !important; 
            opacity: 0 !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            position: fixed !important;
            left: -9999px !important; /* 画面外へ */
        }
        
        /* 3. ステータスウィジェット (右下のRunningアニメーション等) */
        [data-testid="stStatusWidget"] { 
            display: none !important; 
            visibility: hidden !important;
        }
        
        /* 4. ハンバーガーメニュー */
        #MainMenu { display: none !important; }
        
        /* 5. ビューワーバッジ（右下のプロフィールアイコン） 
           クラス名が変わっても対応できるよう、属性セレクタで指定 */
        div[class*="viewerBadge"] { 
            display: none !important; 
            visibility: hidden !important;
        }
        
        /* --- カードデザイン (高さ固定) --- */
        a.quiz-card-link {
            text-decoration: none !important;
            color: inherit !important;
            display: block !important;
        }
        a.quiz-card-link:hover { text-decoration: none !important; }

        .quiz-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
            height: 420px; 
            display: flex;
            flex-direction: column;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            transition: all 0.2s ease-in-out;
            margin-bottom: 10px;
            cursor: pointer;
            position: relative;
        }
        
        .quiz-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
            border-color: #cbd5e1;
        }
        
        /* 画像エリア */
        .quiz-thumb-box {
            width: 100%;
            height: 180px;
            background-color: #f1f5f9;
            overflow: hidden;
            position: relative;
            flex-shrink: 0;
        }
        .quiz-thumb {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.5s ease;
        }
        .quiz-card:hover .quiz-thumb { transform: scale(1.05); }
        
        /* コンテンツエリア */
        .quiz-content {
            padding: 16px;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }
        
        /* タイトル */
        .quiz-title { 
            font-weight: bold;
            font-size: 1.1rem;
            margin-bottom: 8px;
            color: #1e293b;
            line-height: 1.4;
            height: 2.8em;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }
        
        /* 説明文 */
        .quiz-desc { 
            font-size: 0.85rem;
            color: #64748b;
            line-height: 1.6;
            height: 4.8em;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            margin-bottom: auto;
        }
        
        /* バッジ */
        .badge-new { 
            position: absolute; top: 10px; left: 10px; 
            background: rgba(255,255,255,0.9); color: #1e40af; 
            font-size: 0.65rem; padding: 2px 6px; border-radius: 4px; font-weight: bold; z-index: 2;
        }
        .badge-stats {
            position: absolute; bottom: 5px; right: 5px;
            background: rgba(0,0,0,0.6); color: white;
            font-size: 0.7rem; padding: 2px 8px; border-radius: 12px; font-weight: bold; z-index: 2;
        }
        
        /* ボタン共通設定 */
        .stButton button {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            color: #334155 !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            padding: 0.6rem 1rem !important;
            transition: all 0.2s !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        }
        .stButton button:hover {
            border-color: #94a3b8 !important;
            background-color: #f1f5f9 !important;
            color: #1e293b !important;
            transform: translateY(-1px);
        }
        
        /* プライマリボタン */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%) !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2) !important;
        }
        .stButton button[kind="primary"]:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #4338ca 100%) !important;
            box-shadow: 0 6px 10px rgba(37, 99, 235, 0.3) !important;
            color: white !important;
        }
        
        /* セカンダリボタン */
        .stButton button[kind="secondary"] {
            background: #fff1f2 !important;
            color: #e11d48 !important;
            border: 1px solid #fecdd3 !important;
        }
        .stButton button[kind="secondary"]:hover {
            background: #ffe4e6 !important;
            border-color: #fda4af !important;
            color: #be123c !important;
        }

        /* リンクボタン */
        a[data-testid="stLinkButton"] {
            background-color: #1e293b !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: bold !important;
            text-align: center !important;
            border-radius: 8px !important;
            transition: all 0.2s !important;
            margin-top: auto !important;
            display: block !important;
            padding: 10px !important;
        }
        a[data-testid="stLinkButton"]:hover {
            background-color: #334155 !important;
            text-decoration: none !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        }
        
        /* 削除ボタン */
        .delete-btn button {
            background-color: #fee2e2 !important; color: #991b1b !important; border: 1px solid #fecaca !important;
            padding: 0.3rem 0.5rem !important; font-size: 0.8rem !important; margin-top: 5px; width: auto !important;
        }

        /* ヒーローエリア */
        .hero-container {
            background: white; border-radius: 16px; padding: 3rem; margin-bottom: 2rem;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

def apply_editor_style():
    """エディタ用の黒ベースデザイン"""
    st.markdown("""
        <style>
        /* 強制ダークモード */
        .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
        .stTextInput input, .stTextArea textarea, .stSelectbox select {
            background-color: #262730 !important; color: #ffffff !important; border: 1px solid #41444e !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] { background-color: #262730 !important; border: 1px solid #41444e !important; }
        
        /* --- UI非表示設定 (エディタ画面でも同様) --- */
        header[data-testid="stHeader"], .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], #MainMenu, div[class*="viewerBadge"] { 
            display: none !important; 
        }
        
        /* フッター隠し */
        footer { 
            visibility: hidden !important; 
            height: 0px !important;
            position: fixed !important;
            left: -9999px !important;
        }
        
        .block-container { padding-top: 2rem; padding-bottom: 5rem; }
        </style>
    """, unsafe_allow_html=True)

# HTMLパーツ
HERO_HTML = """
<div class="hero-container">
    <h1 style="font-size:2.5rem; font-weight:900; color:#1e293b; margin-bottom:10px;">診断クイズメーカー</h1>
    <p style="color:#64748b;">AIがたった1分で構成案を作成。集客・販促に使える高品質な診断ツールを今すぐ公開。</p>
</div>
"""

# カードの中身
def get_card_content_html(title, desc, img_url, views=0, likes=0):
    return f"""
    <div class="card-img-box">
        <span class="badge-new">NEW</span>
        <span class="badge-stats">👁️ {views} &nbsp; ❤️ {likes}</span>
        <img src="{img_url}" class="card-img" loading="lazy">
    </div>
    <div class="quiz-content">
        <div class="quiz-title">{title}</div>
        <div class="quiz-desc">{desc}</div>
    </div>
    """

# カスタムボタンHTML
def get_custom_button_html(url, text, color="blue", target="_top"):
    color_map = {
        "blue": "background-color: #2563eb; color: white;",
        "green": "background-color: #16a34a; color: white;",
        "red": "background-color: #dc2626; color: white;",
        "black": "background-color: #1e293b; color: white;"
    }
    style = color_map.get(color, color_map["blue"])
    
    return f"""
    <a href="{url}" target="{target}" style="
        display: block;
        width: 100%;
        padding: 0.75rem;
        text-align: center;
        text-decoration: none;
        border-radius: 8px;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: opacity 0.2s;
        {style}
    " onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">
        {text}
    </a>
    """
