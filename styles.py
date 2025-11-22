import streamlit as st

def apply_portal_style():
    """公開画面用の白ベースデザイン"""
    st.markdown("""
        <style>
        /* 全体設定 */
        .stApp { background-color: #ffffff !important; color: #333333 !important; }
        .block-container { max-width: 1100px; padding-top: 1rem; padding-bottom: 5rem; }
        #MainMenu, footer, header {visibility: hidden;}
        .stDeployButton {display:none;}
        
        /* --- クリック可能なカードデザイン --- */
        
        /* リンクのアンダーラインなどを消す */
        a.quiz-card-link {
            text-decoration: none !important;
            color: inherit !important;
            display: block;
            height: 100%;
        }
        
        /* カード本体 */
        .quiz-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
            /* 高さ固定 */
            height: 340px; 
            display: flex;
            flex-direction: column;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            transition: all 0.2s ease-in-out;
            margin-bottom: 15px;
        }
        
        /* ホバー時の動き (カード全体が浮き上がる) */
        .quiz-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 20px -3px rgba(0,0,0,0.15);
            border-color: #3b82f6;
        }
        
        /* サムネイル画像エリア */
        .quiz-thumb-box {
            width: 100%;
            height: 180px; /* 画像を大きく */
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
        
        /* ホバー時に画像が少しズームする演出 */
        .quiz-card:hover .quiz-thumb {
            transform: scale(1.08);
        }
        
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
            font-weight: 700;
            font-size: 1.1rem;
            margin-bottom: 8px;
            color: #1e293b;
            line-height: 1.4;
            /* 2行で省略 */
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            height: 3em;
        }
        /* ホバー時にタイトルが青くなる */
        .quiz-card:hover .quiz-title {
            color: #2563eb;
        }
        
        /* 説明文 */
        .quiz-desc {
            font-size: 0.85rem;
            color: #64748b;
            line-height: 1.5;
            /* 2行で省略 */
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        /* NEWバッジ */
        .badge-new {
            position: absolute;
            top: 10px;
            left: 10px;
            background-color: rgba(255, 255, 255, 0.9);
            color: #2563eb;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 800;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            z-index: 10;
        }

        /* --- 作成ボタン (メイン) --- */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
            color: white; border: none; font-size: 1.1rem; padding: 0.8rem;
            box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
        }
        .stButton button[kind="primary"]:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #4338ca 100%);
            box-shadow: 0 8px 12px rgba(37, 99, 235, 0.3);
            transform: scale(1.01);
        }
        
        /* 削除ボタン */
        .delete-wrapper { text-align: right; margin-top: 5px; }
        .delete-btn button {
            background-color: #fee2e2 !important; color: #991b1b !important; border: 1px solid #fecaca !important;
            padding: 0.2rem 0.6rem !important; font-size: 0.8rem !important; height: auto !important; width: auto !important;
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

# HTMLパーツ
HERO_HTML = """
<div class="hero-container">
    <h1 style="font-size:2.5rem; font-weight:900; color:#1e293b; margin-bottom:10px;">診断クイズメーカー</h1>
    <p style="color:#64748b;">AIがたった1分で構成案を作成。集客・販促に使える高品質な診断ツールを今すぐ公開。</p>
</div>
"""

def get_clickable_card_html(link, title, desc, img_url):
    """カード全体がリンクになったHTMLを返す"""
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
