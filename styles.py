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
        
        /* --- カスタムボタンの共通スタイル (HTML) --- */
        .custom-btn {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: bold;
            text-decoration: none !important;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            cursor: pointer;
            margin-bottom: 10px;
            border: none;
            line-height: 1.5;
        }
        .custom-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            opacity: 0.9;
        }
        .custom-btn:active {
            transform: translateY(0);
        }

        /* 色ごとのクラス */
        .btn-green { background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); color: white !important; }
        .btn-blue { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white !important; }
        .btn-red { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white !important; }
        .btn-orange { background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); color: white !important; }
        .btn-gray { background: #f1f5f9; color: #475569 !important; border: 1px solid #cbd5e1; }

        /* --- 以下、既存のカードデザイン等 --- */
        a.quiz-card-link { text-decoration: none !important; color: inherit !important; display: block !important; }
        .quiz-card {
            background: white; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;
            height: 380px; display: flex; flex-direction: column;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02); transition: 0.2s; margin-bottom: 10px;
            position: relative;
        }
        .quiz-card:hover { transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-color: #3b82f6; }
        .quiz-thumb-box { width: 100%; height: 160px; background-color: #f1f5f9; overflow: hidden; position: relative; }
        .quiz-thumb { width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s ease; }
        .quiz-card:hover .quiz-thumb { transform: scale(1.05); }
        .quiz-content { padding: 16px; flex-grow: 1; display:flex; flex-direction:column; }
        .quiz-title { font-weight: bold; font-size: 1.1rem; margin-bottom: 8px; color: #1e293b; line-height: 1.4; height: 3em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
        .quiz-desc { font-size: 0.85rem; color: #64748b; margin-bottom: 10px; line-height: 1.5; height: 4.5em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; }
        .badge-new { position: absolute; top: 10px; left: 10px; background: rgba(255,255,255,0.9); color: #1e40af; font-size: 0.65rem; padding: 2px 6px; border-radius: 4px; font-weight: bold; z-index: 2; }
        .badge-stats { position: absolute; bottom: 5px; right: 5px; background: rgba(0,0,0,0.6); color: white; font-size: 0.7rem; padding: 2px 8px; border-radius: 12px; font-weight: bold; z-index: 2; }
        
        /* Streamlit純正ボタンの補正 (ホバーで白くなるのを防ぐ) */
        .stButton button { border-radius: 8px; font-weight: bold; transition: 0.2s; }
        .stButton button:hover { border-color: #3b82f6; color: #2563eb; background-color: #eff6ff; }
        /* セカンダリ(いいね)ボタン用 */
        .stButton button[kind="secondary"] {
            background-color: #fff1f2 !important; color: #e11d48 !important; border: 1px solid #fecdd3 !important;
        }
        .stButton button[kind="secondary"]:hover {
            background-color: #ffe4e6 !important; color: #be123c !important; border-color: #fda4af !important;
        }
        /* プライマリ(作成)ボタン用 */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%) !important; color: white !important; border: none !important;
        }
        .stButton button[kind="primary"]:hover {
             color: white !important; opacity: 0.9;
        }
        
        /* 削除ボタン */
        .delete-btn button { background-color: #fee2e2 !important; color: #991b1b !important; border: 1px solid #fecaca !important; font-size: 0.8rem; padding: 0.2rem 0.5rem; }
        
        .hero-container { background: white; border-radius: 16px; padding: 3rem; margin-bottom: 2rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; text-align: center; }
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

def get_card_content_html(title, desc, img_url, views=0, likes=0):
    return f"""
    <div class="card-img-box">
        <span class="badge-new">NEW</span>
        <span class="badge-stats">👁️ {views} &nbsp; ❤️ {likes}</span>
        <img src="{img_url}" class="card-img" loading="lazy">
    </div>
    <div class="card-text-box">
        <div class="card-title">{title}</div>
        <div class="card-desc">{desc}</div>
    </div>
    """

# ★新機能: 色付きボタンのHTMLを生成する関数★
def get_custom_button_html(url, text, color="blue", target="_top"):
    return f"""
    <a href="{url}" target="{target}" class="custom-btn btn-{color}">
        {text}
    </a>
    """
