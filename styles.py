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
        #MainMenu, footer, header {visibility: hidden;}
        .stDeployButton {display:none;}
        
        /* --- リンクカードのスタイル --- */
        a.quiz-card-link {
            text-decoration: none !important;
            color: inherit !important;
            display: block !important;
        }
        a.quiz-card-link:hover {
            text-decoration: none !important;
        }

        /* カード本体 */
        .quiz-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
            height: 360px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            transition: transform 0.2s, box-shadow 0.2s;
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
            height: 160px;
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
        .quiz-card:hover .quiz-thumb { transform: scale(1.05); }
        
        /* コンテンツエリア */
        .quiz-content { padding: 16px; flex-grow: 1; display:flex; flex-direction:column; }
        .quiz-title { 
            font-weight: bold; font-size: 1.1rem; margin-bottom: 8px; color: #1e293b; 
            line-height: 1.4; height: 3em; overflow: hidden;
            display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
        }
        .quiz-card:hover .quiz-title { color: #2563eb; }
        
        .quiz-desc { 
            font-size: 0.85rem; color: #64748b; margin-bottom: 10px; line-height: 1.5;
            height: 4.5em; overflow: hidden;
            display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;
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
        
        /* ボタン */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
            color: white; border: none;
        }
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

# ★ここを修正: リンク、閲覧数、いいね数を受け取る関数に統一
def get_clickable_card_html(link, title, desc, img_url, views=0, likes=0):
    return f"""
    <a href="{link}" target="_top" class="quiz-card-link">
        <div class="quiz-card">
            <div class="quiz-thumb-box">
                <span class="badge-new">NEW</span>
                <span class="badge-stats">👁️ {views} &nbsp; ❤️ {likes}</span>
                <img src="{img_url}" class="quiz-thumb" loading="lazy">
            </div>
            <div class="quiz-content">
                <div class="quiz-title">{title}</div>
                <div class="quiz-desc">{desc}</div>
            </div>
        </div>
    </a>
    """
