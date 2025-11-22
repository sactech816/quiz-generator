import streamlit as st

# ==========================================
# CSS (デザイン定義)
# ==========================================
def apply_portal_style():
    """公開画面用の白ベースデザイン"""
    st.markdown("""
        <style>
        /* 全体設定 */
        .stApp { background-color: #f8fafc !important; color: #333333 !important; }
        .block-container { max-width: 1100px; padding-top: 1rem; padding-bottom: 5rem; }
        
        /* --- 邪魔な表示を消す --- */
        #MainMenu {visibility: hidden;} 
        footer {visibility: hidden;} 
        header {visibility: hidden;} 
        .stDeployButton {display:none;}
        [data-testid="stElementToolbar"] {display: none;}
        
        /* --- カードデザイン (高さ固定で整列) --- */
        .quiz-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
            /* ★ここで高さを固定します★ */
            height: 360px; 
            display: flex;
            flex-direction: column;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            transition: transform 0.2s;
            margin-bottom: 10px;
        }
        .quiz-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
            border-color: #cbd5e1;
        }
        
        /* サムネイル画像 */
        .quiz-thumb-box {
            width: 100%;
            height: 160px; /* 画像の高さ固定 */
            background-color: #f1f5f9;
            overflow: hidden;
        }
        .quiz-thumb {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s;
        }
        .quiz-card:hover .quiz-thumb {
            transform: scale(1.05);
        }
        
        /* カードの中身 */
        .quiz-content {
            padding: 16px;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }
        
        /* タイトル (2行までで省略) */
        .quiz-title {
            font-weight: bold;
            font-size: 1.1rem;
            margin-bottom: 8px;
            color: #1e293b;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            height: 3em; /* 高さ確保 */
        }
        
        /* 説明文 (3行までで省略) */
        .quiz-desc {
            font-size: 0.85rem;
            color: #64748b;
            line-height: 1.5;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        /* バッジ */
        .badge-new {
            background-color: #dbeafe; color: #1e40af;
            font-size: 0.65rem; padding: 2px 6px; border-radius: 4px;
            font-weight: bold; display: inline-block; margin-bottom: 6px; width: fit-content;
        }
        
        /* --- ボタンデザイン --- */
        
        /* 黒い「今すぐ診断する」ボタン (画像に合わせました) */
        .play-btn-link {
            display: block;
            background-color: #1e293b; /* 濃いネイビー/黒 */
            color: white !important;
            text-align: center;
            padding: 12px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            margin-top: 0px;
            transition: background 0.2s;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .play-btn-link:hover {
            background-color: #334155;
            color: white !important;
        }

        /* 通常のボタン */
        .stButton button {
            background-color: #f8fafc; border: 1px solid #cbd5e1; color: #334155;
            border-radius: 8px; font-weight: bold; padding: 0.6rem 1rem; transition: all 0.2s; width: 100%;
        }
        .stButton button:hover { border-color: #3b82f6; color: #2563eb; background-color: #eff6ff; }
        
        /* 作成ボタン (強調) */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
            color: white; border: none; font-size: 1.1rem; padding: 0.8rem;
        }
        .stButton button[kind="primary"]:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #4338ca 100%);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }
        
        /* ヒーローエリア */
        .hero-container {
            background: white; border-radius: 16px; padding: 3rem; margin-bottom: 2rem;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;
            position: relative; overflow: hidden; text-align: center;
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
    <h1 style="font-size: 2.5rem; font-weight: 900; color: #1e293b; margin-bottom: 10px;">
        診断クイズメーカー
    </h1>
    <p style="color: #64748b;">AIがたった1分で構成案を作成。集客・販促に使える高品質な診断ツールを今すぐ公開。</p>
</div>
"""

def get_card_html(title, desc, img_url):
    return f"""
    <div class="quiz-card">
        <div class="quiz-thumb-box">
            <img src="{img_url}" class="quiz-thumb" loading="lazy">
        </div>
        <div class="quiz-content">
            <span class="badge-new">NEW</span>
            <div class="quiz-title">{title}</div>
            <div class="quiz-desc">{desc}</div>
        </div>
    </div>
    """
