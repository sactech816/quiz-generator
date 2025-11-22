import streamlit as st

# ==========================================
# CSS (デザイン定義)
# ==========================================
def apply_portal_style():
    """公開画面用の白ベースデザイン"""
    st.markdown("""
        <style>
        /* 全体設定 */
        .stApp { background-color: #ffffff !important; color: #333333 !important; }
        .block-container { max-width: 1100px; padding-top: 1rem; padding-bottom: 5rem; }
        
        /* UI隠し */
        #MainMenu, footer, header {visibility: hidden;}
        .stDeployButton {display:none;}
        [data-testid="stElementToolbar"] {display: none;}
        
        /* --- コンテナ（カード枠）の調整 --- */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            transition: transform 0.2s;
            padding: 0 !important;
            overflow: hidden;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: #3b82f6;
            transform: translateY(-3px);
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        }
        
        /* --- カード内部のビジュアル (HTML) --- */
        .card-visual-box {
            display: flex;
            flex-direction: column;
            height: 300px; /* 画像+テキストエリアの高さ固定 */
        }
        
        .card-img-box {
            width: calc(100% + 2rem); /* Streamlitのpadding相殺 */
            margin: -1rem -1rem 0 -1rem; 
            height: 160px;
            background-color: #f1f5f9;
            overflow: hidden;
            position: relative;
        }
        
        .card-img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .card-content {
            padding: 10px 5px;
            flex-grow: 1;
        }
        
        .card-title {
            font-weight: 700;
            font-size: 1.1rem;
            margin-bottom: 5px;
            color: #1e293b;
            line-height: 1.4;
            height: 3em;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }
        
        .card-desc {
            font-size: 0.85rem;
            color: #64748b;
            line-height: 1.5;
            height: 4.5em; /* 3行分 */
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
        }
        
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

        /* --- 純正ボタンのデザイン --- */
        .stButton button {
            width: 100%; border-radius: 8px; font-weight: bold; border: none;
        }
        
        /* 黒い「今すぐ診断」ボタン */
        a[data-testid="stLinkButton"] {
            background-color: #1e293b !important;
            color: #ffffff !important;
            text-align: center !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            margin-top: 5px !important;
        }
        a[data-testid="stLinkButton"]:hover {
            background-color: #334155 !important;
            text-decoration: none !important;
        }
        
        /* 作成ボタン (青) */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
            color: white;
        }
        
        /* 削除ボタン (赤) */
        .delete-btn button {
            background-color: #fee2e2 !important; color: #991b1b !important;
            border: 1px solid #fecaca !important; font-size: 0.8rem !important;
            padding: 0.2rem !important; margin-top: 5px;
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
        #MainMenu, footer, header {visibility: hidden;}
        .stDeployButton {display:none;}
        .block-container { padding-top: 2rem; padding-bottom: 5rem; }
        .stTextInput input, .stTextArea textarea { font-family: "Inter", sans-serif; }
        </style>
    """, unsafe_allow_html=True)

# HTMLパーツ
HERO_HTML = """
<div class="hero-container">
    <h1 style="font-size:2.5rem; font-weight:900; color:#1e293b; margin-bottom:10px;">診断クイズメーカー</h1>
    <p style="color:#64748b;">AIがたった1分で構成案を作成。集客・販促に使える高品質な診断ツールを今すぐ公開。</p>
</div>
"""

# ★ここを変更: リンク機能を持たない純粋な表示用HTML
def get_card_visual_html(title, desc, img_url, views=0, likes=0):
    return f"""
    <div class="card-visual-box">
        <div class="card-img-box">
            <span class="badge-new">NEW</span>
            <span class="badge-stats">👁️ {views} &nbsp; ❤️ {likes}</span>
            <img src="{img_url}" class="card-img" loading="lazy">
        </div>
        <div class="card-content">
            <div class="card-title">{title}</div>
            <div class="card-desc">{desc}</div>
        </div>
    </div>
    """
