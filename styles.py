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
        
        /* 不要な要素を隠す */
        #MainMenu, footer, header {visibility: hidden;}
        .stDeployButton {display:none;}
        [data-testid="stElementToolbar"] {display: none;}
        
        /* --- カードコンテナのデザイン (st.container) --- */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            transition: transform 0.2s;
            overflow: hidden;
            padding: 0 !important; /* 内側の余白をリセット */
            margin-bottom: 1rem;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: #3b82f6;
            transform: translateY(-3px);
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        }
        
        /* --- カード内部のHTML要素 --- */
        .card-img-box {
            width: calc(100% + 2rem); /* Streamlitのpaddingを相殺 */
            margin: -1rem -1rem 0 -1rem; /* 上左右の余白を消す */
            height: 160px;
            background-color: #f1f5f9;
            overflow: hidden;
            position: relative;
        }
        .card-img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:hover .card-img {
            transform: scale(1.05);
        }
        
        .card-text-box {
            padding: 10px 5px 5px 5px;
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
            height: 4.5em;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            margin-bottom: 10px;
        }
        .badge-new {
            position: absolute; top: 10px; left: 10px;
            background: rgba(255,255,255,0.9); color: #1e40af;
            font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; font-weight: bold; z-index: 2;
        }
        
        /* --- リンクボタン (黒くする) --- */
        a[data-testid="stLinkButton"] {
            background-color: #1e293b !important; /* 黒/濃紺 */
            color: #ffffff !important;
            border: none !important;
            font-weight: bold !important;
            text-align: center !important;
            border-radius: 8px !important;
            transition: all 0.2s !important;
            margin-top: 5px !important;
        }
        a[data-testid="stLinkButton"]:hover {
            background-color: #334155 !important; /* ホバー時は少し明るく */
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
            text-decoration: none !important;
        }

        /* 作成ボタン (青) */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
            color: white; border: none; font-size: 1.1rem; padding: 0.8rem;
            box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
        }
        .stButton button[kind="primary"]:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #4338ca 100%);
            transform: scale(1.01);
        }
        
        /* 削除ボタン (赤) */
        .stButton button[kind="secondary"] {
            background-color: #fee2e2; color: #991b1b; border: 1px solid #fecaca;
            font-size: 0.8rem; padding: 0.2rem 0.5rem;
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

# ==========================================
# HTMLパーツ
# ==========================================
HERO_HTML = """
<div class="hero-container">
    <h1 style="font-size:2.5rem; font-weight:900; color:#1e293b; margin-bottom:10px;">診断クイズメーカー</h1>
    <p style="color:#64748b;">AIがたった1分で構成案を作成。集客・販促に使える高品質な診断ツールを今すぐ公開。</p>
</div>
"""

# ★ここを修正しました（関数名変更＆中身調整）★
def get_card_content_html(title, desc, img_url):
    return f"""
    <div class="card-img-box">
        <span class="badge-new">NEW</span>
        <img src="{img_url}" class="card-img" loading="lazy">
    </div>
    <div class="card-text-box">
        <div class="card-title">{title}</div>
        <div class="card-desc">{desc}</div>
    </div>
    """
# ★カードの中身（統計情報付き）
def get_card_content_html(title, desc, img_url, views=0, likes=0):
    return f"""
    <div class="card-img-box">
        <span class="badge-new">NEW</span>
        <div style="position:absolute; bottom:5px; right:5px; background:rgba(0,0,0,0.6); color:white; padding:2px 8px; border-radius:12px; font-size:0.7rem; font-weight:bold;">
            👁️ {views} &nbsp; ❤️ {likes}
        </div>
        <img src="{img_url}" class="card-img" loading="lazy">
    </div>
    <div class="card-text-box">
        <div class="card-title">{title}</div>
        <div class="card-desc">{desc}</div>
    </div>
    """
