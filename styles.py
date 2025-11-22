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
        
        /* --- 【重要】余計なUIを徹底的に隠す --- */
        #MainMenu {visibility: hidden !important;} 
        footer {visibility: hidden !important;} 
        header {visibility: hidden !important;} 
        
        /* 右下のManageアプリボタンやデプロイボタンを消す */
        .stDeployButton {display:none !important;}
        [data-testid="stToolbar"] {display: none !important;}
        [data-testid="stDecoration"] {display: none !important;}
        [data-testid="stStatusWidget"] {display: none !important;}
        
        /* --- カードデザイン --- */
        .quiz-card-link {
            text-decoration: none !important;
            color: inherit !important;
            display: block !important;
        }
        
        .quiz-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
            height: 380px; /* 高さを固定 */
            display: flex;
            flex-direction: column;
            box-shadow: 0 4px 6px rgba(0,0,0,0.02);
            transition: all 0.3s ease;
            margin-bottom: 20px;
            position: relative;
        }
        
        /* ホバー時の動き */
        .quiz-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.1);
            border-color: #3b82f6;
        }
        
        /* 画像エリア */
        .quiz-thumb-box {
            width: 100%;
            height: 180px;
            background-color: #f1f5f9;
            overflow: hidden;
            position: relative;
        }
        .quiz-thumb {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.5s ease;
        }
        .quiz-card:hover .quiz-thumb {
            transform: scale(1.05);
        }
        
        /* コンテンツ */
        .quiz-content {
            padding: 20px;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }
        
        .quiz-title {
            font-weight: 700;
            font-size: 1.1rem;
            margin-bottom: 8px;
            color: #1e293b;
            line-height: 1.4;
            height: 3em;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }
        
        .quiz-card:hover .quiz-title {
            color: #2563eb; /* ホバーで青くする */
        }
        
        .quiz-desc {
            font-size: 0.85rem;
            color: #64748b;
            line-height: 1.6;
            height: 4.5em;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
        }
        
        /* NEWバッジ */
        .badge-new {
            position: absolute;
            top: 12px;
            left: 12px;
            background-color: rgba(255, 255, 255, 0.95);
            color: #2563eb;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 800;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            z-index: 10;
        }
        
        /* 削除ボタン */
        .delete-btn button {
            background-color: #fee2e2 !important;
            color: #991b1b !important;
            border: 1px solid #fecaca !important;
            font-size: 0.8rem !important;
            margin-top: 5px;
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

def get_clickable_card_html(link, title, desc, img_url):
    """
    カード全体をリンク(aタグ)にするHTML。
    target="_top" を指定することで、Streamlitのiframeを抜けて同じタブで遷移します。
    """
    return f"""
    <a href="{link}" target="_top" class="quiz-card-link">
        <div class="quiz-card">
            <div class="quiz-thumb-box">
                <span class="badge-new">NEW</span>
                <img src="{img_url}" class="quiz-thumb" loading="lazy">
            </div>
            <div class="quiz-content">
                <div class="quiz-title">{title}</div>
                <div class="quiz-desc">{desc}</div>
            </div>
        </div>
    </a>
    """
